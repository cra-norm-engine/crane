# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import asyncio
from functools import partial
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.annex_matrix import (
    ProductRequirementDecisionUpdate,
    ProductRequirementMatrixRowRead,
    RequirementImplementationStatusUpdate,
)
from app.schemas.declaration import (
    DeclarationApproveRequest,
    DeclarationSignRequest,
    DeclarationSummaryRead,
    DeclarationUpdate,
)
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate
from app.schemas.requirement_assessment import RequirementAssessmentRead
from app.services.eu_declaration_service import EuDeclarationService
from app.services.package_label_service import PackageLabelService
from app.services.product_release_service import ProductReleaseService
from app.services.release_report_service import ReleaseReportService
from app.services.requirement_assessment_service import RequirementAssessmentService
from app.services.requirement_mapping_service import RequirementMappingService

router = APIRouter()


@router.get("/", response_model=list[ProductReleaseRead])
def list_product_releases(
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> list[ProductReleaseRead]:
    return ProductReleaseService(db).list_releases(product_id=product_id)


@router.get("/declarations", response_model=list[DeclarationSummaryRead])
def list_declarations(
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> list[DeclarationSummaryRead]:
    """List releases with their DoC status, for the top-level Declarations page.

    Declared before the ``/{release_id}`` routes so the literal path is not
    captured as a release UUID.
    """
    return EuDeclarationService(db).list_declarations(product_id=product_id)


@router.post("/", response_model=ProductReleaseRead, status_code=status.HTTP_201_CREATED)
def create_product_release(
    payload: ProductReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).create_release(payload, actor=current_user)


@router.get("/{release_id}", response_model=ProductReleaseRead)
def get_product_release(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).get_release(release_id)


@router.put("/{release_id}", response_model=ProductReleaseRead)
def update_product_release(
    release_id: UUID,
    payload: ProductReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).update_release(release_id, payload, actor=current_user)


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product_release(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> Response:
    ProductReleaseService(db).delete_release(release_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{release_id}/requirement-matrix", response_model=list[ProductRequirementMatrixRowRead])
def get_release_requirement_matrix(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> list[ProductRequirementMatrixRowRead]:
    return RequirementMappingService(db).release_matrix(release_id)


@router.get(
    "/{release_id}/requirement-matrix/{annex_requirement_id}",
    response_model=ProductRequirementMatrixRowRead,
)
def get_release_requirement_row(
    release_id: UUID,
    annex_requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> ProductRequirementMatrixRowRead:
    """Return a single matrix row so the client can refresh just the affected
    requirement after a trace-record mutation, instead of reloading the whole matrix."""
    return RequirementMappingService(db).release_requirement_row(release_id, annex_requirement_id)


@router.patch(
    "/{release_id}/requirement-matrix/{annex_requirement_id}/decision",
    response_model=ProductRequirementMatrixRowRead,
)
def update_release_requirement_decision(
    release_id: UUID,
    annex_requirement_id: UUID,
    payload: ProductRequirementDecisionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductRequirementMatrixRowRead:
    return RequirementMappingService(db).update_release_requirement_decision(
        release_id,
        annex_requirement_id,
        payload,
        actor_user_id=current_user.id,
    )


@router.patch(
    "/{release_id}/requirement-matrix/{annex_requirement_id}/status",
    response_model=ProductRequirementMatrixRowRead,
)
def update_release_requirement_status(
    release_id: UUID,
    annex_requirement_id: UUID,
    payload: RequirementImplementationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductRequirementMatrixRowRead:
    return RequirementMappingService(db).update_release_requirement_status(
        release_id,
        annex_requirement_id,
        payload.implementation_status,
        actor_user_id=current_user.id,
    )


@router.get(
    "/{release_id}/requirement-assessment",
    response_model=RequirementAssessmentRead,
)
def get_release_requirement_assessment(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> RequirementAssessmentRead:
    """Status of the release's Annex I requirement assessment (for the matrix banner)."""
    return RequirementAssessmentService(db).get_status(release_id)


@router.post(
    "/{release_id}/requirement-assessment/approve",
    response_model=RequirementAssessmentRead,
)
def approve_release_requirement_assessment(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> RequirementAssessmentRead:
    """Finalise (approve) the requirement assessment, locking it for the release."""
    return RequirementAssessmentService(db).approve(release_id, actor_user_id=current_user.id)


@router.post(
    "/{release_id}/requirement-assessment/reopen",
    response_model=RequirementAssessmentRead,
)
def reopen_release_requirement_assessment(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> RequirementAssessmentRead:
    """Reopen an approved assessment for amendment (returns it to draft)."""
    return RequirementAssessmentService(db).reopen(release_id, actor_user_id=current_user.id)


@router.get("/{release_id}/report", response_class=Response)
async def download_release_report(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> Response:
    """
    Generate and return a PDF compliance report for the given release.

    WeasyPrint is CPU-intensive so generation runs in a thread-pool executor
    to avoid blocking the event loop during rendering.
    """
    service = ReleaseReportService(db)
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, partial(service.generate_pdf, release_id, current_user.email)
    )
    filename = service.generate_filename(release_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{release_id}/report/data")
def get_release_report_data(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> dict:
    """
    Return the structured compliance-report data (all 17 sections) as JSON.

    Feeds the in-app HTML report view; the same builder backs the PDF export so
    both stay in sync.
    """
    return ReleaseReportService(db).build_report_data(release_id, generated_by=current_user.email)


# ----------------------------------------------------------------------
# EU Declaration of Conformity (CRA Art. 28 / Annex V)
# ----------------------------------------------------------------------


@router.get("/{release_id}/declaration/data")
def get_declaration_data(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> dict:
    """Return the structured EU DoC content (Annex V items) for the in-app preview."""
    return EuDeclarationService(db).build_declaration_data(release_id, generated_by=current_user.email)


@router.get("/{release_id}/declaration", response_class=Response)
async def download_declaration(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> Response:
    """Generate and return the EU Declaration of Conformity PDF for a release.

    WeasyPrint is CPU-intensive, so rendering runs in a thread-pool executor to
    avoid blocking the event loop.
    """
    service = EuDeclarationService(db)
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(
        None, partial(service.generate_pdf, release_id, current_user.email)
    )
    filename = service.generate_filename(release_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.patch("/{release_id}/declaration", response_model=ProductReleaseRead)
def update_declaration(
    release_id: UUID,
    payload: DeclarationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    """Update the editable DoC fields (Annex V). Allowed only while in draft."""
    return EuDeclarationService(db).update(release_id, payload.model_dump(exclude_unset=True))


@router.post("/{release_id}/declaration/submit", response_model=ProductReleaseRead)
def submit_declaration(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    """Return an approved DoC to draft so it can be edited again (signed DoCs are locked)."""
    return EuDeclarationService(db).submit(release_id)


@router.post("/{release_id}/declaration/approve", response_model=ProductReleaseRead)
def approve_declaration(
    release_id: UUID,
    payload: DeclarationApproveRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    """Approve a draft DoC and capture its signature (approver + signatory)."""
    signatory = payload.signatory if payload else None
    return EuDeclarationService(db).approve(
        release_id, approver=current_user.email, signatory=signatory
    )


@router.post("/{release_id}/declaration/sign", response_model=ProductReleaseRead)
def sign_declaration(
    release_id: UUID,
    payload: DeclarationSignRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    """Formally sign (draw up) an approved DoC. Locks it from further edits."""
    signatory = payload.signatory if payload else None
    return EuDeclarationService(db).sign(release_id, signatory=signatory or current_user.email)


# ----------------------------------------------------------------------
# Package label (CE marking + transparency info + DoC QR)
# ----------------------------------------------------------------------


@router.get("/{release_id}/label/data")
def get_label_data(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> dict:
    """Return the structured package-label content for the in-app preview."""
    return PackageLabelService(db).build_label_data(release_id)


@router.get("/{release_id}/label", response_class=Response)
async def download_label(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> Response:
    """Generate and return the printable package-label PDF for a release."""
    service = PackageLabelService(db)
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, partial(service.generate_pdf, release_id))
    filename = service.generate_filename(release_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )