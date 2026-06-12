# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr

from app.schemas.common import ORMBaseModel, TimestampedRead


class UserCreate(ORMBaseModel):
    email: EmailStr
    full_name: str
    roles: list[str]


class UserRead(TimestampedRead):
    email: EmailStr
    full_name: str
    roles: list[str]
    is_active: bool


class UserSummaryRead(ORMBaseModel):
    id: UUID
    email: EmailStr
    full_name: str