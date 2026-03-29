from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.support_period_record import SupportPeriodRecord
from app.repositories.product_repository import ProductRepository
from app.repositories.support_period_record_repository import SupportPeriodRecordRepository
from app.schemas.support_period_record import (
    SupportPeriodRecordCreate,
    SupportPeriodRecordHistoryRead,
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

    def list_records(
        self,
        *,
        product_id: UUID | None = None,
        active_only: bool = False,
    ) -> list[SupportPeriodRecordRead]:
        records = self.repository.list_all(product_id=product_id, active_only=active_only)
        return [SupportPeriodRecordRead.model_validate(record) for record in records]

    def get_record(self, record_id: UUID) -> SupportPeriodRecordRead:
        record = self.repository.get_or_404(record_id)
        return SupportPeriodRecordRead.model_validate(record)

    def get_active_record_for_product(self, product_id: UUID) -> SupportPeriodRecordRead:
        self.product_repository.get_or_404(product_id)
        record = self.repository.get_active_by_product_id(product_id)
        if record is None:
            raise NotFoundException("Active support period record not found for product")
        return SupportPeriodRecordRead.model_validate(record)

    def get_history_for_product(self, product_id: UUID) -> SupportPeriodRecordHistoryRead:
        self.product_repository.get_or_404(product_id)
        records = self.repository.list_current_or_historical_for_product(product_id)
        return SupportPeriodRecordHistoryRead(
            product_id=product_id,
            records=[SupportPeriodRecordRead.model_validate(record) for record in records],
        )

    def create_record(self, payload: SupportPeriodRecordCreate, actor: object) -> SupportPeriodRecordRead:
        self.product_repository.get_or_404(payload.product_id)

        active_record = self.repository.get_active_by_product_id(payload.product_id)
        if active_record is not None:
            raise ConflictException(
                "An active support period record already exists for this product. Use update/versioning instead."
            )

        record = SupportPeriodRecord(**payload.model_dump())

        try:
            self.repository.add(record)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type=AuditActionType.create,
                entity_type=EntityType.support_period_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(record.product_id),
                    "support_start_date": record.support_start_date.isoformat(),
                    "support_end_date": record.support_end_date.isoformat(),
                    "support_type": record.support_type.value,
                    "is_active": record.is_active,
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create support period record due to constraint conflict") from exc

        return SupportPeriodRecordRead.model_validate(record)

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
            return SupportPeriodRecordRead.model_validate(current_record)

        next_values = {
            "product_id": current_record.product_id,
            "support_start_date": current_record.support_start_date,
            "support_end_date": current_record.support_end_date,
            "support_type": current_record.support_type,
            "justification_text": current_record.justification_text,
            "expected_use_time_text": current_record.expected_use_time_text,
            "comparable_products_text": current_record.comparable_products_text,
            "third_party_support_constraints_text": current_record.third_party_support_constraints_text,
            "user_facing_summary": current_record.user_facing_summary,
            "packaging_summary": current_record.packaging_summary,
        }
        next_values.update(updates)

        if next_values["support_end_date"] < next_values["support_start_date"]:
            raise ConflictException("support_end_date must be on or after support_start_date")

        replacement_record = SupportPeriodRecord(**next_values)

        try:
            current_record.is_active = False
            self.db.flush()

            self.repository.add(replacement_record)
            current_record.superseded_by_id = replacement_record.id
            self.db.flush()

            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type=AuditActionType.update,
                entity_type=EntityType.support_period_record,
                entity_id=replacement_record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(replacement_record.product_id),
                    "supersedes_record_id": str(current_record.id),
                    "updated_fields": sorted(updates.keys()),
                    "support_start_date": replacement_record.support_start_date.isoformat(),
                    "support_end_date": replacement_record.support_end_date.isoformat(),
                    "support_type": replacement_record.support_type.value,
                },
            )
            self.db.commit()
            self.db.refresh(replacement_record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to version support period record due to constraint conflict") from exc

        return SupportPeriodRecordRead.model_validate(replacement_record)

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