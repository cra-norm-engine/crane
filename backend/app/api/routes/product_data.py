from __future__ import annotations

from json import JSONEncoder
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.product_data import (
    ProductDataBundle,
    ProductDataHistoryItem,
    ProductDataImportRead,
    ProductDataValidationRead,
)
from app.services.product_data_service import ProductDataService, _json_default, load_bundle

router = APIRouter()

Database = Annotated[Session, Depends(get_db)]
ExportUser = Annotated[User, Depends(require_permission(Permission.product_data_export))]
ImportUser = Annotated[User, Depends(require_permission(Permission.product_data_import))]
ImportFile = Annotated[UploadFile, File()]
ProductName = Annotated[str | None, Form(max_length=255)]
ProductCode = Annotated[str | None, Form(max_length=100)]
ReleaseIds = Annotated[list[UUID] | None, Query()]


@router.get("/schema")
def get_product_data_schema(
    current_user: ExportUser,
) -> dict:
    return ProductDataBundle.model_json_schema(by_alias=True)


@router.get("/history", response_model=list[ProductDataHistoryItem])
def get_product_data_history(
    db: Database,
    current_user: ExportUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ProductDataHistoryItem]:
    return ProductDataService(db).history(limit)


@router.post("/validate", response_model=ProductDataValidationRead)
def validate_product_data(
    file: ImportFile,
    db: Database,
    current_user: ImportUser,
    product_name: ProductName = None,
    product_code: ProductCode = None,
) -> ProductDataValidationRead:
    bundle, raw = load_bundle(file)
    result, _ = ProductDataService(db).validate(
        bundle, raw, actor_id=current_user.id, product_name=product_name, product_code=product_code
    )
    return result


@router.post("/import", response_model=ProductDataImportRead, status_code=201)
def import_product_data(
    file: ImportFile,
    db: Database,
    current_user: ImportUser,
    product_name: ProductName = None,
    product_code: ProductCode = None,
) -> ProductDataImportRead:
    bundle, raw = load_bundle(file)
    return ProductDataService(db).import_bundle(
        bundle, raw, actor_id=current_user.id, product_name=product_name, product_code=product_code
    )


@router.get("/products/{product_id}/export")
def export_product_data(
    product_id: UUID,
    db: Database,
    current_user: ExportUser,
    release_ids: ReleaseIds = None,
    redact_personal_data: bool = True,
    include_embargoed: bool = False,
    sensitivity: Literal["internal", "confidential", "restricted"] = "confidential",
) -> StreamingResponse:
    bundle, digest, filename = ProductDataService(db).export_bundle(
        product_id,
        actor_id=current_user.id,
        actor_email=current_user.email,
        release_ids=release_ids,
        redact_personal_data=redact_personal_data,
        include_embargoed=include_embargoed,
        sensitivity=sensitivity,
    )
    encoder = JSONEncoder(indent=2, default=_json_default)
    return StreamingResponse(
        (chunk.encode("utf-8") for chunk in encoder.iterencode(bundle)),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-CRANE-SHA256": digest,
        },
    )
