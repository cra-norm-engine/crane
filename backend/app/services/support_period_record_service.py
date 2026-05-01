from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import AuditStatus, EntityType
from app.models.support_period_record import (
    SupportPeriodNotificationRecipient,
    SupportPeriodRecord,
)
from app.repositories.product_repository import ProductRepository
from app.repositories.support_period_record_repository import SupportPeriodRecordRepository
from app.repositories.user_repository import UserRepository
from app.schemas.support_period_record import (
    SupportPeriodRecordCreate,
    SupportPeriodRecordHistoryRead,
    SupportPeriodNotificationRecipientOptionRead,
    SupportPeriodNotificationRecipientRead,
    SupportPeriodRecordRead,
    SupportPeriodRecordUpdate,
    SupportPeriodSnippetGenerateRequest,
    SupportPeriodSnippetRead,
)


class SupportPeriodRecordService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SupportPeriodRecordRepository(db)
        self.product_repository = ProductRepository(db)
        self.user_repository = UserRepository(db)

    def _serialize_record(self, record: SupportPeriodRecord) -> SupportPeriodRecordRead:
        recipients = [
            SupportPeriodNotificationRecipientRead(
                id=recipient.id,
                user_id=recipient.user_id,
                full_name=recipient.user.full_name,
                email=recipient.user.email,
            )
            for recipient in record.notification_recipients
            if recipient.user is not None
        ]

        payload = {
            "id": record.id,
            "product_id": record.product_id,
            # Gap 1 — include the release-level FK so callers can distinguish
            # product-level records (None) from per-version records.
            "product_release_id": record.product_release_id,
            "support_start_date": record.support_start_date,
            "support_end_date": record.support_end_date,
            "notify_before_days": record.notify_before_days,
            "support_type": record.support_type,
            "recipient_user_ids": [recipient.user_id for recipient in record.notification_recipients],
            "justification_text": record.justification_text,
            "expected_use_time_text": record.expected_use_time_text,
            "comparable_products_text": record.comparable_products_text,
            "third_party_support_constraints_text": record.third_party_support_constraints_text,
            "user_facing_summary": record.user_facing_summary,
            "packaging_summary": record.packaging_summary,
            "eos_notification_sent_at": record.eos_notification_sent_at,
            "is_active": record.is_active,
            "superseded_by_id": record.superseded_by_id,
            "recipients": recipients,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        return SupportPeriodRecordRead.model_validate(payload)

    def list_notification_recipient_options(self) -> list[SupportPeriodNotificationRecipientOptionRead]:
        users = self.user_repository.list_active_users()
        return [
            SupportPeriodNotificationRecipientOptionRead(
                id=user.id,
                email=user.email,
                full_name=user.full_name,
                roles=user.role_names,
            )
            for user in users
        ]

    def _validate_recipient_user_ids(self, recipient_user_ids: list[UUID]) -> list[UUID]:
        if not recipient_user_ids:
            return []

        unique_ids: list[UUID] = []
        seen: set[UUID] = set()
        for user_id in recipient_user_ids:
            if user_id not in seen:
                seen.add(user_id)
                unique_ids.append(user_id)

        users = self.user_repository.list_active_users_by_ids(unique_ids)
        users_by_id = {user.id: user for user in users}

        invalid_ids = [
            user_id
            for user_id in unique_ids
            if user_id not in users_by_id
        ]
        if invalid_ids:
            raise ConflictException("One or more selected notification recipients do not exist or are inactive")

        return unique_ids

    def list_records(
        self,
        *,
        product_id: UUID | None = None,
        active_only: bool = False,
    ) -> list[SupportPeriodRecordRead]:
        records = self.repository.list_all(product_id=product_id, active_only=active_only)
        return [self._serialize_record(record) for record in records]

    def get_record(self, record_id: UUID) -> SupportPeriodRecordRead:
        record = self.repository.get_or_404(record_id)
        return self._serialize_record(record)

    def get_active_record_for_product(self, product_id: UUID) -> SupportPeriodRecordRead:
        self.product_repository.get_or_404(product_id)
        record = self.repository.get_active_by_product_id(product_id)
        if record is None:
            raise NotFoundException("Active support period record not found for product")
        return self._serialize_record(record)

    def get_history_for_product(self, product_id: UUID) -> SupportPeriodRecordHistoryRead:
        self.product_repository.get_or_404(product_id)
        records = self.repository.list_current_or_historical_for_product(product_id)
        return SupportPeriodRecordHistoryRead(
            product_id=product_id,
            records=[self._serialize_record(record) for record in records],
        )

    def create_record(self, payload: SupportPeriodRecordCreate, actor: object) -> SupportPeriodRecordRead:
        self.product_repository.get_or_404(payload.product_id)

        active_record = self.repository.get_active_by_product_id(payload.product_id)
        if active_record is not None:
            raise ConflictException(
                "An active support period record already exists for this product. Use update/versioning instead."
            )

        recipient_user_ids = self._validate_recipient_user_ids(payload.recipient_user_ids)
        record_payload = payload.model_dump(exclude={"recipient_user_ids"})
        record = SupportPeriodRecord(**record_payload)
        record.notification_recipients = [
            SupportPeriodNotificationRecipient(user_id=user_id)
            for user_id in recipient_user_ids
        ]

        try:
            self.repository.add(record)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="support_period.set",
                entity_type=EntityType.support_period_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(record.product_id),
                    # Gap 1 — log whether this is a per-version or product-level record
                    "product_release_id": str(record.product_release_id) if record.product_release_id else None,
                    "support_start_date": record.support_start_date.isoformat(),
                    "support_end_date": record.support_end_date.isoformat(),
                    "notify_before_days": record.notify_before_days,
                    "support_type": record.support_type.value,
                    "recipient_user_ids": [str(user_id) for user_id in recipient_user_ids],
                    "is_active": record.is_active,
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create support period record due to constraint conflict") from exc

        record = self.repository.get_or_404(record.id)
        return self._serialize_record(record)

    def update_record_versioned(
        self,
        record_id: UUID,
        payload: SupportPeriodRecordUpdate,
        actor: object,
    ) -> SupportPeriodRecordRead:
        current_record = self.repository.get_or_404(record_id)

        if not current_record.is_active:
            raise ConflictException("Only the active support period record can be versioned")

        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return self._serialize_record(current_record)

        next_values = {
            "product_id": current_record.product_id,
            # Gap 1 — preserve the release-level link when versioning a per-version record
            "product_release_id": current_record.product_release_id,
            "support_start_date": current_record.support_start_date,
            "support_end_date": current_record.support_end_date,
            "notify_before_days": current_record.notify_before_days,
            "support_type": current_record.support_type,
            "justification_text": current_record.justification_text,
            "expected_use_time_text": current_record.expected_use_time_text,
            "comparable_products_text": current_record.comparable_products_text,
            "third_party_support_constraints_text": current_record.third_party_support_constraints_text,
            "user_facing_summary": current_record.user_facing_summary,
            "packaging_summary": current_record.packaging_summary,
        }
        next_values.update(updates)
        next_recipient_user_ids = updates.get(
            "recipient_user_ids",
            [recipient.user_id for recipient in current_record.notification_recipients],
        )
        next_recipient_user_ids = self._validate_recipient_user_ids(next_recipient_user_ids)

        if next_values["support_end_date"] < next_values["support_start_date"]:
            raise ConflictException("support_end_date must be on or after support_start_date")

        replacement_record = SupportPeriodRecord(
            **{key: value for key, value in next_values.items() if key != "recipient_user_ids"}
        )
        replacement_record.notification_recipients = [
            SupportPeriodNotificationRecipient(user_id=user_id)
            for user_id in next_recipient_user_ids
        ]

        try:
            current_record.is_active = False
            self.db.flush()

            self.repository.add(replacement_record)
            current_record.superseded_by_id = replacement_record.id
            self.db.flush()

            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="support_period.versioned",
                entity_type=EntityType.support_period_record,
                entity_id=replacement_record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(replacement_record.product_id),
                    "supersedes_record_id": str(current_record.id),
                    "updated_fields": sorted(updates.keys()),
                    "support_start_date": replacement_record.support_start_date.isoformat(),
                    "support_end_date": replacement_record.support_end_date.isoformat(),
                    "notify_before_days": replacement_record.notify_before_days,
                    "support_type": replacement_record.support_type.value,
                    "recipient_user_ids": [str(user_id) for user_id in next_recipient_user_ids],
                },
            )
            self.db.commit()
            self.db.refresh(replacement_record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to version support period record due to constraint conflict") from exc

        replacement_record = self.repository.get_or_404(replacement_record.id)
        return self._serialize_record(replacement_record)

    def generate_snippets(self, payload: SupportPeriodSnippetGenerateRequest) -> SupportPeriodSnippetRead:
        self.product_repository.get_or_404(payload.product_id)

        support_type_label = payload.support_type.value.replace("_", " ")
        start_date_text = payload.support_start_date.isoformat()
        end_date_text = payload.support_end_date.isoformat()

        rationale_parts = [payload.justification_text.strip()]
        if payload.expected_use_time_text:
            rationale_parts.append(f"Expected use time: {payload.expected_use_time_text.strip()}.")
        if payload.comparable_products_text:
            rationale_parts.append(f"Comparable products considered: {payload.comparable_products_text.strip()}.")
        if payload.third_party_support_constraints_text:
            rationale_parts.append(
                f"Third-party support constraints: {payload.third_party_support_constraints_text.strip()}."
            )

        rationale_text = " ".join(part for part in rationale_parts if part).strip()

        user_facing_summary = (
            f"Security support is provided from {start_date_text} until {end_date_text} "
            f"under a {support_type_label} support model. {rationale_text}"
        ).strip()

        packaging_summary = (
            f"Security support period: {start_date_text} to {end_date_text} "
            f"({support_type_label})."
        ).strip()

        return SupportPeriodSnippetRead(
            user_facing_summary=user_facing_summary,
            packaging_summary=packaging_summary,
        )
