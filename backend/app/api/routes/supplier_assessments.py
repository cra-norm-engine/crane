from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.supplier_assessment import *
from app.services.supplier_assessment_service import SupplierAssessmentService

router = APIRouter()

def read_user(): return require_permissions_dependency(Permission.supplier_assessment_read)
def write_user(): return require_permissions_dependency(Permission.supplier_assessment_write)

@router.get("/suppliers", response_model=list[SupplierRead])
def suppliers(db:Session=Depends(get_db), user:User=Depends(read_user())): return SupplierAssessmentService(db).list_suppliers()
@router.post("/suppliers", response_model=SupplierRead, status_code=status.HTTP_201_CREATED)
def create_supplier(p:SupplierCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).create_supplier(p,user.id)
@router.patch("/suppliers/{entity_id}", response_model=SupplierRead)
def update_supplier(entity_id:UUID,p:SupplierUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_supplier(entity_id,p,user.id)

@router.get("/components", response_model=list[ComponentRead])
def components(supplier_id:UUID|None=Query(None),db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).list_components(supplier_id)
@router.post("/components", response_model=ComponentRead, status_code=status.HTTP_201_CREATED)
def create_component(p:ComponentCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).create_component(p,user.id)
@router.patch("/components/{entity_id}", response_model=ComponentRead)
def update_component(entity_id:UUID,p:ComponentUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_component(entity_id,p,user.id)
@router.post("/component-links", response_model=ComponentLinkRead, status_code=status.HTTP_201_CREATED)
def link_component(p:ComponentLinkCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).link_component(p,user.id)
@router.patch("/component-links/{entity_id}", response_model=ComponentLinkRead)
def update_component_link(entity_id:UUID,p:ComponentLinkUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_component_link(entity_id,p,user.id)
@router.delete("/component-links/{entity_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_component_link(entity_id:UUID,db:Session=Depends(get_db),user:User=Depends(write_user())): SupplierAssessmentService(db).delete_component_link(entity_id,user.id); return Response(status_code=status.HTTP_204_NO_CONTENT)
@router.get("/component-links", response_model=list[ComponentLinkRead])
def links(product_release_id:UUID,db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).list_links(product_release_id)
@router.get("/traceability", response_model=list[ComponentTraceabilityRead])
def traceability(supplier_id:UUID|None=Query(None),component_id:UUID|None=Query(None),product_id:UUID|None=Query(None),product_release_id:UUID|None=Query(None),db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).traceability(supplier_id,component_id,product_id,product_release_id)
@router.get("/components/{component_id}/vulnerabilities", response_model=list[ComponentVulnerabilityTraceRead])
def component_vulnerabilities(component_id:UUID,db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).component_vulnerabilities(component_id)

@router.get("/assessments",response_model=list[AssessmentRead])
def assessments(supplier_id:UUID|None=Query(None),db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).list_assessments(supplier_id)
@router.post("/assessments",response_model=AssessmentRead,status_code=status.HTTP_201_CREATED)
def create_assessment(p:AssessmentCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).create_assessment(p,user.id)
@router.get("/assessments/{entity_id}",response_model=AssessmentRead)
def assessment(entity_id:UUID,db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).get_assessment(entity_id)
@router.patch("/assessments/{entity_id}",response_model=AssessmentRead)
def update_assessment(entity_id:UUID,p:AssessmentUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_assessment(entity_id,p,user.id)
@router.put("/assessments/{entity_id}/responses",response_model=ResponseRead)
def response(entity_id:UUID,p:ResponseUpsert,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).upsert_response(entity_id,p,user.id)
@router.post("/assessments/{entity_id}/evidence",response_model=EvidenceLinkRead)
def evidence(entity_id:UUID,p:EvidenceLinkCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).link_evidence(entity_id,p,user.id)
@router.patch("/assessments/{entity_id}/evidence/{link_id}",response_model=EvidenceLinkRead)
def review_evidence(entity_id:UUID,link_id:UUID,p:EvidenceReview,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).review_evidence(entity_id,link_id,p,user.id)
@router.post("/assessments/{entity_id}/findings",response_model=FindingRead)
def finding(entity_id:UUID,p:FindingCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).add_finding(entity_id,p,user.id)
@router.patch("/assessments/{entity_id}/findings/{finding_id}",response_model=FindingRead)
def update_finding(entity_id:UUID,finding_id:UUID,p:FindingUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_finding(entity_id,finding_id,p,user.id)
@router.post("/assessments/{entity_id}/submit",response_model=AssessmentRead)
def submit(entity_id:UUID,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).submit(entity_id,user.id)
@router.post("/assessments/{entity_id}/decision",response_model=AssessmentRead)
def decide(entity_id:UUID,p:AssessmentDecision,db:Session=Depends(get_db),user:User=Depends(require_permissions_dependency(Permission.supplier_assessment_approve))): return SupplierAssessmentService(db).decide(entity_id,p,user.id)
@router.post("/sboms/{sbom_id}/match-components",response_model=SbomMatchRead)
def match_sbom(sbom_id:UUID,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).match_sbom(sbom_id,user.id)
@router.get("/maintainer-notifications",response_model=list[MaintainerNotificationRead])
def notifications(vulnerability_report_id:UUID|None=Query(None),db:Session=Depends(get_db),user:User=Depends(read_user())): return SupplierAssessmentService(db).list_notifications(vulnerability_report_id)
@router.post("/maintainer-notifications",response_model=MaintainerNotificationRead,status_code=status.HTTP_201_CREATED)
def create_notification(p:MaintainerNotificationCreate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).create_notification(p,user.id)
@router.patch("/maintainer-notifications/{entity_id}",response_model=MaintainerNotificationRead)
def update_notification(entity_id:UUID,p:MaintainerNotificationUpdate,db:Session=Depends(get_db),user:User=Depends(write_user())): return SupplierAssessmentService(db).update_notification(entity_id,p,user.id)
