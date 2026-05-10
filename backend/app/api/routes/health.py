from __future__ import annotations

from fastapi import APIRouter

from app.core.database import check_database_connection
from app.schemas.health import HealthRead

router = APIRouter()


@router.get("/health", response_model=HealthRead)
def health() -> HealthRead:
    database_ok = check_database_connection()
    return HealthRead(
        status="ok" if database_ok else "degraded",
        database=database_ok,
    )
