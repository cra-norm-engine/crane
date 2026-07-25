from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from weasyprint import HTML

from app.api.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.maturity import ActionUpdate, EvidenceCreate, MaturityCreate, MaturityDetail, MaturityRead, ResponseUpdate
from app.services.maturity_service import MaturityService

router = APIRouter()


@router.get("", response_model=list[MaturityRead])
def list_assessments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_read})
    return MaturityService(db).list()


@router.post("", response_model=MaturityRead, status_code=201)
def create_assessment(payload: MaturityCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_write})
    return MaturityService(db).create(payload, current_user.id)


@router.get("/{assessment_id}", response_model=MaturityDetail)
def get_assessment(assessment_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_read})
    return MaturityService(db).detail(assessment_id)


@router.put("/{assessment_id}/responses/{code}", response_model=MaturityDetail)
def update_response(assessment_id: UUID, code: str, payload: ResponseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_write})
    service = MaturityService(db)
    service.update_response(assessment_id, code, payload, current_user.id)
    return service.detail(assessment_id)


@router.post("/{assessment_id}/evidence/{code}", response_model=MaturityDetail)
def add_evidence(assessment_id: UUID, code: str, payload: EvidenceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_write})
    service = MaturityService(db)
    service.add_evidence(assessment_id, code, payload, current_user.id)
    return service.detail(assessment_id)


@router.patch("/{assessment_id}/actions/{action_id}", response_model=MaturityDetail)
def update_action(assessment_id: UUID, action_id: UUID, payload: ActionUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_write})
    service = MaturityService(db)
    service.update_action(assessment_id, action_id, payload, current_user.id)
    return service.detail(assessment_id)


@router.post("/{assessment_id}/workflow/{action}", response_model=MaturityDetail)
def transition(assessment_id: UUID, action: str, justification: str | None = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_approve if action == "approve" else Permission.maturity_write})
    service = MaturityService(db)
    service.transition(assessment_id, action, current_user.id, justification)
    return service.detail(assessment_id)


@router.get("/{assessment_id}/export.json")
def export_json(assessment_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_read})
    data = MaturityService(db).detail(assessment_id)
    return JSONResponse(json.loads(json.dumps(data, default=str)), headers={"Content-Disposition": f'attachment; filename="maturity-{assessment_id}.json"'})


@router.get("/{assessment_id}/export.pdf")
def export_pdf(assessment_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    require_permissions(current_user, {Permission.maturity_read})
    data = MaturityService(db).detail(assessment_id)
    results = data["results"]
    domains = "".join(f"<li>Domain {code}: {score:.2f}</li>" for code, score in results["domain_scores"].items())
    attribution = data["attribution"]
    html = f"<h1>{data['title']}</h1><p>Scope: {data['scope']}</p><h2>{(results['profile'] or 'Incomplete').title()}</h2><p>Overall: {results['overall_score'] or 'Incomplete'}</p><ul>{domains}</ul><p><strong>{results['disclaimer']}</strong></p><hr><small>Based on <a href='{attribution['source_url']}'>{attribution['title']}</a>, {attribution['copyright']}, licensed under <a href='{attribution['license_url']}'>CC BY 4.0</a>. {attribution['changes']} {attribution['endorsement']}</small>"
    return Response(HTML(string=html).write_pdf(), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="maturity-{assessment_id}.pdf"'})
