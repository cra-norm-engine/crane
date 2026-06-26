# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundException
from app.models.product import RemoteProcessingElement
from app.repositories.base import BaseRepository


class RemoteProcessingElementRepository(BaseRepository[RemoteProcessingElement]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RemoteProcessingElement)

    def list_all(self, *, product_id: UUID | None = None) -> list[RemoteProcessingElement]:
        statement = (
            select(RemoteProcessingElement)
            # Eager-load the assessor so the Read schema can surface their name without an N+1 query.
            .options(joinedload(RemoteProcessingElement.assessed_by))
            .order_by(RemoteProcessingElement.created_at.desc())
        )
        if product_id:
            statement = statement.where(RemoteProcessingElement.product_id == product_id)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, element_id: UUID) -> RemoteProcessingElement:
        statement = (
            select(RemoteProcessingElement)
            .options(joinedload(RemoteProcessingElement.assessed_by))
            .where(RemoteProcessingElement.id == element_id)
        )
        element = self.db.scalars(statement).first()
        if element is None:
            raise NotFoundException("Remote processing element not found")
        return element