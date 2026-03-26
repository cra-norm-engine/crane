from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.product import RemoteProcessingElement
from app.repositories.base import BaseRepository


class RemoteProcessingElementRepository(BaseRepository[RemoteProcessingElement]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RemoteProcessingElement)

    def list_all(self, *, product_id: UUID | None = None) -> list[RemoteProcessingElement]:
        statement = select(RemoteProcessingElement).order_by(RemoteProcessingElement.created_at.desc())
        if product_id:
            statement = statement.where(RemoteProcessingElement.product_id == product_id)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, element_id: UUID) -> RemoteProcessingElement:
        element = self.get_by_id(element_id)
        if element is None:
            raise NotFoundException("Remote processing element not found")
        return element