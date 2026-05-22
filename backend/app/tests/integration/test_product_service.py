"""Integration tests for ProductService."""
import pytest
from sqlalchemy.orm import Session
from uuid import uuid4

from app.core.exceptions import NotFoundException, ConflictException
from app.models.enums import ProductClassification
from app.models.product import Product
from app.services.product_service import ProductService


@pytest.fixture
def product_service(db_session: Session) -> ProductService:
    return ProductService(db_session)


@pytest.fixture
def test_product(db_session: Session) -> Product:
    """Create a test product."""
    product = Product(
        product_code="TEST-001",
        name="Test Product",
        description="A test product",
        manufacturer_name="Test Manufacturer",
        intended_use="Testing purposes",
        product_type="software",
        current_classification=ProductClassification.normal,
        scope_status="undecided",
    )
    db_session.add(product)
    db_session.commit()
    return product


class TestProductServiceCreate:
    """Test product creation."""

    def test_create_product_with_valid_data(self, product_service, db_session):
        """Product can be created with valid data."""
        from app.schemas.product import ProductCreate

        product_data = ProductCreate(
            product_code="UNIQUE-CODE-001",
            name="New Product",
            description="A new product",
            manufacturer_name="Manufacturer",
            intended_use="Production use",
            product_type="firmware",
            current_classification=ProductClassification.normal,
            scope_status="undecided",
        )

        product = product_service.create_product(product_data)

        assert product.id is not None
        assert product.product_code == "UNIQUE-CODE-001"
        assert product.name == "New Product"

    def test_create_product_with_duplicate_code_fails(self, product_service, test_product):
        """Creating product with duplicate code raises ConflictException."""
        from app.schemas.product import ProductCreate

        product_data = ProductCreate(
            product_code="TEST-001",  # Duplicate code
            name="Another Product",
            description="Different product",
            manufacturer_name="Manufacturer",
            intended_use="Testing",
            product_type="software",
            current_classification=ProductClassification.normal,
            scope_status="undecided",
        )

        with pytest.raises(ConflictException):
            product_service.create_product(product_data)

    def test_create_product_stores_in_database(self, product_service, db_session):
        """Created product is persisted to database."""
        from app.schemas.product import ProductCreate

        product_data = ProductCreate(
            product_code="PERSIST-001",
            name="Persistent Product",
            description="Stored in DB",
            manufacturer_name="Manufacturer",
            intended_use="Testing",
            product_type="software",
            current_classification=ProductClassification.normal,
            scope_status="undecided",
        )

        product = product_service.create_product(product_data)

        # Verify it's in database
        retrieved = db_session.query(Product).filter_by(id=product.id).first()
        assert retrieved is not None
        assert retrieved.product_code == "PERSIST-001"


class TestProductServiceRead:
    """Test product retrieval."""

    def test_get_product_by_id(self, product_service, test_product):
        """Product can be retrieved by ID."""
        product = product_service.get_product(test_product.id)

        assert product.id == test_product.id
        assert product.product_code == "TEST-001"

    def test_get_nonexistent_product_raises_not_found(self, product_service):
        """Getting nonexistent product raises NotFoundException."""
        nonexistent_id = uuid4()

        with pytest.raises(NotFoundException):
            product_service.get_product(nonexistent_id)

    def test_list_products(self, product_service, test_product, db_session):
        """Products can be listed."""
        # Create another product
        product2 = Product(
            product_code="TEST-002",
            name="Second Product",
            description="Another test",
            manufacturer_name="Manufacturer",
            intended_use="Testing",
            product_type="hardware",
            current_classification=ProductClassification.critical,
            scope_status="in_scope",
        )
        db_session.add(product2)
        db_session.commit()

        products = product_service.list_products()

        assert len(products) >= 2
        assert any(p.product_code == "TEST-001" for p in products)
        assert any(p.product_code == "TEST-002" for p in products)

    def test_list_products_with_pagination(self, product_service):
        """Products list supports pagination."""
        products = product_service.list_products(skip=0, limit=10)

        assert isinstance(products, list)
        assert len(products) <= 10


