# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.password_policy import StrongPassword
from app.schemas.common import ORMBaseModel


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: StrongPassword
    role_ids: list[UUID] = []


class AdminUserRoleUpdate(BaseModel):
    role_ids: list[UUID]


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserRead(ORMBaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    roles: list[str]
    is_active: bool
    auth_provider: str
    must_change_password: bool
