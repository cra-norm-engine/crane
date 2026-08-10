from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.audit import create_audit_event
from app.core.exceptions import NotFoundException
from app.models.enums import AuditStatus, EntityType, SupplierAssessmentStatus
from app.models.evidence_item import EvidenceItem
from app.models.product import ProductRelease
from app.models.risk_item import RiskItem
from app.models.sbom_record import SbomRecord
from app.models.sbom_vulnerability_finding import SbomVulnerabilityFinding
from app.models.supplier_assessment import (AssessmentEvidenceLink, AssessmentResponse, ProductComponentLink,
    ComponentMaintainerNotification, Supplier, SupplierAssessment, SupplierFinding, ThirdPartyComponent)
from app.models.vulnerability_report import VulnerabilityReport
from app.repositories.supplier_assessment_repository import SupplierAssessmentRepository
from app.schemas.supplier_assessment import *


def match_registered_component(db: Session, name: str, version: str | None, purl: str | None, release_id=None):
    """Deterministically correlate scanner identity to the supplier component register."""
    identity = ((func.lower(ThirdPartyComponent.purl) == purl.lower()) if purl else
        ((func.lower(ThirdPartyComponent.name) == name.lower()) &
         (func.lower(func.coalesce(ThirdPartyComponent.version, "")) == (version or "").lower())))
    stmt = select(ThirdPartyComponent).where(identity)
    if release_id:
        linked = list(db.scalars(stmt.join(ProductComponentLink).where(
            ProductComponentLink.product_release_id == release_id)).all())
        if len(linked) == 1: return linked[0]
    candidates = list(db.scalars(stmt.limit(2)).all())
    return candidates[0] if len(candidates) == 1 else None


