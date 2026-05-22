from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.enums import ConformityRoute, ProductClassification, ReleaseStatus
from app.models.product import Product, ProductRelease


def test_product_code_must_be_unique(db_session) -> None:
    product_a = Product(
        product_code="PROD-001",
        name="Product A",
        description="A",
        manufacturer_name="Acme",
        intended_use="Test use",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    product_b = Product(
        product_code="PROD-001",
        name="Product B",
        description="B",
        manufacturer_name="Acme",
        intended_use="Test use",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )

    db_session.add(product_a)
    db_session.flush()

    db_session.add(product_b)
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_release_version_must_be_unique_per_product(db_session) -> None:
    product = Product(
        product_code=f"PROD-{uuid4()}",
        name="Product A",
        description="A",
        manufacturer_name="Acme",
        intended_use="Test use",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    db_session.add(product)
    db_session.flush()

    release_a = ProductRelease(
        product_id=product.id,
        system_version=1,
        user_version="1.0.0",
        release_status=ReleaseStatus.draft,
        classification_snapshot=ProductClassification.normal,
        conformity_route_snapshot=ConformityRoute.undecided,
    )
    release_b = ProductRelease(
        product_id=product.id,
        system_version=1,
        user_version="1.0.0",
        release_status=ReleaseStatus.draft,
        classification_snapshot=ProductClassification.normal,
        conformity_route_snapshot=ConformityRoute.undecided,
    )

    db_session.add(release_a)
    db_session.flush()

    db_session.add(release_b)
    with pytest.raises(IntegrityError):
        db_session.flush()