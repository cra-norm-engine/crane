"""Shared test fixtures for backend tests."""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.models.base import Base

# Use PostgreSQL for testing (JSONB type is Postgres-specific).
# CI pipeline sets BACKEND_DATABASE_URL as env var for CI Postgres container.
# Local fallback: connect to localhost Postgres (assumes 'cra_test' db exists).
import os

TEST_DATABASE_URL = os.environ.get(
    "BACKEND_DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/cra_test"
)


@pytest.fixture(scope="session")
def engine():
    """Create test database engine once per session."""
    eng = create_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    # Note: drop_all skipped to avoid circular dependency issues with FK constraints.
    # The test database is fresh for each test run via explicit rollback in db_session.


@pytest.fixture(scope="function")
def db_session(engine):
    """Session: each test gets a fresh connection with explicit rollback.

    Using SAVEPOINT for transaction isolation without full reconnect overhead.
    """
    connection = engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection, expire_on_commit=False)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """FastAPI TestClient with database dependency overridden to use test session."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
