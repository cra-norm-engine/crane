from __future__ import annotations

import logging
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.core.maturity_catalog import ATTRIBUTION, CATALOG, CRANE_SUPPORT, MODEL, RECOMMENDATIONS
from app.models import Artifact, AuditLogEvent, CertificationRecord, CvdPolicy, IncidentReport, MaturityAssessment, MaturityEvidenceLink, MaturityImprovementAction, MaturityModelVersion, MaturityResponse, Product, ReleaseGate, RequirementMapping, RiskAssessment, SbomRecord, SecurityAdvisory, SecurityUpdate, SupportPeriodRecord, User, VulnerabilityReport
from app.models.base import utc_now
from app.schemas.maturity import ActionUpdate, EvidenceCreate, MaturityCreate, ResponseUpdate

logger = logging.getLogger(__name__)


class MaturityService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _model(self) -> MaturityModelVersion:
        model = self.db.query(MaturityModelVersion).filter_by(code=MODEL["code"]).first()
        if model:
            return model
        model = MaturityModelVersion(**MODEL, catalog_json=CATALOG)
        self.db.add(model)
        self.db.flush()
        return model

    def list(self) -> list[MaturityAssessment]:
        return self.db.query(MaturityAssessment).order_by(MaturityAssessment.created_at.desc()).all()

    def _get(self, assessment_id: UUID) -> MaturityAssessment:
        assessment = self.db.query(MaturityAssessment).options(selectinload(MaturityAssessment.responses).selectinload(MaturityResponse.evidence_links), selectinload(MaturityAssessment.actions)).filter_by(id=assessment_id).first()
        if not assessment:
            raise NotFoundException("Maturity assessment not found")
        return assessment

    def create(self, payload: MaturityCreate, actor_id: UUID) -> MaturityAssessment:
        try:
            model = self._model()
            assessment = MaturityAssessment(**payload.model_dump(), model_version_id=model.id, assessor_user_id=actor_id, catalog_snapshot_json=model.catalog_json)
            self.db.add(assessment)
            self.db.flush()
            for question in model.catalog_json:
                self.db.add(MaturityResponse(assessment_id=assessment.id, question_code=question["code"]))
            create_audit_event(self.db, actor_user_id=actor_id, action_type="maturity.created", entity_type="maturity_assessment", entity_id=assessment.id, status="success")
            self.db.commit()
            return self._get(assessment.id)
        except SQLAlchemyError:
            self.db.rollback()
            logger.exception("Failed to create maturity assessment")
            raise

    @staticmethod
    def results(assessment: MaturityAssessment) -> dict:
        by_domain: dict[str, list[int]] = defaultdict(list)
        for response in assessment.responses:
            if response.score is not None:
                by_domain[response.question_code[0]].append(response.score)
        domains = {code: float(sum(scores) / Decimal(len(scores))) if scores else None for code, scores in by_domain.items()}
        complete = len([r for r in assessment.responses if r.score is not None]) == len(assessment.catalog_snapshot_json)
        overall = float(sum(Decimal(str(v)) for v in domains.values()) / Decimal(5)) if complete else None
        profile = None if overall is None else "advanced" if overall >= 4 else "intermediate" if overall >= 2.6 else "basic"
        answered = [r for r in assessment.responses if r.score is not None]
        supported = [r for r in answered if getattr(r, "evidence_links", [])]
        contradictions = [f"{r.question_code}: Level {r.score} has no linked evidence" for r in answered if (r.score or 0) >= 4 and not getattr(r, "evidence_links", [])]
        return {"domain_scores": domains, "overall_score": overall, "profile": profile, "complete": complete, "weak_domains": [k for k, v in domains.items() if v is not None and v < 2.6], "evidence_coverage": round(len(supported) / len(answered) * 100, 1) if answered else 0, "contradictions": contradictions, "disclaimer": "This maturity result is not proof of CRA compliance."}

    def update_response(self, assessment_id: UUID, code: str, payload: ResponseUpdate, actor_id: UUID) -> MaturityAssessment:
        assessment = self._get(assessment_id)
        if assessment.status != "draft":
            raise ConflictException("Only draft assessments can be edited")
        response = next((r for r in assessment.responses if r.question_code == code), None)
        if not response:
            raise NotFoundException("Maturity question not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(response, key, value)
        create_audit_event(self.db, actor_user_id=actor_id, action_type="maturity.response.updated", entity_type="maturity_assessment", entity_id=assessment.id, status="success", details_json={"question_code": code, "score": response.score})
        self.db.commit()
        return self._get(assessment_id)

    def transition(self, assessment_id: UUID, action: str, actor_id: UUID, justification: str | None = None) -> MaturityAssessment:
        assessment = self._get(assessment_id)
        if action == "submit":
            if assessment.status != "draft":
                raise ConflictException("Only draft assessments can be submitted")
            if not self.results(assessment)["complete"]:
                raise ValidationException("All 25 questions must be answered before submission")
            assessment.status, assessment.submitted_at = "submitted", utc_now()
            if not assessment.actions:
                for response in assessment.responses:
                    if response.score and response.score < 4:
                        assessment.actions.append(MaturityImprovementAction(question_code=response.question_code, domain_code=response.question_code[0], title=f"{response.question_code}: {RECOMMENDATIONS[response.question_code[0]]}", priority="high" if response.score < 3 else "medium"))
            assessment.reassessment_due_date = utc_now().date() + timedelta(days=365)
        elif action == "approve":
            if assessment.status != "submitted":
                raise ConflictException("Only submitted assessments can be approved")
            unsupported_high = [r for r in assessment.responses if (r.score or 0) >= 4 and not r.evidence_links]
            if unsupported_high and not (justification or "").strip():
                raise ValidationException("Reviewer justification is required for unsupported Level 4 or 5 answers")
            assessment.status, assessment.approved_at, assessment.reviewer_user_id = "approved", utc_now(), actor_id
            assessment.reviewer_justification = justification
        else:
            raise ValidationException("Unknown workflow action")
        create_audit_event(self.db, actor_user_id=actor_id, action_type=f"maturity.{action}", entity_type="maturity_assessment", entity_id=assessment.id, status="success")
        self.db.commit()
        return self._get(assessment_id)

    def update_action(self, assessment_id: UUID, action_id: UUID, payload: ActionUpdate, actor_id: UUID) -> MaturityAssessment:
        assessment = self._get(assessment_id)
        action = next((item for item in assessment.actions if item.id == action_id), None)
        if not action:
            raise NotFoundException("Improvement action not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(action, key, value)
        create_audit_event(self.db, actor_user_id=actor_id, action_type="maturity.action.updated", entity_type="maturity_action", entity_id=action.id, status="success")
        self.db.commit()
        return self._get(assessment_id)

    def add_evidence(self, assessment_id: UUID, code: str, payload: EvidenceCreate, actor_id: UUID) -> MaturityAssessment:
        assessment = self._get(assessment_id)
        response = next((r for r in assessment.responses if r.question_code == code), None)
        if not response:
            raise NotFoundException("Maturity question not found")
        response.evidence_links.append(MaturityEvidenceLink(**payload.model_dump(), added_by_user_id=actor_id))
        create_audit_event(self.db, actor_user_id=actor_id, action_type="maturity.evidence.linked", entity_type="maturity_assessment", entity_id=assessment.id, status="success", details_json={"question_code": code, "entity_type": payload.entity_type})
        self.db.commit()
        return self._get(assessment_id)

    def suggestions(self) -> dict[str, list[dict]]:
        adapters = {
            "1.1": (Artifact, "Policy artifact"), "1.2": (User, "Assigned user or role"),
            "1.3": (Artifact, "Technical artifact"), "1.4": (AuditLogEvent, "Review audit event"),
            "1.5": (CertificationRecord, "Conformity record"),
            "2.1": (RiskAssessment, "Risk assessment"), "2.2": (RequirementMapping, "Security-by-design mapping"),
            "2.3": (RequirementMapping, "Secure-default evidence"), "2.4": (ReleaseGate, "Release gate"),
            "2.5": (RiskAssessment, "Risk review"),
            "3.1": (CvdPolicy, "CVD policies"), "3.2": (SecurityUpdate, "Security updates"),
            "3.3": (SbomRecord, "SBOM records"), "3.4": (VulnerabilityReport, "Vulnerability reports"),
            "3.5": (SecurityUpdate, "Fix and update evidence"),
            "4.1": (VulnerabilityReport, "Operational security records"), "4.2": (SupportPeriodRecord, "Support period records"),
            "4.3": (IncidentReport, "Incident and operational learning records"), "4.4": (ReleaseGate, "Tested release-gate records"),
            "4.5": (SbomRecord, "SBOM monitoring records"),
            "5.1": (User, "Security role assignment"), "5.3": (AuditLogEvent, "Accountability audit event"),
            "5.4": (SecurityAdvisory, "External security advisory"), "5.5": (User, "Role assignment (not competence proof)"),
        }
        result: dict[str, list[dict]] = {}
        for code, (model, label) in adapters.items():
            order_column = getattr(model, "created_at", None)
            if order_column is None:
                order_column = model.occurred_at
            rows = self.db.query(model).order_by(order_column.desc()).limit(10).all()
            result[code] = [{"entity_type": model.__tablename__, "entity_id": str(row.id), "label": f"{label}: {getattr(row, 'title', None) or getattr(row, 'name', None) or getattr(row, 'file_name', None) or str(row.id)[:8]}"} for row in rows]
        return result

    def detail(self, assessment_id: UUID) -> dict:
        assessment = self._get(assessment_id)
        previous = self.db.query(MaturityAssessment).options(selectinload(MaturityAssessment.responses)).filter(MaturityAssessment.status == "approved", MaturityAssessment.id != assessment.id).order_by(MaturityAssessment.approved_at).all()
        current_results = self.results(assessment)
        return {
            **{key: getattr(assessment, key) for key in ("id", "title", "scope", "status", "period_start", "period_end", "assessor_user_id", "reviewer_user_id", "submitted_at", "approved_at", "reassessment_due_date", "created_at")},
            "catalog": [{**question, "crane_support": CRANE_SUPPORT.get(question["code"])} for question in assessment.catalog_snapshot_json],
            "responses": [{"id": r.id, "question_code": r.question_code, "score": r.score, "rationale": r.rationale, "confidence": r.confidence, "assessor_notes": r.assessor_notes, "evidence": [{"id": e.id, "entity_type": e.entity_type, "entity_id": e.entity_id, "label": e.label} for e in r.evidence_links]} for r in assessment.responses],
            "actions": assessment.actions,
            "results": current_results,
            "attribution": ATTRIBUTION,
            "evidence_suggestions": self.suggestions(),
            "history": [{"id": item.id, "title": item.title, "approved_at": item.approved_at, **self.results(item)} for item in previous] + ([{"id": assessment.id, "title": assessment.title, "approved_at": assessment.approved_at, **current_results}] if current_results["overall_score"] is not None else []),
        }
