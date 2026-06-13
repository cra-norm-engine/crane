# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
import secrets
from sqlalchemy.orm import Session
from sqlalchemy.exc import ProgrammingError

from app.core.annex_i_catalog import sync_annex_i_requirements
from app.core.config import settings
from app.core.permissions import Permission as PermissionEnum
from app.core.security import hash_password
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user import Role, User, UserRole

logger = logging.getLogger(__name__)

_DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}


def _resolve_initial_admin_password() -> str:
    """Choose the seeded admin password without shipping a known default to production (M-03).

    Priority:
      1. explicit ``BACKEND_ADMIN_PASSWORD`` (any environment);
      2. development builds fall back to the well-known ``admin1234`` for convenience;
      3. any other environment gets a random password, logged exactly once.

    The admin account is always created with ``must_change_password=True``.
    """
    if settings.admin_password:
        return settings.admin_password

    if settings.environment.lower() in _DEV_ENVIRONMENTS:
        logger.warning(
            "Seeding admin '%s' with the well-known development password 'admin1234'. "
            "Set BACKEND_ADMIN_PASSWORD (or run with a non-development BACKEND_ENVIRONMENT) "
            "to avoid shipping known default credentials.",
            settings.admin_email,
        )
        return "admin1234"

    generated = secrets.token_urlsafe(24)
    logger.warning(
        "No BACKEND_ADMIN_PASSWORD configured; generated a random initial password for "
        "admin '%s'. Sign in with it once and change it immediately:\n"
        "    initial admin password: %s",
        settings.admin_email,
        generated,
    )
    return generated


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

    admin_email = settings.admin_email
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if admin_user is None:
        admin_user = User(
            email=admin_email,
            full_name="Admin",
            hashed_password=hash_password(_resolve_initial_admin_password()),
            is_active=True,
            # Always force a password change on first login.
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
