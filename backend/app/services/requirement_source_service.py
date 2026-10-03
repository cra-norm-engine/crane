from __future__ import annotations

from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.annex_requirement import ReleaseRequirementBaseline, RequirementSource, RequirementSourceProduct
from app.models.product import Product, ProductRelease
from app.models.requirement_assessment import ReleaseRequirementAssessment
from app.models.enums import RequirementAssessmentStatus
from app.schemas.requirement_source import RequirementSourceCreate, RequirementSourceUpdate


class RequirementSourceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self):
        return select(RequirementSource).options(
            selectinload(RequirementSource.product_links),
            selectinload(RequirementSource.requirements),
        )

    def list(self) -> list[RequirementSource]:
        return list(self.db.scalars(self._query().order_by(RequirementSource.is_system_managed.desc(), RequirementSource.title)).unique())

    def get(self, source_id: UUID) -> RequirementSource:
        source = self.db.scalar(self._query().where(RequirementSource.id == source_id))
        if source is None:
            raise NotFoundException("Requirement source not found")
        return source

    def create(self, payload: RequirementSourceCreate) -> RequirementSource:
        identifier = payload.identifier.strip().upper()
        if self.db.scalar(select(RequirementSource.id).where(RequirementSource.identifier == identifier)):
            raise ConflictException("A requirement source with this identifier already exists.")
        self._validate_products(payload.product_ids)
        source = RequirementSource(
            identifier=identifier, title=payload.title.strip(), source_type=payload.source_type,
            edition=payload.edition, publisher=payload.publisher, reference_url=payload.reference_url,
            license_note=payload.license_note, organization_wide=payload.organization_wide,
        )
        self.db.add(source)
        self.db.flush()
        self._replace_products(source, [] if payload.organization_wide else payload.product_ids)
        self.db.commit()
        return self.get(source.id)

    def update(self, source_id: UUID, payload: RequirementSourceUpdate) -> RequirementSource:
        source = self.get(source_id)
        if source.is_system_managed:
            raise ConflictException("System-managed requirement sources cannot be edited.")
        changes = payload.model_dump(exclude_unset=True, exclude={"product_ids"})
        if source.status == "published" and (payload.product_ids is not None or any(key not in {"license_note", "reference_url"} for key in changes)):
            raise ConflictException("Published source identity is frozen. Retire it and create a new edition.")
        for key, value in changes.items():
            setattr(source, key, value)
        product_ids = payload.product_ids
        if product_ids is not None:
            self._validate_products(product_ids)
            self._replace_products(source, [] if source.organization_wide else product_ids)
        if not source.organization_wide and not source.product_links:
            raise ValidationException("Select organization-wide scope or at least one product.")
        self.db.commit()
        return self.get(source.id)

    def set_status(self, source_id: UUID, status: str) -> RequirementSource:
        source = self.get(source_id)
        if source.is_system_managed:
            raise ConflictException("System-managed requirement sources cannot be changed.")
        if status == "published" and not source.requirements:
            raise ValidationException("Add at least one requirement before publishing.")
        source.status = status
        for requirement in source.requirements:
            requirement.status = status
            requirement.is_active = status == "published"
        if status == "published":
            self._assign_to_existing_releases(source)
        self.db.commit()
        return self.get(source.id)

    def _replace_products(self, source: RequirementSource, product_ids: list[UUID]) -> None:
        source.product_links[:] = [RequirementSourceProduct(product_id=product_id) for product_id in dict.fromkeys(product_ids)]

    def _validate_products(self, product_ids: list[UUID]) -> None:
        if not product_ids:
            return
        found = set(self.db.scalars(select(Product.id).where(Product.id.in_(product_ids))))
        if found != set(product_ids):
            raise ValidationException("One or more selected products do not exist.")

    def _assign_to_existing_releases(self, source: RequirementSource) -> None:
        release_stmt = select(ProductRelease.id).outerjoin(
            ReleaseRequirementAssessment,
            ReleaseRequirementAssessment.product_release_id == ProductRelease.id,
        ).where(or_(
            ReleaseRequirementAssessment.id.is_(None),
            ReleaseRequirementAssessment.status != RequirementAssessmentStatus.approved,
        ))
        if not source.organization_wide:
            release_stmt = release_stmt.where(ProductRelease.product_id.in_(source.product_ids))
        release_ids = list(self.db.scalars(release_stmt))
        existing = set(self.db.execute(select(ReleaseRequirementBaseline.product_release_id, ReleaseRequirementBaseline.requirement_id)).all())
        for release_id in release_ids:
            for requirement in source.requirements:
                if (release_id, requirement.id) not in existing:
                    self.db.add(ReleaseRequirementBaseline(product_release_id=release_id, requirement_id=requirement.id, requirement_revision=requirement.revision))
