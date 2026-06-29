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
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate
from app.schemas.requirement_assessment import RequirementAssessmentRead
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