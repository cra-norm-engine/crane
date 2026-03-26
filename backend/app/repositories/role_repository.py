from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import Role
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Role)

    def _role_options(self):
        return (
            selectinload(Role.permissions).selectinload(RolePermission.permission),
        )

    def list_roles(self) -> list[Role]:
        statement = (
            select(Role)
            .options(*self._role_options())
            .order_by(Role.name.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_by_id(self, role_id: UUID | str) -> Role | None:
        statement = (
            select(Role)
            .where(Role.id == role_id)
            .options(*self._role_options())
        )
        return self.db.scalar(statement)

    def get_by_name(self, name: str) -> Role | None:
        statement = (
            select(Role)
            .where(Role.name == name)
            .options(*self._role_options())
        )
        return self.db.scalar(statement)

    def create_role(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Role:
        role = Role(
            name=name,
            description=description,
        )
        self.db.add(role)
        self.db.flush()
        refreshed = self.get_by_id(role.id)
        return refreshed or role

    def update_role(
        self,
        *,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        role = self.get_by_id(role_id)
        if role is None:
            raise ValueError("Role not found")

        if name is not None:
            role.name = name
        if description is not None:
            role.description = description

        self.db.flush()
        refreshed = self.get_by_id(role_id)
        return refreshed or role

    def delete_role(self, role_id: UUID) -> None:
        role = self.get_by_id(role_id)
        if role is None:
            raise ValueError("Role not found")

        self.db.delete(role)
        self.db.flush()

    def list_permissions(self) -> list[Permission]:
        statement = select(Permission).order_by(Permission.key.asc())
        return list(self.db.scalars(statement).all())

    def get_permission_by_id(self, permission_id: UUID | str) -> Permission | None:
        statement = select(Permission).where(Permission.id == permission_id)
        return self.db.scalar(statement)

    def set_role_permissions(self, role_id: UUID, permission_ids: list[UUID]) -> Role:
        role = self.get_by_id(role_id)
        if role is None:
            raise ValueError("Role not found")

        self.db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))

        unique_permission_ids: list[UUID] = []
        seen: set[UUID] = set()
        for permission_id in permission_ids:
            if permission_id not in seen:
                unique_permission_ids.append(permission_id)
                seen.add(permission_id)

        for permission_id in unique_permission_ids:
            self.db.add(RolePermission(role_id=role_id, permission_id=permission_id))

        self.db.flush()
        refreshed = self.get_by_id(role_id)
        if refreshed is None:
            raise ValueError("Role not found")
        return refreshed