class TestProductServiceUpdate:
    """Test product updates."""

    def test_update_product_name(self, product_service, test_product, db_session):
        """Product name can be updated."""
        from app.schemas.product import ProductUpdate

        update_data = ProductUpdate(name="Updated Name")

        updated = product_service.update_product(test_product.id, update_data)

        assert updated.name == "Updated Name"
        assert updated.product_code == "TEST-001"  # Unchanged

    def test_update_product_classification(self, product_service, test_product):
        """Product classification can be updated."""
        from app.schemas.product import ProductUpdate

        update_data = ProductUpdate(
            current_classification=ProductClassification.critical
        )

        updated = product_service.update_product(test_product.id, update_data)

        assert updated.current_classification == ProductClassification.critical

    def test_update_nonexistent_product_raises_not_found(self, product_service):
        """Updating nonexistent product raises NotFoundException."""
        from app.schemas.product import ProductUpdate

        nonexistent_id = uuid4()
        update_data = ProductUpdate(name="New Name")

        with pytest.raises(NotFoundException):
            product_service.update_product(nonexistent_id, update_data)

    def test_update_preserves_other_fields(self, product_service, test_product, db_session):
        """Updating one field preserves others."""
        original_code = test_product.product_code
        original_manufacturer = test_product.manufacturer_name

        from app.schemas.product import ProductUpdate
        update_data = ProductUpdate(name="New Name")

        updated = product_service.update_product(test_product.id, update_data)

        assert updated.product_code == original_code
        assert updated.manufacturer_name == original_manufacturer
        assert updated.name == "New Name"


class TestProductServiceDelete:
    """Test product deletion."""

    def test_delete_product(self, product_service, test_product, db_session):
        """Product can be deleted."""
        product_id = test_product.id

        product_service.delete_product(product_id)

        # Verify it's deleted
        retrieved = db_session.query(Product).filter_by(id=product_id).first()
        assert retrieved is None

    def test_delete_nonexistent_product_raises_not_found(self, product_service):
        """Deleting nonexistent product raises NotFoundException."""
        nonexistent_id = uuid4()

        with pytest.raises(NotFoundException):
            product_service.delete_product(nonexistent_id)


class TestProductServiceValidation:
    """Test product data validation."""

    def test_product_code_is_required(self, product_service):
        """Product code is required."""
        from app.schemas.product import ProductCreate

        with pytest.raises((ValueError, TypeError)):
            product_data = ProductCreate(
                product_code=None,  # type: ignore
                name="Name",
                description="Desc",
                manufacturer_name="Mfg",
                intended_use="Use",
                product_type="software",
                current_classification=ProductClassification.normal,
                scope_status="undecided",
            )

    def test_product_type_is_required(self, product_service):
        """Product type is required."""
        from app.schemas.product import ProductCreate

        with pytest.raises((ValueError, TypeError)):
            product_data = ProductCreate(
                product_code="CODE",
                name="Name",
                description="Desc",
                manufacturer_name="Mfg",
                intended_use="Use",
                product_type=None,  # type: ignore
                current_classification=ProductClassification.normal,
                scope_status="undecided",
            )


class TestProductServiceHierarchy:
    """Test product hierarchy (parent/child products)."""

    def test_product_can_have_parent(self, product_service, test_product, db_session):
        """Product can be assigned a parent product."""
        from app.schemas.product import ProductCreate

        child_data = ProductCreate(
            product_code="CHILD-001",
            name="Child Product",
            description="A child product",
            manufacturer_name="Manufacturer",
            intended_use="Testing",
            product_type="software",
            current_classification=ProductClassification.normal,
            scope_status="undecided",
        )

        # Create child with parent
        child = product_service.create_product(child_data, parent_product_id=test_product.id)

        assert child.parent_product_id == test_product.id

    def test_product_hierarchy_is_preserved(self, product_service, test_product, db_session):
        """Parent-child hierarchy is maintained."""
        from app.schemas.product import ProductCreate

        child_data = ProductCreate(
            product_code="CHILD-002",
            name="Second Child",
            description="Another child",
            manufacturer_name="Manufacturer",
            intended_use="Testing",
            product_type="hardware",
            current_classification=ProductClassification.normal,
            scope_status="undecided",
        )

        child = product_service.create_product(child_data, parent_product_id=test_product.id)

        # Retrieve parent and check children
        parent = product_service.get_product(test_product.id)
        assert len(parent.child_products) > 0
        assert any(c.id == child.id for c in parent.child_products)
