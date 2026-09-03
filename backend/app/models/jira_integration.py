from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDTimestampMixin


class JiraConnection(UUIDTimestampMixin, Base):
    __tablename__ = "jira_connections"
    __table_args__ = (UniqueConstraint("created_by_user_id", "cloud_id", name="uq_jira_connection_owner_cloud"),)

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cloud_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    site_url: Mapped[str] = mapped_column(String(500), nullable=False)
    site_name: Mapped[str] = mapped_column(String(255), nullable=False)
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    access_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str | None] = mapped_column(Text)
    project_key: Mapped[str | None] = mapped_column(String(50))
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False, default="Task")
    status_mapping_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    priority_mapping_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    forge_installation_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    last_error: Mapped[str | None] = mapped_column(Text)


class JiraUserMapping(UUIDTimestampMixin, Base):
    __tablename__ = "jira_user_mappings"
    __table_args__ = (
        UniqueConstraint("connection_id", "crane_user_id", name="uq_jira_user_crane"),
        UniqueConstraint("connection_id", "jira_account_id", name="uq_jira_user_account"),
    )

    connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    crane_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jira_account_id: Mapped[str] = mapped_column(String(255), nullable=False)
    jira_display_name: Mapped[str | None] = mapped_column(String(255))


class JiraTaskLink(UUIDTimestampMixin, Base):
    __tablename__ = "jira_task_links"
    __table_args__ = (
        UniqueConstraint("connection_id", "manual_task_id", name="uq_jira_link_task"),
        UniqueConstraint("connection_id", "issue_id", name="uq_jira_link_issue"),
    )

    connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    manual_task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("manual_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_id: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    issue_url: Mapped[str] = mapped_column(String(700), nullable=False)
    sync_status: Mapped[str] = mapped_column(String(30), nullable=False, default="synced", index=True)
    jira_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    last_payload_hash: Mapped[str | None] = mapped_column(String(64))


class JiraSyncEvent(UUIDTimestampMixin, Base):
    __tablename__ = "jira_sync_events"

    connection_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jira_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    manual_task_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("manual_tasks.id", ondelete="CASCADE"), index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
