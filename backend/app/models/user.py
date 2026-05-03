from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import AuthProvider
from app.models.role_permission import RolePermission


class Role(UUIDTimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    users: Mapped[List["UserRole"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    permissions: Mapped[List["RolePermission"]] = relationship(
        back_populates="role",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class User(UUIDTimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    auth_provider: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AuthProvider.local, index=True
    )
    # True for local users who have not yet changed their initial password.
    # Always False for LDAP users (they authenticate externally).
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    roles: Mapped[List["UserRole"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    owned_risk_assessments: Mapped[list["RiskAssessment"]] = relationship(
        "RiskAssessment",
        foreign_keys="RiskAssessment.owner_user_id",
        back_populates="owner_user",
        passive_deletes=True,
    )
    owned_risk_items: Mapped[list["RiskItem"]] = relationship(
        "RiskItem",
        foreign_keys="RiskItem.owner_user_id",
        back_populates="owner_user",
        passive_deletes=True,
    )
    uploaded_evidence_items: Mapped[list["EvidenceItem"]] = relationship(
        "EvidenceItem",
        foreign_keys="EvidenceItem.uploaded_by_user_id",
        back_populates="uploaded_by_user",
        passive_deletes=True,
    )
    support_period_notification_assignments: Mapped[list["SupportPeriodNotificationRecipient"]] = relationship(
        "SupportPeriodNotificationRecipient",
        back_populates="user",
        passive_deletes=True,
    )
    assigned_lifecycle_notifications: Mapped[list["LifecycleNotification"]] = relationship(
        "LifecycleNotification",
        foreign_keys="LifecycleNotification.recipient_user_id",
        back_populates="recipient_user",
        passive_deletes=True,
    )

    @property
    def role_names(self) -> list[str]:
        return [ur.role.name for ur in self.roles if ur.role]


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="roles")
    role: Mapped["Role"] = relationship(back_populates="users")
