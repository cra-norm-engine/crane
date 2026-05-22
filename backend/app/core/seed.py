from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from app.core.annex_i_catalog import sync_annex_i_requirements
from app.core.permissions import Permission as PermissionEnum
from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import Role, User, UserRole

logger = logging.getLogger(__name__)


def seed_initial_data(db: Session) -> None:
    try:
        existing_permissions = {permission.key for permission in db.query(Permission).all()}
    except (ProgrammingError, Exception) as e:
        logger.warning(f"Database not ready for seeding: {e}. Skipping seed_initial_data.")
        return
    for perm in PermissionEnum:
        if perm.value not in existing_permissions:
            db.add(Permission(key=perm.value, description=perm.value))
    db.commit()

    default_roles = [
        "admin",
        "product_owner",
        "cybersecurity_engineer",
        "development_team",
        "legal_team",
        "lifecycle_manager",
        "product_management",
    ]

    existing_roles = {role.name for role in db.query(Role).all()}
    for role_name in default_roles:
        if role_name not in existing_roles:
            db.add(Role(name=role_name, description=role_name.replace("_", " ").title()))
    db.commit()

    admin_role = db.query(Role).filter(Role.name == "admin").first()
    all_permissions = db.query(Permission).all()

    if admin_role is not None:
        existing_role_permission_ids = {
            rp.permission_id
            for rp in db.query(RolePermission).filter(RolePermission.role_id == admin_role.id).all()
        }

        for permission in all_permissions:
            if permission.id not in existing_role_permission_ids:
                db.add(RolePermission(role_id=admin_role.id, permission_id=permission.id))
        db.commit()

    admin_user = db.query(User).filter(User.email == "admin@example.com").first()
    if admin_user is None:
        admin_user = User(
            email="admin@example.com",
            full_name="Admin",
            hashed_password=hash_password("admin1234"),
            is_active=True,
            # Force password change on first login — default password is known.
            must_change_password=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

    if admin_role is not None:
        existing_user_role = (
            db.query(UserRole)
            .filter(UserRole.user_id == admin_user.id, UserRole.role_id == admin_role.id)
            .first()
        )
        if existing_user_role is None:
            db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
            db.commit()

    sync_annex_i_requirements(db)
    db.commit()
