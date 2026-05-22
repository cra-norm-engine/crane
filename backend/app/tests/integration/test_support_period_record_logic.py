from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictException
from app.core.permissions import ROLE_PRODUCT_OWNER
from app.models.enums import ProductClassification, SupportType
from app.models.product import Product
from app.models.user import Role, User, UserRole
from app.schemas.support_period_record import SupportPeriodRecordCreate, SupportPeriodRecordUpdate
from app.services.support_period_record_service import SupportPeriodRecordService


class DummyActor:
    def __init__(self) -> None:
        self.id = uuid4()


def create_product(db_session) -> Product:
    product = Product(
        product_code=f"PROD-{uuid4()}",
        name="Lifecycle Product",
        description="Lifecycle managed product",
        manufacturer_name="Acme",
        intended_use="Lifecycle testing",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    db_session.add(product)
    db_session.flush()
    return product


def create_notification_recipient(db_session) -> User:
    role = db_session.query(Role).filter(Role.name == ROLE_PRODUCT_OWNER).first()
    if role is None:
        role = Role(name=ROLE_PRODUCT_OWNER, description="Product Owner")
        db_session.add(role)
        db_session.flush()

    user = User(
        email=f"owner-{uuid4()}@example.com",
        full_name="Support Recipient",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.flush()
    return user


def test_create_support_period_record(db_session) -> None:
    product = create_product(db_session)
    recipient = create_notification_recipient(db_session)
    actor = DummyActor()

    service = SupportPeriodRecordService(db_session)
    result = service.create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            notify_before_days=45,
            support_type=SupportType.standard,
            recipient_user_ids=[recipient.id],
            justification_text="Aligned with expected secure maintenance window.",
            expected_use_time_text="12 months",
            comparable_products_text="Comparable SME software tools support 12 months.",
            third_party_support_constraints_text="Upstream dependencies are supported for 12 months.",
            user_facing_summary="Support available through 2027-01-01.",
            packaging_summary="Support through 2027-01-01.",
        ),
        actor=actor,
    )

    assert result.product_id == product.id
    assert result.support_start_date == date(2026, 1, 1)
    assert result.support_end_date == date(2027, 1, 1)
    assert result.notify_before_days == 45
    assert result.support_type == SupportType.standard
    assert result.recipient_user_ids == [recipient.id]
    assert len(result.recipients) == 1
    assert result.is_active is True
    assert result.superseded_by_id is None


def test_only_one_active_support_period_record_per_product(db_session) -> None:
    product = create_product(db_session)
    recipient = create_notification_recipient(db_session)
    actor = DummyActor()
    service = SupportPeriodRecordService(db_session)

    service.create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            support_type=SupportType.standard,
            recipient_user_ids=[recipient.id],
            justification_text="Initial support policy.",
        ),
        actor=actor,
    )

    with pytest.raises(ConflictException):
        service.create_record(
            SupportPeriodRecordCreate(
                product_id=product.id,
                support_start_date=date(2026, 2, 1),
                support_end_date=date(2027, 2, 1),
                support_type=SupportType.extended,
                recipient_user_ids=[recipient.id],
                justification_text="Conflicting second active record.",
            ),
            actor=actor,
        )


def test_versioned_update_replaces_active_record_and_preserves_history(db_session) -> None:
    product = create_product(db_session)
    recipient = create_notification_recipient(db_session)
    actor = DummyActor()
    service = SupportPeriodRecordService(db_session)

    original = service.create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            support_type=SupportType.standard,
            recipient_user_ids=[recipient.id],
            justification_text="Initial rationale.",
            user_facing_summary="Initial user summary.",
            packaging_summary="Initial packaging summary.",
        ),
        actor=actor,
    )

    replacement = service.update_record_versioned(
        original.id,
        SupportPeriodRecordUpdate(
            support_end_date=date(2027, 6, 30),
            notify_before_days=30,
            support_type=SupportType.extended,
            justification_text="Extended based on customer lifecycle commitments.",
            user_facing_summary="Extended support available through 2027-06-30.",
        ),
        actor=actor,
    )

    history = service.get_history_for_product(product.id)

    assert replacement.id != original.id
    assert replacement.product_id == product.id
    assert replacement.is_active is True
    assert replacement.support_end_date == date(2027, 6, 30)
    assert replacement.notify_before_days == 30
    assert replacement.support_type == SupportType.extended
    assert len(history.records) == 2

    active_records = [record for record in history.records if record.is_active]
    inactive_records = [record for record in history.records if not record.is_active]

    assert len(active_records) == 1
    assert len(inactive_records) == 1
    assert active_records[0].id == replacement.id
    assert inactive_records[0].id == original.id
    assert inactive_records[0].superseded_by_id == replacement.id


def test_cannot_version_inactive_support_period_record(db_session) -> None:
    product = create_product(db_session)
    recipient = create_notification_recipient(db_session)
    actor = DummyActor()
    service = SupportPeriodRecordService(db_session)

    original = service.create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            support_type=SupportType.standard,
            recipient_user_ids=[recipient.id],
            justification_text="Initial rationale.",
        ),
        actor=actor,
    )

    service.update_record_versioned(
        original.id,
        SupportPeriodRecordUpdate(
            support_end_date=date(2027, 3, 1),
            justification_text="Superseding rationale.",
        ),
        actor=actor,
    )

    with pytest.raises(ConflictException):
        service.update_record_versioned(
            original.id,
            SupportPeriodRecordUpdate(
                support_end_date=date(2027, 5, 1),
            ),
            actor=actor,
        )


def test_multiple_version_updates_preserve_multiple_inactive_history_records(db_session) -> None:
    product = create_product(db_session)
    recipient = create_notification_recipient(db_session)
    actor = DummyActor()
    service = SupportPeriodRecordService(db_session)

    first = service.create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            support_type=SupportType.standard,
            recipient_user_ids=[recipient.id],
            justification_text="Initial lifecycle policy.",
        ),
        actor=actor,
    )

    second = service.update_record_versioned(
        first.id,
        SupportPeriodRecordUpdate(
            support_end_date=date(2027, 3, 1),
            justification_text="First extension.",
        ),
        actor=actor,
    )

    third = service.update_record_versioned(
        second.id,
        SupportPeriodRecordUpdate(
            support_end_date=date(2027, 6, 1),
            justification_text="Second extension.",
        ),
        actor=actor,
    )

    history = service.get_history_for_product(product.id)

    assert third.is_active is True
    assert len(history.records) == 3
    assert len([record for record in history.records if record.is_active]) == 1
    assert len([record for record in history.records if not record.is_active]) == 2


def test_generate_support_period_snippets(db_session) -> None:
    product = create_product(db_session)
    service = SupportPeriodRecordService(db_session)

    from app.schemas.support_period_record import SupportPeriodSnippetGenerateRequest

    snippets = service.generate_snippets(
        SupportPeriodSnippetGenerateRequest(
            product_id=product.id,
            support_start_date=date(2026, 1, 1),
            support_end_date=date(2027, 1, 1),
            support_type=SupportType.standard,
            justification_text="Support duration is based on expected product use.",
            expected_use_time_text="12 months",
            comparable_products_text="Comparable products provide 12 months of security support.",
            third_party_support_constraints_text="Critical dependencies are maintained for the same period.",
        )
    )

    assert "2026-01-01" in snippets.user_facing_summary
    assert "2027-01-01" in snippets.user_facing_summary
    assert "standard" in snippets.user_facing_summary
    assert "Security support period: 2026-01-01 to 2027-01-01" in snippets.packaging_summary
