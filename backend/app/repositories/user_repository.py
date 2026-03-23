from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.user import Role, User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        return self.db.scalar(statement)

    def get_by_id(self, user_id: UUID | str) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.roles).selectinload(UserRole.role),
            )
        )
        return self.db.scalar(statement)

    def list_roles(self) -> list[Role]:
        statement = select(Role).order_by(Role.name.asc())
        return list(self.db.scalars(statement).all())