class SupplierAssessmentService:
    def __init__(self, db: Session): self.db, self.repo = db, SupplierAssessmentRepository(db)
    def _audit(self, actor_id, entity_type, entity_id, action, details=None):
        create_audit_event(self.db, actor_user_id=actor_id, action_type=action, entity_type=entity_type,
            entity_id=entity_id, status=AuditStatus.success, details_json=details or {})
    def _commit(self, value): self.db.commit(); self.db.refresh(value); return value
    @staticmethod
    def _editable(a):
        if a.status != SupplierAssessmentStatus.draft: raise ValueError("Only draft assessments can be edited")

    def list_suppliers(self): return [SupplierRead.model_validate(x) for x in self.repo.suppliers()]
    def create_supplier(self, p: SupplierCreate, actor_id):
        x = Supplier(**p.model_dump()); self.db.add(x); self.db.flush(); self._audit(actor_id, EntityType.supplier, x.id, "create"); return SupplierRead.model_validate(self._commit(x))
    def update_supplier(self, entity_id, p: SupplierUpdate, actor_id):
        x = self.repo.supplier(entity_id)
        for k,v in p.model_dump(exclude_unset=True).items(): setattr(x,k,v)
        self._audit(actor_id, EntityType.supplier, x.id, "update", p.model_dump(exclude_unset=True, mode="json")); return SupplierRead.model_validate(self._commit(x))

    def list_components(self, supplier_id=None): return [ComponentRead.model_validate(x) for x in self.repo.components(supplier_id)]
    def create_component(self, p: ComponentCreate, actor_id):
        self.repo.supplier(p.supplier_id); x=ThirdPartyComponent(**p.model_dump()); self.db.add(x); self.db.flush(); self._audit(actor_id,EntityType.third_party_component,x.id,"create"); return ComponentRead.model_validate(self._commit(x))
    def update_component(self, entity_id, p: ComponentUpdate, actor_id):
        x = self.repo.component(entity_id)
        changes = p.model_dump(exclude_unset=True)
        for key, value in changes.items(): setattr(x, key, value)
        if changes:
            self._trigger_reassessment(x.supplier_id, x.id, "Component identity, support, or update information changed")
        self._audit(actor_id, EntityType.third_party_component, x.id, "update", p.model_dump(exclude_unset=True, mode="json"))
        return ComponentRead.model_validate(self._commit(x))

    def _trigger_reassessment(self, supplier_id, component_id, reason):
        rows = self.db.scalars(select(SupplierAssessment).where(
            SupplierAssessment.supplier_id == supplier_id,
            SupplierAssessment.status.in_(["approved", "approved_with_conditions"]),
            (SupplierAssessment.component_id.is_(None)) | (SupplierAssessment.component_id == component_id),
        )).all()
        now = datetime.now(UTC)
        for item in rows:
            item.reassessment_required = True; item.reassessment_reason = reason
            item.reassessment_triggered_at = now; item.reassessment_due_date = date.today() + timedelta(days=30)

    def match_sbom(self, sbom_id, actor_id):
        sbom = self.db.get(SbomRecord, sbom_id)
        if sbom is None: raise NotFoundException("SBOM record not found")
        inventory = self.repo.components()
        by_purl = {c.purl.lower(): c for c in inventory if c.purl}
        by_name_version = {(c.name.lower(), (c.version or "").lower()): c for c in inventory}
        matched = linked = 0; unmatched = []
        for raw in sbom.components_json or []:
            name = str(raw.get("name") or raw.get("component") or "").strip()
            version = str(raw.get("version") or "").strip()
            purl = str(raw.get("purl") or raw.get("package_url") or "").strip()
            component = by_purl.get(purl.lower()) if purl else None
            component = component or by_name_version.get((name.lower(), version.lower()))
            if component is None:
                unmatched.append({"name": name, "version": version, "purl": purl}); continue
            matched += 1
            self.db.execute(
                SbomVulnerabilityFinding.__table__.update().where(
                    SbomVulnerabilityFinding.sbom_record_id == sbom.id,
                    ((func.lower(SbomVulnerabilityFinding.component_purl) == purl.lower()) if purl else
                     ((func.lower(SbomVulnerabilityFinding.component_name) == name.lower()) &
                      (func.lower(func.coalesce(SbomVulnerabilityFinding.component_version, "")) == version.lower()))),
                ).values(component_id=component.id)
            )
            exists = self.db.scalar(select(ProductComponentLink).where(ProductComponentLink.product_release_id==sbom.product_release_id,ProductComponentLink.component_id==component.id))
            if exists is None:
                self.db.add(ProductComponentLink(product_release_id=sbom.product_release_id,component_id=component.id,sbom_record_id=sbom.id,is_direct=True,is_core_function=False,criticality="medium",criticality_rationale="Matched from the release SBOM; criticality requires human confirmation."))
                linked += 1; self._trigger_reassessment(component.supplier_id,component.id,"Component integrated into a new product release")
        self._audit(actor_id,EntityType.sbom_record,sbom.id,"supplier_components_matched",{"matched":matched,"linked":linked,"unmatched":len(unmatched)})
        self.db.commit()
        return SbomMatchRead(sbom_record_id=sbom.id,product_release_id=sbom.product_release_id,matched=matched,linked=linked,unmatched=unmatched)

    def create_notification(self,p,actor_id):
        report=self.db.get(VulnerabilityReport,p.vulnerability_report_id)
        if report is None: raise NotFoundException("Vulnerability report not found")
        component=self.repo.component(p.component_id)
        linked=self.db.scalar(select(ProductComponentLink).where(ProductComponentLink.product_release_id==report.product_release_id,ProductComponentLink.component_id==component.id))
        if linked is None: raise ValueError("Component is not linked to the affected product release")
        x=ComponentMaintainerNotification(**p.model_dump(),status="draft",created_by_user_id=actor_id)
        self.db.add(x);self.db.flush();self._audit(actor_id,EntityType.component_maintainer_notification,x.id,"create");return MaintainerNotificationRead.model_validate(self._commit(x))
    def list_notifications(self,vulnerability_report_id=None):
        stmt=select(ComponentMaintainerNotification).order_by(ComponentMaintainerNotification.created_at.desc())
        if vulnerability_report_id: stmt=stmt.where(ComponentMaintainerNotification.vulnerability_report_id==vulnerability_report_id)
        return [MaintainerNotificationRead.model_validate(x) for x in self.db.scalars(stmt).all()]
    def update_notification(self,entity_id,p,actor_id):
        x=self.db.get(ComponentMaintainerNotification,entity_id)
        if x is None: raise NotFoundException("Maintainer notification not found")
        changes=p.model_dump(exclude_unset=True)
        for key,value in changes.items(): setattr(x,key,value)
        now=datetime.now(UTC)
        if changes.get("status")=="sent" and x.notified_at is None:x.notified_at=now
        if changes.get("status")=="acknowledged" and x.acknowledged_at is None:x.acknowledged_at=now
        self._audit(actor_id,EntityType.component_maintainer_notification,x.id,"update",p.model_dump(exclude_unset=True,mode="json"));return MaintainerNotificationRead.model_validate(self._commit(x))
    def link_component(self, p: ComponentLinkCreate, actor_id):
        component = self.repo.component(p.component_id)
        if self.db.get(ProductRelease,p.product_release_id) is None: raise NotFoundException("Product release not found")
        if p.sbom_record_id:
            sbom = self.db.get(SbomRecord,p.sbom_record_id)
            if sbom is None: raise NotFoundException("SBOM record not found")
            if sbom.product_release_id != p.product_release_id: raise ValueError("SBOM does not belong to the selected product release")
        if self.db.scalar(select(ProductComponentLink.id).where(ProductComponentLink.product_release_id==p.product_release_id,ProductComponentLink.component_id==p.component_id)):
            raise ValueError("This component is already linked to the selected product release")
        x=ProductComponentLink(**p.model_dump()); self.db.add(x); self.db.flush(); self._audit(actor_id,EntityType.third_party_component,x.component_id,"link_release",{"release_id":str(x.product_release_id)}); return ComponentLinkRead.model_validate(self._commit(x))
    def update_component_link(self, entity_id, p: ComponentLinkUpdate, actor_id):
        x = self.db.get(ProductComponentLink, entity_id)
        if x is None: raise NotFoundException("Product-component link not found")
        changes = p.model_dump(exclude_unset=True)
        release_id = changes.get("product_release_id", x.product_release_id)
        component_id = changes.get("component_id", x.component_id)
        component = self.repo.component(component_id)
        if self.db.get(ProductRelease, release_id) is None: raise NotFoundException("Product release not found")
        sbom_id = changes.get("sbom_record_id", x.sbom_record_id)
        if sbom_id:
            sbom = self.db.get(SbomRecord, sbom_id)
            if sbom is None: raise NotFoundException("SBOM record not found")
            if sbom.product_release_id != release_id: raise ValueError("SBOM does not belong to the selected product release")
        duplicate = self.db.scalar(select(ProductComponentLink.id).where(
            ProductComponentLink.product_release_id == release_id,
            ProductComponentLink.component_id == component_id,
            ProductComponentLink.id != entity_id,
        ))
        if duplicate: raise ValueError("This component is already linked to the selected product release")
        for key, value in changes.items(): setattr(x, key, value)
        self._trigger_reassessment(component.supplier_id, component.id, "Product integration details changed")
        self._audit(actor_id, EntityType.third_party_component, component.id, "update_release_link", {"release_id": str(release_id)})
        return ComponentLinkRead.model_validate(self._commit(x))
    def delete_component_link(self, entity_id, actor_id):
        x = self.db.get(ProductComponentLink, entity_id)
        if x is None: raise NotFoundException("Product-component link not found")
        component = self.repo.component(x.component_id)
        details = {"release_id": str(x.product_release_id)}
        self._trigger_reassessment(component.supplier_id, component.id, "Component removed from a product release")
        self._audit(actor_id, EntityType.third_party_component, component.id, "unlink_release", details)
        self.db.delete(x); self.db.commit()
    def list_links(self, release_id):
        return [ComponentLinkRead.model_validate(x) for x in self.db.scalars(select(ProductComponentLink).where(ProductComponentLink.product_release_id==release_id)).all()]

    def traceability(self, supplier_id=None, component_id=None, product_id=None, release_id=None):
        from app.models.product import Product
        stmt = (select(ProductComponentLink, ThirdPartyComponent, Supplier, ProductRelease, Product)
            .join(ThirdPartyComponent, ThirdPartyComponent.id == ProductComponentLink.component_id)
            .join(Supplier, Supplier.id == ThirdPartyComponent.supplier_id)
            .join(ProductRelease, ProductRelease.id == ProductComponentLink.product_release_id)
            .join(Product, Product.id == ProductRelease.product_id)
            .order_by(Product.name, ProductRelease.system_version.desc(), ThirdPartyComponent.name))
        if supplier_id: stmt = stmt.where(Supplier.id == supplier_id)
        if component_id: stmt = stmt.where(ThirdPartyComponent.id == component_id)
        if product_id: stmt = stmt.where(Product.id == product_id)
        if release_id: stmt = stmt.where(ProductRelease.id == release_id)
        result = []
        for link, component, supplier, release, product in self.db.execute(stmt).all():
            assessment = self.db.scalar(select(SupplierAssessment).where(
                SupplierAssessment.supplier_id == supplier.id,
                (SupplierAssessment.component_id.is_(None)) | (SupplierAssessment.component_id == component.id),
            ).order_by(SupplierAssessment.system_version.desc()).limit(1))
            notices = self.db.scalar(select(func.count()).select_from(ComponentMaintainerNotification).where(
                ComponentMaintainerNotification.component_id == component.id)) or 0
            sbom = self.db.get(SbomRecord, link.sbom_record_id) if link.sbom_record_id else None
            result.append(ComponentTraceabilityRead.model_validate({
                **ComponentLinkRead.model_validate(link).model_dump(),
                "supplier_id": supplier.id, "supplier_name": supplier.name,
                "component_name": component.name, "component_version": component.version,
                "product_id": product.id, "product_name": product.name, "product_code": product.product_code,
                "release_version": release.user_version or f"v{release.system_version}",
                "sbom_file_name": sbom.file_name if sbom else None,
                "assessment_id": assessment.id if assessment else None,
                "assessment_status": assessment.status if assessment else None,
                "assessment_valid_until": assessment.valid_until if assessment else None,
                "reassessment_required": assessment.reassessment_required if assessment else False,
                "maintainer_notification_count": notices,
            }))
        return result

    def component_vulnerabilities(self, component_id):
        from app.models.product import Product
        component = self.repo.component(component_id)
        findings = self.db.scalars(select(SbomVulnerabilityFinding).where(
            SbomVulnerabilityFinding.component_id == component_id
        ).order_by(SbomVulnerabilityFinding.created_at.desc())).all()
        links = self.db.execute(select(ProductComponentLink, ProductRelease, Product)
            .join(ProductRelease, ProductRelease.id == ProductComponentLink.product_release_id)
            .join(Product, Product.id == ProductRelease.product_id)
            .where(ProductComponentLink.component_id == component_id)).all()
        affected = [{"product_id": str(product.id), "product_name": product.name,
            "release_id": str(release.id), "release_version": release.user_version or f"v{release.system_version}"}
            for _, release, product in links]
        result = []
        for finding in findings:
            report = self.db.get(VulnerabilityReport, finding.linked_report_id) if finding.linked_report_id else None
            sbom = self.db.get(SbomRecord, finding.sbom_record_id)
            finding_affected = list(affected)
            if not any(row["release_id"] == str(sbom.product_release_id) for row in finding_affected):
                detected_release, detected_product = self.db.execute(select(ProductRelease, Product).join(Product, Product.id == ProductRelease.product_id).where(
                    ProductRelease.id == sbom.product_release_id)).one()
                finding_affected.append({"product_id": str(detected_product.id), "product_name": detected_product.name,
                    "release_id": str(detected_release.id), "release_version": detected_release.user_version or f"v{detected_release.system_version}"})
            result.append(ComponentVulnerabilityTraceRead(
                finding_id=finding.id, vulnerability_report_id=finding.linked_report_id,
                component_id=component.id, vulnerability_id=finding.vuln_id,
                aliases=finding.aliases_json or [], title=(report.title if report else finding.summary or finding.vuln_id),
                severity=finding.severity, status=str(report.status.value if hasattr(report.status,"value") else report.status) if report else None,
                cvss_score=finding.cvss_score, is_known_exploited=finding.is_known_exploited,
                fixed_versions=finding.fixed_in_versions_json or [], source_sbom_id=finding.sbom_record_id,
                detected_release_id=sbom.product_release_id, affected_releases=finding_affected,
            ))
        return result

    def list_assessments(self,supplier_id=None): return [AssessmentRead.model_validate(x) for x in self.repo.assessments(supplier_id)]
    def get_assessment(self,entity_id): return AssessmentRead.model_validate(self.repo.assessment(entity_id))
    def create_assessment(self,p:AssessmentCreate,actor_id):
        self.repo.supplier(p.supplier_id)
        if p.component_id:
            c=self.repo.component(p.component_id)
            if c.supplier_id != p.supplier_id: raise ValueError("Component does not belong to supplier")
        if p.product_release_id and self.db.get(ProductRelease,p.product_release_id) is None: raise NotFoundException("Product release not found")
        x=SupplierAssessment(**p.model_dump(),system_version=self.repo.next_version(p.supplier_id),status="draft",owner_user_id=actor_id)
        self.db.add(x); self.db.flush(); self._audit(actor_id,EntityType.supplier_assessment,x.id,"create"); self._commit(x); return self.get_assessment(x.id)
    def update_assessment(self,entity_id,p,actor_id):
        x=self.repo.assessment(entity_id); self._editable(x)
        for k,v in p.model_dump(exclude_unset=True).items(): setattr(x,k,v)
        self._audit(actor_id,EntityType.supplier_assessment,x.id,"update",p.model_dump(exclude_unset=True,mode="json")); self._commit(x); return self.get_assessment(x.id)
    def upsert_response(self,entity_id,p,actor_id):
        a=self.repo.assessment(entity_id); self._editable(a)
        x=self.db.scalar(select(AssessmentResponse).where(AssessmentResponse.assessment_id==entity_id,AssessmentResponse.criterion_key==p.criterion_key))
        if x is None: x=AssessmentResponse(assessment_id=entity_id,**p.model_dump()); self.db.add(x)
        else:
            for k,v in p.model_dump().items(): setattr(x,k,v)
        self.db.flush(); self._audit(actor_id,EntityType.supplier_assessment,a.id,"response_upsert",{"criterion_key":p.criterion_key}); self._commit(x); return ResponseRead.model_validate(x)
    def link_evidence(self,entity_id,p,actor_id):
        a=self.repo.assessment(entity_id); self._editable(a)
        if self.db.get(EvidenceItem,p.evidence_item_id) is None: raise NotFoundException("Evidence item not found")
        if p.response_id:
            r=self.db.get(AssessmentResponse,p.response_id)
            if r is None or r.assessment_id != entity_id: raise ValueError("Response does not belong to assessment")
        x=AssessmentEvidenceLink(assessment_id=entity_id,**p.model_dump()); self.db.add(x); self.db.flush(); self._audit(actor_id,EntityType.supplier_assessment,a.id,"evidence_link"); return EvidenceLinkRead.model_validate(self._commit(x))
    def review_evidence(self,entity_id,link_id,p,actor_id):
        self.repo.assessment(entity_id); x=self.db.get(AssessmentEvidenceLink,link_id)
        if x is None or x.assessment_id != entity_id: raise NotFoundException("Assessment evidence link not found")
        x.review_status=p.review_status.value; x.review_notes=p.review_notes; x.reviewed_by_user_id=actor_id; x.reviewed_at=datetime.now(UTC)
        self._audit(actor_id,EntityType.supplier_assessment,entity_id,"evidence_review",{"status":x.review_status}); return EvidenceLinkRead.model_validate(self._commit(x))
    def add_finding(self,entity_id,p,actor_id):
        a=self.repo.assessment(entity_id); self._editable(a)
        if p.risk_item_id and self.db.get(RiskItem,p.risk_item_id) is None: raise NotFoundException("Risk item not found")
        x=SupplierFinding(assessment_id=entity_id,status="open",**p.model_dump()); self.db.add(x); self.db.flush(); self._audit(actor_id,EntityType.supplier_finding,x.id,"create"); return FindingRead.model_validate(self._commit(x))
    def update_finding(self,entity_id,finding_id,p,actor_id):
        self.repo.assessment(entity_id); x=self.db.get(SupplierFinding,finding_id)
        if x is None or x.assessment_id != entity_id: raise NotFoundException("Supplier finding not found")
        for k,v in p.model_dump(exclude_unset=True).items(): setattr(x,k,v)
        self._audit(actor_id,EntityType.supplier_finding,x.id,"update"); return FindingRead.model_validate(self._commit(x))
    def submit(self,entity_id,actor_id):
        x=self.repo.assessment(entity_id); self._editable(x)
        if not x.responses: raise ValueError("At least one assessment response is required")
        x.status="in_review"; x.submitted_at=datetime.now(UTC); self._audit(actor_id,EntityType.supplier_assessment,x.id,"submit"); self._commit(x); return self.get_assessment(x.id)
    def decide(self,entity_id,p,actor_id):
        x=self.repo.assessment(entity_id)
        if x.status != SupplierAssessmentStatus.in_review: raise ValueError("Only assessments in review can be decided")
        if actor_id == x.owner_user_id: raise ValueError("Assessment owner cannot approve their own assessment")
        if p.decision in {SupplierAssessmentStatus.approved,SupplierAssessmentStatus.approved_with_conditions}:
            if any(e.review_status != "accepted" or (e.valid_until and e.valid_until < date.today()) for e in x.evidence_links): raise ValueError("All linked evidence must be current and accepted")
            if p.decision == SupplierAssessmentStatus.approved and any(f.status in {"open","in_progress"} and f.severity in {"high","critical"} for f in x.findings): raise ValueError("High or critical open findings prevent approval")
        x.status=p.decision.value; x.conclusion=p.conclusion; x.rejection_reason=p.rejection_reason; x.valid_until=p.valid_until; x.reviewer_user_id=actor_id; x.reviewed_at=datetime.now(UTC)
        x.reassessment_required=False; x.reassessment_reason=None; x.reassessment_triggered_at=None; x.reassessment_due_date=None
        self._audit(actor_id,EntityType.supplier_assessment,x.id,"approve" if "approved" in x.status else "reject",{"decision":x.status}); self._commit(x); return self.get_assessment(x.id)


def release_due_diligence_status(db: Session, release_id: UUID) -> dict:
    links = list(db.scalars(select(ProductComponentLink).where(
        ProductComponentLink.product_release_id == release_id
    ).options(selectinload(ProductComponentLink.component))).all())
    today = date.today(); gaps = []
    for link in links:
        if link.criticality not in {"medium", "high"}: continue
        approved = db.scalar(select(SupplierAssessment).where(
            SupplierAssessment.supplier_id == link.component.supplier_id,
            (SupplierAssessment.component_id.is_(None)) | (SupplierAssessment.component_id == link.component_id),
            SupplierAssessment.status.in_(["approved", "approved_with_conditions"]),
            SupplierAssessment.reassessment_required.is_(False),
            (SupplierAssessment.valid_until.is_(None)) | (SupplierAssessment.valid_until >= today),
        ).order_by(SupplierAssessment.system_version.desc()))
        if approved is None: gaps.append({"component_id":str(link.component_id),"component_name":link.component.name,"criticality":link.criticality})
    return {"complete":not gaps,"relevant_components":len(links),"gaps":gaps}
