from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import LoginRequest, TokenRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenRead, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenRead:
    return AuthService(db).authenticate(payload)