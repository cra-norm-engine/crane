# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.annex_requirement import AnnexRequirement
from app.models.enums import AnnexPart
from app.repositories.base import BaseRepository


class AnnexRequirementRepository(BaseRepository[AnnexRequirement]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AnnexRequirement)

    def list_all(
        self,
        *,
        annex_part: AnnexPart | None = None,
        is_active: bool | None = None,
    ) -> list[AnnexRequirement]:
        stmt = select(AnnexRequirement).order_by(
            AnnexRequirement.annex_part.asc(),
            AnnexRequirement.code.asc(),
        )

        if annex_part is not None:
            stmt = stmt.where(AnnexRequirement.annex_part == annex_part)

        if is_active is not None:
            stmt = stmt.where(AnnexRequirement.is_active.is_(is_active))

        return list(self.db.scalars(stmt).all())

    def list_active(self) -> list[AnnexRequirement]:
        return self.list_all(is_active=True)

    def list_by_part(self, annex_part: AnnexPart) -> list[AnnexRequirement]:
        return self.list_all(annex_part=annex_part)

    def get_by_code(self, code: str) -> AnnexRequirement | None:
        stmt = select(AnnexRequirement).where(AnnexRequirement.code == code)
        return self.db.scalar(stmt)

    def get_or_404(self, annex_requirement_id) -> AnnexRequirement:
        annex_requirement = self.get_by_id(annex_requirement_id)
        if annex_requirement is None:
            raise NotFoundException("Annex requirement not found")
        return annex_requirement