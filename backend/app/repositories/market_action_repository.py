from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.market_action import MarketAction
from app.models.enums import MarketActionStatus, MarketActionType
from app.repositories.base import BaseRepository


class MarketActionRepository(BaseRepository[MarketAction]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MarketAction)

    def _default_options(self):
        return (selectinload(MarketAction.product_release),)

    def list_all(
        self,
        *,
        product_release_id: UUID | None = None,
        action_type: MarketActionType | None = None,
        status: MarketActionStatus | None = None,
    ) -> list[MarketAction]:
        stmt = (
            select(MarketAction)
            .options(*self._default_options())
            .order_by(MarketAction.created_at.desc())
        )
        if product_release_id is not None:
            stmt = stmt.where(MarketAction.product_release_id == product_release_id)
        if action_type is not None:
            stmt = stmt.where(MarketAction.action_type == action_type)
        if status is not None:
            stmt = stmt.where(MarketAction.status == status)
        return list(self.db.scalars(stmt).all())

    def get_or_404(self, action_id: UUID) -> MarketAction:
        stmt = (
            select(MarketAction)
            .options(*self._default_options())
            .where(MarketAction.id == action_id)
        )
        obj = self.db.scalar(stmt)
        if obj is None:
            raise NotFoundException("Market action not found")
        return obj
