# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import AnnexPart

if TYPE_CHECKING:
    from app.models.requirement_mapping import RequirementMapping


class RequirementSource(UUIDTimestampMixin, Base):
    __tablename__ = "requirement_sources"
    __table_args__ = (UniqueConstraint("identifier", "edition", name="uq_requirement_source_edition"),)

    identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    edition: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    license_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    organization_wide: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_system_managed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    requirements: Mapped[list["AnnexRequirement"]] = relationship("AnnexRequirement", back_populates="source", order_by="AnnexRequirement.code")
    product_links: Mapped[list["RequirementSourceProduct"]] = relationship("RequirementSourceProduct", back_populates="source", cascade="all, delete-orphan")

    @property
    def product_ids(self) -> list[uuid.UUID]:
        return [link.product_id for link in self.product_links]

    @property
    def requirement_count(self) -> int:
        return len(self.requirements)


class RequirementSourceProduct(UUIDTimestampMixin, Base):
    __tablename__ = "requirement_source_products"
    __table_args__ = (UniqueConstraint("source_id", "product_id", name="uq_requirement_source_product"),)

    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requirement_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped["RequirementSource"] = relationship("RequirementSource", back_populates="product_links")


class ReleaseRequirementBaseline(UUIDTimestampMixin, Base):
    __tablename__ = "release_requirement_baselines"
    __table_args__ = (UniqueConstraint("product_release_id", "requirement_id", name="uq_release_requirement_baseline"),)

    product_release_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_releases.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("annex_requirements.id", ondelete="RESTRICT"), nullable=False, index=True)
    requirement_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    requirement_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class RequirementContribution(UUIDTimestampMixin, Base):
    __tablename__ = "requirement_contributions"
    __table_args__ = (UniqueConstraint("technical_requirement_id", "essential_requirement_id", name="uq_requirement_contribution"),)

    technical_requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("annex_requirements.id", ondelete="CASCADE"), nullable=False, index=True)
    essential_requirement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("annex_requirements.id", ondelete="RESTRICT"), nullable=False, index=True)
    contribution: Mapped[str] = mapped_column(Text, nullable=False)


class AnnexRequirement(UUIDTimestampMixin, Base):
    __tablename__ = "annex_requirements"
    __table_args__ = (UniqueConstraint("source_id", "code", name="uq_requirement_source_code"),)

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    annex_part: Mapped[AnnexPart] = mapped_column(nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, index=True)

    source_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("requirement_sources.id", ondelete="RESTRICT"), nullable=True, index=True)
    clause_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    applicability_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published", index=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    acceptance_criteria: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributions: Mapped[list["RequirementContribution"]] = relationship(
        foreign_keys="RequirementContribution.technical_requirement_id",
        cascade="all, delete-orphan", lazy="selectin",
    )

    source: Mapped["RequirementSource | None"] = relationship("RequirementSource", back_populates="requirements")

    @property
    def source_identifier(self) -> str:
        return self.source.identifier if self.source else "CRA-ANNEX-I"

    @property
    def source_title(self) -> str:
        return self.source.title if self.source else "CRA Annex I essential requirements"

    @property
    def source_edition(self) -> str:
        return self.source.edition if self.source else ""

    @property
    def kind(self) -> str:
        return "essential" if self.source is None or self.source.is_system_managed else "technical"

    requirement_mappings: Mapped[list["RequirementMapping"]] = relationship(
        "RequirementMapping",
        back_populates="annex_requirement",
        passive_deletes=True,
        order_by="desc(RequirementMapping.created_at)",
    )
