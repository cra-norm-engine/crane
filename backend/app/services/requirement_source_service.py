from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.annex_requirement import RequirementSource, RequirementSourceProduct
from app.models.product import Product
from app.schemas.requirement_source import RequirementSourceCreate, RequirementSourceUpdate


class RequirementSourceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self):
        return select(RequirementSource).execution_options(populate_existing=True).options(
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
        edition = (payload.edition or "").strip()
        if not identifier or not payload.title.strip():
            raise ValidationException("Enter a source identifier and title.")
        if identifier == "CRA-ANNEX-I":
            raise ValidationException("The CRA source identifier is reserved.")
        if self.db.scalar(select(RequirementSource.id).where(RequirementSource.identifier == identifier, RequirementSource.edition == edition)):
            raise ConflictException("This source edition already exists. Use a different edition or version.")
        self._validate_products(payload.product_ids)
        source = RequirementSource(
            identifier=identifier, title=payload.title.strip(), source_type=payload.source_type,
            edition=edition, publisher=payload.publisher, reference_url=payload.reference_url,
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
        if "edition" in changes:
            changes["edition"] = (changes["edition"] or "").strip()
        if source.status != "draft" and (payload.product_ids is not None or any(key not in {"license_note", "reference_url"} for key in changes)):
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
        if (source.status, status) not in {("draft", "published"), ("published", "retired")}:
            raise ConflictException("Publish a draft or retire a published edition. Create a new edition for changes.")
        if status == "published" and not source.requirements:
            raise ValidationException("Add at least one requirement before publishing.")
        if status == "published" and any(not (r.acceptance_criteria or r.verification_guidance or "").strip() for r in source.requirements):
            raise ValidationException("Add acceptance criteria or verification guidance to every requirement before publishing.")
        source.status = status
        for requirement in source.requirements:
            requirement.status = status
            requirement.is_active = status == "published"
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
