import hashlib
import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event, snapshot_model
from app.core.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException
from app.models.base import utc_now
from app.models.evidence_item import EvidenceItem
from app.models.product import Product, ProductRelease
from app.models.sbom_record import SbomRecord
from app.models.risk_assessment import RiskAssessment
from app.models.vulnerability_report import VulnerabilityReport
from app.models.support_assessment import SupportAssessment
from app.models.support_period_record import SupportPeriodRecord
from app.models.supplier_assessment import ProductComponentLink, Supplier, ThirdPartyComponent
from app.schemas.support_advisor import AssessmentCreate, AssessmentReview
from app.services.support_advisor_rules import assess


class SupportAdvisorService:
    def __init__(self, db: Session):
        self.db = db

    def context(self, product_id: UUID, release_id: UUID):
        product = self.db.get(Product, product_id)
        release = self.db.get(ProductRelease, release_id)
        if not product or not release or release.product_id != product_id:
            raise NotFoundException("Product release not found")
        support = self.db.scalar(select(SupportPeriodRecord).where(
            SupportPeriodRecord.product_id == product_id,
            SupportPeriodRecord.is_active.is_(True),
            (SupportPeriodRecord.product_release_id == release_id) | SupportPeriodRecord.product_release_id.is_(None),
        ).order_by(SupportPeriodRecord.product_release_id.is_(None), SupportPeriodRecord.created_at.desc()).limit(1))
        rows = self.db.execute(select(ProductComponentLink, ThirdPartyComponent, Supplier)
            .join(ThirdPartyComponent, ThirdPartyComponent.id == ProductComponentLink.component_id)
            .join(Supplier, Supplier.id == ThirdPartyComponent.supplier_id)
            .where(ProductComponentLink.product_release_id == release_id)
            .order_by(ProductComponentLink.id)).all()
        components = []
        for link, component, supplier in rows:
            data = snapshot_model(component)
            components.append({**data, "link_id": str(link.id), "supplier_name": supplier.name,
                               "link_snapshot": snapshot_model(link), "supplier_snapshot": snapshot_model(supplier),
                               "criticality": link.criticality, "is_core_function": link.is_core_function})
        evidence = list(self.db.scalars(select(EvidenceItem).where(EvidenceItem.product_release_id == release_id).order_by(EvidenceItem.id)))
        sboms = list(self.db.scalars(select(SbomRecord).where(SbomRecord.product_release_id == release_id).order_by(SbomRecord.id)))
        risks = list(self.db.scalars(select(RiskAssessment).where(
            RiskAssessment.product_id == product_id,
            (RiskAssessment.product_release_id == release_id) | RiskAssessment.product_release_id.is_(None),
        ).order_by(RiskAssessment.id)))
        vulnerabilities = list(self.db.scalars(select(VulnerabilityReport).where(
            VulnerabilityReport.product_release_id == release_id).order_by(VulnerabilityReport.id)))
        context = {"product": snapshot_model(product), "release": snapshot_model(release),
                "support": snapshot_model(support) if support else None, "components": components,
                "evidence": [{k: v for k, v in snapshot_model(e).items() if k != "file_path"} for e in evidence],
                "sboms": [snapshot_model(s) for s in sboms],
                "risk_assessments": [snapshot_model(r) for r in risks],
                "vulnerabilities": [snapshot_model(v) for v in vulnerabilities]}
        context["context_version"] = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
        return context

    def _validated_context(self, product_id, payload: AssessmentCreate):
        context = self.context(product_id, payload.product_release_id)
        if payload.context_version != context["context_version"]:
            raise ConflictException("Source data changed while editing; reload the advisor before saving")
        available = {e["id"] for e in context["evidence"]}
        requested = {str(e) for e in payload.evidence_ids}
        links = {c["link_id"] for c in context["components"]}
        for remedy in payload.remediations:
            if str(remedy.component_link_id) not in links:
                raise ValidationException("Remediation component does not belong to this release")
            requested.update(str(e) for e in remedy.evidence_ids)
        if not requested <= available:
            raise ValidationException("Evidence must belong to the assessed release")
        return context

    def preview(self, product_id, payload: AssessmentCreate):
        context = self._validated_context(product_id, payload)
        return assess(payload, context["components"], context["sboms"])

    def create(self, product_id, payload: AssessmentCreate, actor):
        context = self._validated_context(product_id, payload)
        record = SupportAssessment(product_id=product_id, product_release_id=payload.product_release_id,
            author_id=actor.id, inputs=payload.model_dump(mode="json"), context_snapshot=context,
            result=assess(payload, context["components"], context["sboms"]))
        self.db.add(record)
        self.db.flush()
        self._audit(record, actor, "created")
        self.db.commit()
        return self.read(record)

    def get(self, product_id, assessment_id, lock=False):
        stmt = select(SupportAssessment).where(SupportAssessment.id == assessment_id, SupportAssessment.product_id == product_id)
        if lock:
            stmt = stmt.with_for_update()
        record = self.db.scalar(stmt)
        if not record:
            raise NotFoundException("Support assessment not found")
        return record

    def read(self, record):
        current = self.context(record.product_id, record.product_release_id)
        return {**snapshot_model(record), "needs_refresh": current != record.context_snapshot}

    def review(self, product_id, assessment_id, payload: AssessmentReview, actor):
        record = self.get(product_id, assessment_id, lock=True)
        if record.status != "pending_review":
            raise ConflictException("Decision already recorded; create a new assessment")
        if actor.id == record.author_id:
            raise ForbiddenException("An independent reviewer must record the decision")
        if payload.decision == "approved":
            if self.read(record)["needs_refresh"]:
                raise ConflictException("SP-007: source records changed; create a fresh assessment")
            if record.result["approval_blockers"]:
                raise ValidationException("Resolve missing evidence and remediation before approval")
        record.status = payload.decision
        record.reviewer_id = actor.id
        record.reviewed_at = utc_now()
        record.review_reason = payload.reason
        self._audit(record, actor, payload.decision)
        self.db.commit()
        return self.read(record)

    def _audit(self, record, actor, action):
        create_audit_event(self.db, actor_user_id=actor.id, action_type=f"support_advisor.{action}",
            entity_type="support_assessment", entity_id=record.id, status="success",
            details_json={"product_id": str(record.product_id), "product_release_id": str(record.product_release_id), "snapshot": snapshot_model(record)})
