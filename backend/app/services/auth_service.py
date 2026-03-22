from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.core.security import create_access_token, verify_password
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenRead


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)

    def authenticate(self, payload: LoginRequest) -> TokenRead:
        user = self.user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise AppException("Invalid email or password", status_code=401)
        if not user.is_active:
            raise AppException("User account is inactive", status_code=403)

        token = create_access_token(str(user.id))
        return TokenRead(access_token=token)
