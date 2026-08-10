from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.supplier_assessment import Supplier, SupplierAssessment, ThirdPartyComponent


class SupplierAssessmentRepository:
    def __init__(self, db: Session): self.db = db

    def suppliers(self): return list(self.db.scalars(select(Supplier).order_by(Supplier.name)).all())
    def supplier(self, entity_id: UUID):
        value = self.db.get(Supplier, entity_id)
        if value is None: raise NotFoundException("Supplier not found")
        return value
    def components(self, supplier_id: UUID | None = None):
        stmt = select(ThirdPartyComponent).order_by(ThirdPartyComponent.name)
        if supplier_id: stmt = stmt.where(ThirdPartyComponent.supplier_id == supplier_id)
        return list(self.db.scalars(stmt).all())
    def component(self, entity_id: UUID):
        value = self.db.get(ThirdPartyComponent, entity_id)
        if value is None: raise NotFoundException("Third-party component not found")
        return value
    def assessments(self, supplier_id: UUID | None = None):
        stmt = select(SupplierAssessment).options(*self._loads()).order_by(SupplierAssessment.created_at.desc())
        if supplier_id: stmt = stmt.where(SupplierAssessment.supplier_id == supplier_id)
        return list(self.db.scalars(stmt).unique().all())
    def assessment(self, entity_id: UUID):
        value = self.db.scalar(select(SupplierAssessment).where(SupplierAssessment.id == entity_id).options(*self._loads()))
        if value is None: raise NotFoundException("Supplier assessment not found")
        return value
    def next_version(self, supplier_id: UUID) -> int:
        return int(self.db.scalar(select(func.coalesce(func.max(SupplierAssessment.system_version), 0)).where(SupplierAssessment.supplier_id == supplier_id)) or 0) + 1
    @staticmethod
    def _loads():
        return (selectinload(SupplierAssessment.responses), selectinload(SupplierAssessment.evidence_links), selectinload(SupplierAssessment.findings))
