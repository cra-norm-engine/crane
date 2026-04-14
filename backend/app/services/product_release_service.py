from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType, ReleaseStatus
from app.models.product import ProductRelease
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate


class ProductReleaseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProductReleaseRepository(db)
        self.product_repository = ProductRepository(db)

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
                },
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
