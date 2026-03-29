from datetime import date
from uuid import uuid4

from app.models.enums import LifecycleNotificationStatus, ProductClassification, SupportType
from app.models.product import Product
from app.schemas.support_period_record import SupportPeriodRecordCreate
from app.services.lifecycle_notification_service import LifecycleNotificationService
from app.services.support_period_record_service import SupportPeriodRecordService


class DummyActor:
    def __init__(self) -> None:
        self.id = uuid4()


def create_product(db_session) -> Product:
    product = Product(
        product_code=f"PROD-{uuid4()}",
        name="Notification Product",
        description="EOS notification testing",
        manufacturer_name="Acme",
        intended_use="Notification lifecycle testing",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    db_session.add(product)
    db_session.flush()
    return product


def create_support_period(
    db_session,
    *,
    product: Product,
    support_start_date: date,
    support_end_date: date,
):
    actor = DummyActor()
    return SupportPeriodRecordService(db_session).create_record(
        SupportPeriodRecordCreate(
            product_id=product.id,
            support_start_date=support_start_date,
            support_end_date=support_end_date,
            support_type=SupportType.standard,
            justification_text="Lifecycle notification support period test.",
        ),
        actor=actor,
    )


def test_schedule_eos_notifications_for_records_within_6_months(db_session) -> None:
    actor = DummyActor()
    near_product = create_product(db_session)
    far_product = create_product(db_session)

    create_support_period(
        db_session,
        product=near_product,
        support_start_date=date(2026, 1, 1),
        support_end_date=date(2026, 8, 15),
    )
    create_support_period(
        db_session,
        product=far_product,
        support_start_date=date(2026, 1, 1),
        support_end_date=date(2027, 3, 1),
    )

    service = LifecycleNotificationService(db_session)
    notifications = service.schedule_end_of_support_notifications(
        actor=actor,
        today=date(2026, 3, 1),
    )

    assert len(notifications) == 1
    assert notifications[0].status == LifecycleNotificationStatus.pending
    assert "End of support approaching" == notifications[0].title
    assert str(near_product.id) in notifications[0].message


def test_schedule_eos_notifications_does_not_duplicate_existing_notification(db_session) -> None:
    actor = DummyActor()
    product = create_product(db_session)

    record = create_support_period(
        db_session,
        product=product,
        support_start_date=date(2026, 1, 1),
        support_end_date=date(2026, 8, 15),
    )

    service = LifecycleNotificationService(db_session)

    first_run = service.schedule_end_of_support_notifications(
        actor=actor,
        today=date(2026, 3, 1),
    )
    second_run = service.schedule_end_of_support_notifications(
        actor=actor,
        today=date(2026, 3, 1),
    )

    assert len(first_run) == 1
    assert len(second_run) == 0

    all_notifications = service.list_notifications(support_period_record_id=record.id)
    assert len(all_notifications) == 1


def test_mark_notification_sent_updates_status_and_support_record_timestamp(db_session) -> None:
    actor = DummyActor()
    product = create_product(db_session)

    record = create_support_period(
        db_session,
        product=product,
        support_start_date=date(2026, 1, 1),
        support_end_date=date(2026, 8, 15),
    )

    notification_service = LifecycleNotificationService(db_session)
    created = notification_service.schedule_end_of_support_notifications(
        actor=actor,
        today=date(2026, 3, 1),
    )
    assert len(created) == 1

    sent = notification_service.mark_notification_sent(created[0].id, actor=actor)

    assert sent.status == LifecycleNotificationStatus.sent
    assert sent.sent_at is not None

    refreshed_record = SupportPeriodRecordService(db_session).get_record(record.id)
    assert refreshed_record.eos_notification_sent_at is not None


def test_dismiss_notification_updates_status(db_session) -> None:
    actor = DummyActor()
    product = create_product(db_session)

    create_support_period(
        db_session,
        product=product,
        support_start_date=date(2026, 1, 1),
        support_end_date=date(2026, 8, 15),
    )

    notification_service = LifecycleNotificationService(db_session)
    created = notification_service.schedule_end_of_support_notifications(
        actor=actor,
        today=date(2026, 3, 1),
    )
    assert len(created) == 1

    dismissed = notification_service.dismiss_notification(created[0].id, actor=actor)

    assert dismissed.status == LifecycleNotificationStatus.dismissed
    assert dismissed.dismissed_at is not None