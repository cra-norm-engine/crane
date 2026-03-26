from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import AnnexPart


class AnnexRequirement(UUIDTimestampMixin, Base):
    __tablename__ = "annex_requirements"

    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    annex_part: Mapped[AnnexPart] = mapped_column(nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    requirement_mappings: Mapped[list["RequirementMapping"]] = relationship(
        "RequirementMapping",
        back_populates="annex_requirement",
        passive_deletes=True,
        order_by="desc(RequirementMapping.created_at)",
    )