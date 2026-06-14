# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.role_permission import RolePermission
from app.models.user import Role, User, UserRole
from app.models.user_preference import UserPreference
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def _user_rbac_options(self):
        return (
            selectinload(User.roles)
            .selectinload(UserRole.role)
            .selectinload(Role.permissions)
            .selectinload(RolePermission.permission),
        )

    def get_by_email(self, email: str) -> User | None:
        statement = (
            select(User)
            .where(User.email == email)
            .options(*self._user_rbac_options())
        )
        return self.db.scalar(statement)

    def get_by_id(self, user_id: UUID | str) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(*self._user_rbac_options())
        )
        return self.db.scalar(statement)

    def list_users(self) -> list[User]:
        statement = (
            select(User)
            .options(*self._user_rbac_options())
            .order_by(User.email.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_active_users(self) -> list[User]:
        statement = (
            select(User)
            .where(User.is_active.is_(True))
            .options(*self._user_rbac_options())
            .order_by(User.full_name.asc(), User.email.asc())
        )
        return list(self.db.scalars(statement).all())

    def list_active_users_by_ids(self, user_ids: list[UUID]) -> list[User]:
        if not user_ids:
            return []

        statement = (
            select(User)
            .where(User.id.in_(user_ids), User.is_active.is_(True))
            .options(*self._user_rbac_options())
        )
        return list(self.db.scalars(statement).all())

    def create_user(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
        is_active: bool = True,
        auth_provider: str = "local",
        must_change_password: bool = False,
    ) -> User:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=is_active,
            auth_provider=auth_provider,
            must_change_password=must_change_password,
        )
        self.db.add(user)
        self.db.flush()
        return self.get_by_id(user.id) or user

    def set_user_roles(self, user_id: UUID, role_ids: list[UUID]) -> User:
        self.db.execute(delete(UserRole).where(UserRole.user_id == user_id))

        unique_role_ids: list[UUID] = []
        seen: set[UUID] = set()
        for role_id in role_ids:
            if role_id not in seen:
                unique_role_ids.append(role_id)
                seen.add(role_id)

        for role_id in unique_role_ids:
            self.db.add(UserRole(user_id=user_id, role_id=role_id))

        self.db.flush()
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    def set_password(
        self,
        user_id: UUID,
        hashed_password: str,
        must_change_password: bool = False,
    ) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        user.hashed_password = hashed_password
        user.must_change_password = must_change_password
        # Any password change invalidates all outstanding access/refresh tokens.
        user.token_version = (user.token_version or 0) + 1
        self.db.flush()
        refreshed = self.get_by_id(user_id)
        if refreshed is None:
            raise ValueError("User not found")
        return refreshed

    def bump_token_version(self, user_id: UUID) -> int:
        """Increment token_version, immediately invalidating the user's issued tokens."""
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        user.token_version = (user.token_version or 0) + 1
        self.db.flush()
        return user.token_version

    def update_full_name(self, user_id: UUID, full_name: str) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        user.full_name = full_name
        self.db.flush()
        refreshed = self.get_by_id(user_id)
        if refreshed is None:
            raise ValueError("User not found")
        return refreshed

    def get_preferences(self, user_id: UUID) -> UserPreference | None:
        return self.db.scalar(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )

    def upsert_preferences(self, user_id: UUID, **changes: str) -> UserPreference:
        """Create the user's preference row if absent, then apply the given fields."""
        preference = self.get_preferences(user_id)
        if preference is None:
            preference = UserPreference(user_id=user_id)
            self.db.add(preference)
        for field, value in changes.items():
            setattr(preference, field, value)
        self.db.flush()
        return preference

    def set_user_active(self, user_id: UUID, is_active: bool) -> User:
        user = self.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")

        user.is_active = is_active
        self.db.flush()
        refreshed_user = self.get_by_id(user_id)
        if refreshed_user is None:
            raise ValueError("User not found")
        return refreshed_user

    def list_roles(self) -> list[Role]:
        statement = (
            select(Role)
            .options(
                selectinload(Role.permissions).selectinload(RolePermission.permission),
            )
            .order_by(Role.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_role_by_id(self, role_id: UUID | str) -> Role | None:
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .options(
                selectinload(Role.permissions).selectinload(RolePermission.permission),
            )
        )
        return self.db.scalar(statement)
