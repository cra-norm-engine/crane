from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.sbom_record import SbomRecordCreate, SbomRecordRead, SbomRecordUpdate
from app.schemas.sbom_vulnerability_finding import SbomScanResult, SbomVulnerabilityFindingRead
from app.services.sbom_record_service import SbomRecordService
from app.services.sbom_vulnerability_scanner import SbomVulnerabilityScanner
from app.repositories.sbom_vulnerability_finding_repository import SbomVulnerabilityFindingRepository

router = APIRouter()


@router.get("/", response_model=list[SbomRecordRead])
def list_sbom_records(
    product_release_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[SbomRecordRead]:
    return SbomRecordService(db).list_sbom_records(
        product_release_id=product_release_id,
        product_id=product_id,
    )


@router.post("/", response_model=SbomRecordRead, status_code=status.HTTP_201_CREATED)
def create_sbom_record(
    payload: SbomRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    return SbomRecordService(db).create_sbom_record(payload, actor=current_user)


@router.get("/{sbom_id}", response_model=SbomRecordRead)
def get_sbom_record(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> SbomRecordRead:
    return SbomRecordService(db).get_sbom_record(sbom_id)


@router.put("/{sbom_id}", response_model=SbomRecordRead)
def update_sbom_record(
    sbom_id: UUID,
    payload: SbomRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    return SbomRecordService(db).update_sbom_record(sbom_id, payload, actor=current_user)


@router.post("/import-from-artifact", response_model=SbomRecordRead, status_code=status.HTTP_201_CREATED)
def import_sbom_from_artifact(
    product_release_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    """Create a SbomRecord from the SBOM artifact already attached to the release gate."""
    return SbomRecordService(db).import_from_artifact(product_release_id, actor=current_user)


@router.post("/upload", response_model=SbomRecordRead, status_code=status.HTTP_201_CREATED)
async def upload_sbom_record(
    product_release_id: UUID = Form(...),
    file: UploadFile = File(...),
    notes: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    """Upload a raw SBOM file, run sbom-tools analysis, and create a record."""
    content = (await file.read()).decode("utf-8", errors="replace")
    return SbomRecordService(db).upload_and_analyze(
        product_release_id=product_release_id,
        sbom_content=content,
        file_name=file.filename,
        notes=notes,
        actor=current_user,
    )


@router.post("/{sbom_id}/analyze", response_model=SbomRecordRead)
def reanalyze_sbom_record(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    """Re-run sbom-tools analysis on an existing record's stored content."""
    return SbomRecordService(db).reanalyze(sbom_id, actor=current_user)


@router.post("/{sbom_id}/scan-vulnerabilities", response_model=SbomScanResult)
def scan_sbom_vulnerabilities(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomScanResult:
    """
    Scan an SBOM's components against the OSV vulnerability database.

    Creates SbomVulnerabilityFinding records for each CVE match and
    auto-creates a VulnerabilityReport for each finding so it enters the
    exploitability assessment workflow (CRA Art. 13(2)).
    """
    result = SbomVulnerabilityScanner(db).scan(sbom_id, actor=current_user)
    return SbomScanResult(**result)


@router.get("/{sbom_id}/vulnerability-findings", response_model=list[SbomVulnerabilityFindingRead])
def list_sbom_vulnerability_findings(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[SbomVulnerabilityFindingRead]:
    """List all CVE findings discovered during vulnerability scans of this SBOM."""
    findings = SbomVulnerabilityFindingRepository(db).list_by_sbom(sbom_id)
    return [SbomVulnerabilityFindingRead.model_validate(f) for f in findings]


@router.delete("/{sbom_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_sbom_record(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> Response:
    SbomRecordService(db).delete_sbom_record(sbom_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
