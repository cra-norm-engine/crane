from types import SimpleNamespace
from uuid import uuid4

from app.models.enums import CvdPolicyStatus, ProductClassification
from app.models.product import Product
from app.repositories.cvd_policy_repository import CvdPolicyRepository
from app.schemas.cvd_policy import CvdPolicyCreate, CvdPolicyUpdate
from app.services.cvd_policy_service import CvdPolicyService


def _product(name: str) -> Product:
    return Product(
        product_code=f"CVD-{uuid4()}",
        name=name,
        description=name,
        manufacturer_name="Acme",
        intended_use="Test",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )


def test_cvd_policy_scopes_and_specific_precedence(db_session) -> None:
    first, second = _product("First"), _product("Second")
    db_session.add_all([first, second])
    db_session.flush()
    service = CvdPolicyService(db_session)
    actor = SimpleNamespace(id=None)

    organization = service.create_cvd_policy(
        CvdPolicyCreate(
            organization_wide=True,
            product_ids=[],
            status=CvdPolicyStatus.active,
            contact_email="security@example.com",
        ),
        actor,
    )
    group = service.create_cvd_policy(
        CvdPolicyCreate(
            organization_wide=False,
            product_ids=[first.id],
            status=CvdPolicyStatus.active,
            contact_email="product-security@example.com",
        ),
        actor,
    )

    repository = CvdPolicyRepository(db_session)
    assert {policy.id for policy in repository.list_all(product_id=first.id)} == {
        organization.id,
        group.id,
    }
    assert repository.get_effective_active(first.id).id == group.id
    assert repository.get_effective_active(second.id).id == organization.id

    service.update_cvd_policy(
        group.id,
        CvdPolicyUpdate(organization_wide=False, product_ids=[first.id, second.id]),
        actor,
    )
    assert repository.get_effective_active(second.id).id == group.id
