from datetime import UTC, datetime
from uuid import uuid4

from app.models.enums import ConformityRoute, DistributionMechanism, ProductClassification, ReleaseStatus
from app.models.product import Product, ProductRelease
from app.schemas.security_update import SecurityUpdateCreate, SecurityUpdateUpdate
from app.services.security_update_service import SecurityUpdateService


class DummyActor:
    def __init__(self) -> None:
        self.id = uuid4()


def create_product_and_release(db_session) -> ProductRelease:
    product = Product(
        product_code=f"PROD-{uuid4()}",
        name="Security Update Product",
        description="Security update testing",
        manufacturer_name="Acme",
        intended_use="Security update lifecycle testing",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    db_session.add(product)
    db_session.flush()

    release = ProductRelease(
        product_id=product.id,
        version="1.0.0",
        release_status=ReleaseStatus.released,
        classification_snapshot=ProductClassification.normal,
        conformity_route_snapshot=ConformityRoute.undecided,
    )
    db_session.add(release)
    db_session.flush()
    return release


def test_create_security_update(db_session) -> None:
    release = create_product_and_release(db_session)
    actor = DummyActor()
    service = SecurityUpdateService(db_session)

    result = service.create_security_update(
        SecurityUpdateCreate(
            product_release_id=release.id,
            title="Security update 2026-001",
            description="Fixes multiple vulnerabilities.",
            cves_addressed_json=["CVE-2026-0001", "CVE-2026-0002"],
            affected_versions_json=["1.0.0"],
            distribution_mechanism=DistributionMechanism.vendor_download,
            available_until=datetime(2027, 1, 1, tzinfo=UTC),
            released_at=datetime(2026, 4, 1, tzinfo=UTC),
        ),
        actor=actor,
    )

    assert result.product_release_id == release.id
    assert result.title == "Security update 2026-001"
    assert result.cves_addressed_json == ["CVE-2026-0001", "CVE-2026-0002"]
    assert result.affected_versions_json == ["1.0.0"]
    assert result.distribution_mechanism == DistributionMechanism.vendor_download


def test_update_security_update(db_session) -> None:
    release = create_product_and_release(db_session)
    actor = DummyActor()
    service = SecurityUpdateService(db_session)

    created = service.create_security_update(
        SecurityUpdateCreate(
            product_release_id=release.id,
            title="Security update 2026-001",
            description="Fixes vulnerabilities.",
            cves_addressed_json=["CVE-2026-0001"],
            affected_versions_json=["1.0.0"],
            distribution_mechanism=DistributionMechanism.vendor_download,
        ),
        actor=actor,
    )

    updated = service.update_security_update(
        created.id,
        SecurityUpdateUpdate(
            title="Security update 2026-001 revised",
            description="Fixes vulnerabilities and improves retention metadata.",
            distribution_mechanism=DistributionMechanism.package_repository,
            affected_versions_json=["1.0.0", "1.0.1"],
        ),
        actor=actor,
    )

    assert updated.id == created.id
    assert updated.title == "Security update 2026-001 revised"
    assert updated.distribution_mechanism == DistributionMechanism.package_repository
    assert updated.affected_versions_json == ["1.0.0", "1.0.1"]


def test_delete_security_update(db_session) -> None:
    release = create_product_and_release(db_session)
    actor = DummyActor()
    service = SecurityUpdateService(db_session)

    created = service.create_security_update(
        SecurityUpdateCreate(
            product_release_id=release.id,
            title="Security update 2026-001",
            cves_addressed_json=[],
            affected_versions_json=["1.0.0"],
            distribution_mechanism=DistributionMechanism.vendor_download,
        ),
        actor=actor,
    )

    service.delete_security_update(created.id, actor=actor)
    remaining = service.list_security_updates(product_release_id=release.id)

    assert remaining == []