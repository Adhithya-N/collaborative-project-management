"""Shared pytest fixtures - a dedicated test database, with each test isolated in its own transaction."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base, get_db
from app.main import app

# Separate database from the real dev one - tests should never touch real data.
TEST_DATABASE_URL = "postgresql+psycopg://collab_user:collab_password@localhost:5432/collab_test_db"

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Creates every table once before any test runs, drops them all once the whole session ends."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    """Wraps one test in a single DB transaction, rolled back afterward - tests never leak state to each other."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """A test client whose requests reuse the SAME transaction as the test itself.

    Without this override, the app would open its own separate DB connection/transaction and
    never see data the test set up (or vice versa).
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def register_and_login(client: TestClient, email: str, full_name: str = "Test User") -> dict[str, str]:
    """Helper (not a fixture) - creates a user and returns a ready-to-use Authorization header.

    Shared across test files by importing it, e.g. `from tests.conftest import register_and_login`.
    """
    client.post("/auth/register", json={"email": email, "password": "secret123", "full_name": full_name})
    response = client.post("/auth/login", json={"email": email, "password": "secret123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
