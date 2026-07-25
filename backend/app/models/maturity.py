from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin


class MaturityModelVersion(UUIDTimestampMixin, Base):
    __tablename__ = "maturity_model_versions"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    published_on: Mapped[date] = mapped_column(Date, nullable=False)
    attribution: Mapped[str] = mapped_column(Text, nullable=False)
    catalog_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)


class MaturityAssessment(UUIDTimestampMixin, Base):
    __tablename__ = "maturity_assessments"

    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("maturity_model_versions.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(Text, nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", index=True)
    assessor_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reviewer_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewer_justification: Mapped[str | None] = mapped_column(Text)
    reassessment_due_date: Mapped[date | None] = mapped_column(Date)
    # Frozen at creation so later catalog revisions cannot rewrite history.
    catalog_snapshot_json: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)

    model_version: Mapped[MaturityModelVersion] = relationship()
    responses: Mapped[list["MaturityResponse"]] = relationship(cascade="all, delete-orphan", order_by="MaturityResponse.question_code")
    actions: Mapped[list["MaturityImprovementAction"]] = relationship(cascade="all, delete-orphan")


class MaturityResponse(UUIDTimestampMixin, Base):
    __tablename__ = "maturity_responses"
    __table_args__ = (UniqueConstraint("assessment_id", "question_code", name="uq_maturity_response_question"),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("maturity_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_code: Mapped[str] = mapped_column(String(10), nullable=False)
    score: Mapped[int | None] = mapped_column(Integer)
    rationale: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(20))
    assessor_notes: Mapped[str | None] = mapped_column(Text)

    evidence_links: Mapped[list["MaturityEvidenceLink"]] = relationship(cascade="all, delete-orphan")


class MaturityEvidenceLink(UUIDTimestampMixin, Base):
    __tablename__ = "maturity_evidence_links"

    response_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("maturity_responses.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)


class MaturityImprovementAction(UUIDTimestampMixin, Base):
    __tablename__ = "maturity_improvement_actions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("maturity_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    question_code: Mapped[str | None] = mapped_column(String(10))
    domain_code: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    due_date: Mapped[date | None] = mapped_column(Date)
    comments: Mapped[str | None] = mapped_column(Text)
    completion_evidence: Mapped[str | None] = mapped_column(Text)
