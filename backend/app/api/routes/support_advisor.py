from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.support_assessment import SupportAssessment
from app.models.user import User
from app.schemas.support_advisor import AssessmentCreate, AssessmentReview
from app.services.support_advisor_service import SupportAdvisorService

router = APIRouter(prefix="/products/{product_id}/support-advisor", tags=["support-advisor"])
read_permissions = (Permission.product_read, Permission.release_read, Permission.support_period_read,
                    Permission.supplier_assessment_read, Permission.evidence_item_read,
                    Permission.risk_assessment_read, Permission.vulnerability_report_read)
read = require_permissions_dependency(*read_permissions)
write = require_permissions_dependency(*read_permissions, Permission.support_period_write)
review = require_permissions_dependency(*read_permissions, Permission.support_period_write, Permission.supplier_assessment_approve)


@router.get("/context")
def context(product_id: UUID, release_id: UUID, db: Session = Depends(get_db), actor: User = Depends(read)):
    return SupportAdvisorService(db).context(product_id, release_id)


@router.get("/assessments")
def history(product_id: UUID, db: Session = Depends(get_db), actor: User = Depends(read)):
    service = SupportAdvisorService(db)
    records = db.scalars(select(SupportAssessment).where(SupportAssessment.product_id == product_id).order_by(SupportAssessment.created_at.desc())).all()
    return [service.read(r) for r in records]


@router.post("/preview")
def preview(product_id: UUID, payload: AssessmentCreate, db: Session = Depends(get_db), actor: User = Depends(read)):
    return SupportAdvisorService(db).preview(product_id, payload)


@router.post("/assessments", status_code=201)
def create(product_id: UUID, payload: AssessmentCreate, db: Session = Depends(get_db), actor: User = Depends(write)):
    return SupportAdvisorService(db).create(product_id, payload, actor)


@router.post("/assessments/{assessment_id}/review")
def decide(product_id: UUID, assessment_id: UUID, payload: AssessmentReview, db: Session = Depends(get_db), actor: User = Depends(review)):
    return SupportAdvisorService(db).review(product_id, assessment_id, payload, actor)


@router.get("/assessments/{assessment_id}/report")
def report(product_id: UUID, assessment_id: UUID, db: Session = Depends(get_db), actor: User = Depends(read)):
    service = SupportAdvisorService(db)
    record = service.get(product_id, assessment_id)
    # The stored snapshot is exported unchanged; current freshness is separate metadata.
    return JSONResponse(service.read(record), headers={"Content-Disposition": f'attachment; filename="support-assessment-{assessment_id}.json"'})
