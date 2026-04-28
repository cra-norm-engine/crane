from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, ComplianceActionStatus, ComplianceActionType, EntityType, ReleaseStatus
from app.models.product import ProductRelease
from app.repositories.change_repository import ChangeRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate


class ProductReleaseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProductReleaseRepository(db)
        self.product_repository = ProductRepository(db)
        # Used to look up and close the re_release_product compliance action
        # when a new release is linked to a substantial change
        self.change_repository = ChangeRepository(db)

    def list_releases(self, *, product_id: UUID | None = None) -> list[ProductReleaseRead]:
        releases = self.repository.list_all(product_id=product_id)
        return [ProductReleaseRead.model_validate(release) for release in releases]

    def get_release(self, release_id: UUID) -> ProductReleaseRead:
        release = self.repository.get_or_404(release_id)
        return ProductReleaseRead.model_validate(release)

    def create_release(self, payload: ProductReleaseCreate, actor: object) -> ProductReleaseRead:
        self.product_repository.get_or_404(payload.product_id)

        if self.repository.get_by_product_and_version(product_id=payload.product_id, version=payload.version):
            raise ConflictException("Release version already exists for this product")

        release = ProductRelease(**payload.model_dump())

        try:
            self.repository.add(release)
            # Flush to get the generated release ID before creating audit events
            self.db.flush()

            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="release.created",
                entity_type=EntityType.product_release,
                entity_id=release.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "version": release.version,
                    "release_version": release.version,
                    "release_status": release.release_status.value,
                    # Record the causal change ID in the audit trail for traceability
                    "caused_by_change_id": str(payload.caused_by_change_id) if payload.caused_by_change_id else None,
                },
            )

            # If this release is linked to a substantial change, automatically
            # mark the re_release_product compliance action as completed.
            # This closes the CRA Art. 13(8) loop without requiring a separate manual step.
            if payload.caused_by_change_id:
                self._auto_complete_re_release_action(
                    change_id=payload.caused_by_change_id,
                    actor=actor,
                )

            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create release due to uniqueness conflict") from exc

        return ProductReleaseRead.model_validate(release)

    def update_release(self, release_id: UUID, payload: ProductReleaseUpdate, actor: object) -> ProductReleaseRead:
        release = self.repository.get_or_404(release_id)
        updates = payload.model_dump(exclude_unset=True)
        previous_release_status = release.release_status

        if "version" in updates and updates["version"] != release.version:
            existing = self.repository.get_by_product_and_version(
                product_id=release.product_id,
                version=updates["version"],
            )
            if existing and existing.id != release.id:
                raise ConflictException("Release version already exists for this product")

        for field_name, value in updates.items():
            setattr(release, field_name, value)

        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type=(
                    "release.published"
                    if release.release_status == ReleaseStatus.released
                    and previous_release_status != ReleaseStatus.released
                    else "release.updated"
                ),
                entity_type=EntityType.product_release,
                entity_id=release.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "product_release_id": str(release.id),
                    "version": release.version,
                    "release_version": release.version,
                    "release_status": release.release_status.value,
                    "previous_release_status": previous_release_status.value,
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(release)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update release due to uniqueness conflict") from exc

        return ProductReleaseRead.model_validate(release)

    def _auto_complete_re_release_action(self, change_id: UUID, actor: object) -> None:
        """
        Find the pending re_release_product compliance action on the given substantial
        change and mark it completed.  Called automatically when a release is created
        with caused_by_change_id set.

        If the action has already been completed (e.g. marked manually) this is a no-op.
        If the change has no assessment or no re_release_product action, nothing happens.
        """
        assessment = self.change_repository.get_assessment(change_id)
        if assessment is None:
            # Change has not been assessed yet — nothing to auto-complete
            return

        # Find the re_release_product action that is still pending or in_progress
        for action in assessment.compliance_actions:
            if (
                action.action_type == ComplianceActionType.re_release_product
                and action.action_status != ComplianceActionStatus.completed
            ):
                action.action_status = ComplianceActionStatus.completed
                action.completed_by_user_id = getattr(actor, "id", None)

                create_audit_event(
                    self.db,
                    actor_user_id=getattr(actor, "id", None),
                    action_type="update",
                    entity_type=EntityType.change_compliance_action,
                    entity_id=action.id,
                    status=AuditStatus.success,
                    details_json={
                        "action_type": ComplianceActionType.re_release_product.value,
                        "action_status": ComplianceActionStatus.completed.value,
                        "auto_completed_by": "release_creation",
                        "change_id": str(change_id),
                    },
                )
                # Only one re_release_product action exists per assessment
                break

    def delete_release(self, release_id: UUID, actor: object) -> None:
        release = self.repository.get_or_404(release_id)
        self.repository.delete(release)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="release.deleted",
            entity_type=EntityType.product_release,
            entity_id=release.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(release.product_id),
                "version": release.version,
                "release_version": release.version,
            },
        )
        self.db.commit()
