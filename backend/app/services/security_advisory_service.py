# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.advisory_release import AdvisoryRelease
from app.models.enums import AuditStatus, EntityType
from app.models.security_advisory import SecurityAdvisory
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.security_advisory_repository import SecurityAdvisoryRepository
from app.schemas.security_advisory import (
    AdvisoryReleaseRef,
    SecurityAdvisoryCreate,
    SecurityAdvisoryRead,
    SecurityAdvisoryUpdate,
)


class SecurityAdvisoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SecurityAdvisoryRepository(db)
        self.release_repository = ProductReleaseRepository(db)
        self.product_repository = ProductRepository(db)

    # ── Read mapping ──────────────────────────────────────────────────────────

    @staticmethod
    def _release_ref(release: object) -> AdvisoryReleaseRef:
        """Build a release ref, computing display_version like the release schema."""
        user_version = getattr(release, "user_version", None)
        system_version = getattr(release, "system_version", None)
        version_label = f"v{system_version}"
        display_version = f"{user_version} ({version_label})" if user_version else version_label
        return AdvisoryReleaseRef(
            id=release.id,
            display_version=display_version,
            release_status=str(getattr(release, "release_status", "")),
        )

    def _to_read(self, advisory: SecurityAdvisory) -> SecurityAdvisoryRead:
        """Build the Read payload, resolving product name + affected releases."""
        releases = [
            self._release_ref(link.product_release)
            for link in advisory.release_links
            if link.product_release is not None
        ]
        # Newest release first for a stable, readable order.
        releases.sort(key=lambda r: r.display_version, reverse=True)
        data = SecurityAdvisoryRead.model_validate(advisory)
        data.product_name = advisory.product.name if advisory.product else None
        data.releases = releases
        return data

    # ── Release-set resolution ────────────────────────────────────────────────

    def _resolve_release_ids(
        self, product_id: UUID, release_ids: list[UUID], all_releases: bool
    ) -> list[UUID]:
        """
        Resolve the affected-release set for a product.

        all_releases → snapshot every current release of the product. Otherwise
        validate that each given release belongs to the product.
        """
        product_releases = self.release_repository.list_all(product_id=product_id)
        valid_ids = {r.id for r in product_releases}
        if all_releases:
            return list(valid_ids)
        resolved: list[UUID] = []
        for rid in release_ids:
            if rid not in valid_ids:
                raise ConflictException(
                    f"Release {rid} does not belong to product {product_id}"
                )
            resolved.append(rid)
        return resolved

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def list_security_advisories(
        self, *, product_id: UUID | None = None, release_id: UUID | None = None
    ) -> list[SecurityAdvisoryRead]:
        advisories = self.repository.list_all(product_id=product_id, release_id=release_id)
        return [self._to_read(a) for a in advisories]

    def get_security_advisory(self, advisory_id: UUID) -> SecurityAdvisoryRead:
        return self._to_read(self.repository.get_or_404(advisory_id))

    def create_security_advisory(
        self, payload: SecurityAdvisoryCreate, actor: object
    ) -> SecurityAdvisoryRead:
        # Validate the product exists.
        self.product_repository.get_or_404(payload.product_id)

        if self.repository.get_by_advisory_id(payload.advisory_id) is not None:
            raise ConflictException(f"Advisory ID '{payload.advisory_id}' already exists")

        release_ids = self._resolve_release_ids(
            payload.product_id, payload.release_ids, payload.all_releases
        )

        advisory = SecurityAdvisory(
            **payload.model_dump(exclude={"release_ids", "all_releases"})
        )
        advisory.release_links = [
            AdvisoryRelease(product_release_id=rid) for rid in release_ids
        ]
        try:
            self.repository.add(advisory)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_advisory.created",
                entity_type=EntityType.security_advisory,
                entity_id=advisory.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(advisory.product_id),
                    "advisory_id": advisory.advisory_id,
                    "status": advisory.status,
                    "release_ids": [str(rid) for rid in release_ids],
                },
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create security advisory") from exc
        return self._to_read(self.repository.get_or_404(advisory.id))

    def update_security_advisory(
        self, advisory_id: UUID, payload: SecurityAdvisoryUpdate, actor: object
    ) -> SecurityAdvisoryRead:
        advisory = self.repository.get_or_404(advisory_id)
        updates = payload.model_dump(exclude_unset=True)
        new_release_ids = updates.pop("release_ids", None)

        for field, value in updates.items():
            setattr(advisory, field, value)

        # Reconcile the affected-release set if the caller provided one.
        if new_release_ids is not None:
            self._sync_release_links(advisory, new_release_ids)

        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_advisory.updated",
                entity_type=EntityType.security_advisory,
                entity_id=advisory.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(advisory.product_id),
                    "advisory_id": advisory.advisory_id,
                    "updated_fields": sorted(updates.keys())
                    + (["release_ids"] if new_release_ids is not None else []),
                },
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update security advisory") from exc
        return self._to_read(self.repository.get_or_404(advisory.id))

    def _sync_release_links(
        self, advisory: SecurityAdvisory, release_ids: list[UUID]
    ) -> None:
        """Attach/detach join rows so the advisory's release set matches release_ids."""
        target = set(
            self._resolve_release_ids(advisory.product_id, release_ids, all_releases=False)
        )
        current = {link.product_release_id: link for link in advisory.release_links}
        # Detach removed.
        for rid, link in current.items():
            if rid not in target:
                advisory.release_links.remove(link)
        # Attach added.
        for rid in target:
            if rid not in current:
                advisory.release_links.append(AdvisoryRelease(product_release_id=rid))

    def delete_security_advisory(self, advisory_id: UUID, actor: object) -> None:
        advisory = self.repository.get_or_404(advisory_id)
        product_id = advisory.product_id
        code = advisory.advisory_id
        self.repository.delete(advisory)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="security_advisory.deleted",
            entity_type=EntityType.security_advisory,
            entity_id=advisory_id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(product_id),
                "advisory_id": code,
            },
        )
        self.db.commit()
