"""
Integration test configuration for anomaly-service.

These tests require a real PostgreSQL database.
Set DATABASE_URL environment variable to point to a test database.
The test database should have the FairGig schema applied (see db/schema.sql).

Run with: pytest tests_integration/ -v
"""

import os
import pytest
from fastapi.testclient import TestClient
import jwt
from datetime import datetime, timedelta
from contextlib import contextmanager
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.main import app
from app.auth import SECRET_KEY, ALGORITHM


TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fairgig_test")
TEST_JWT_SECRET = os.getenv("JWT_SECRET_KEY", "test-secret-key-for-integration-tests-only")


def create_test_token(user_id: str, role: str = "worker") -> str:
    """Create a valid JWT token for testing."""
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm=ALGORITHM)


@pytest.fixture(scope="session")
def test_pool():
    """Create a connection pool for the test database."""
    pool = ConnectionPool(
        conninfo=TEST_DATABASE_URL,
        min_size=1,
        max_size=3,
        kwargs={"row_factory": dict_row},
        open=False,
    )
    pool.open()
    yield pool
    pool.close()


@pytest.fixture(scope="function")
def db_connection(test_pool):
    """Get a database connection for a test."""
    with test_pool.connection() as conn:
        yield conn


@pytest.fixture(scope="function")
def clean_db(db_connection):
    """Clean the database before each test."""
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM shifts")
        cur.execute("DELETE FROM users WHERE role IN ('worker', 'verifier', 'advocate')")
        db_connection.commit()


@pytest.fixture(scope="function")
def test_user(db_connection):
    """Create a test user and return their ID."""
    import uuid
    user_id = str(uuid.uuid4())
    with db_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (user_id, "Test Worker", f"test_{user_id}@example.com", "hash", "worker")
        )
        db_connection.commit()
    yield user_id
    # Cleanup
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db_connection.commit()


@pytest.fixture(scope="function")
def test_verifier(db_connection):
    """Create a test verifier user and return their ID."""
    import uuid
    user_id = str(uuid.uuid4())
    with db_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (user_id, "Test Verifier", f"verifier_{user_id}@example.com", "hash", "verifier")
        )
        db_connection.commit()
    yield user_id
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db_connection.commit()


@pytest.fixture(scope="function")
def test_advocate(db_connection):
    """Create a test advocate user and return their ID."""
    import uuid
    user_id = str(uuid.uuid4())
    with db_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, name, email, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
            (user_id, "Test Advocate", f"advocate_{user_id}@example.com", "hash", "advocate")
        )
        db_connection.commit()
    yield user_id
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        db_connection.commit()


@pytest.fixture(scope="function")
def worker_token(test_user):
    """Create a valid token for the test worker."""
    return create_test_token(test_user, "worker")


@pytest.fixture(scope="function")
def verifier_token(test_verifier):
    """Create a valid token for the test verifier."""
    return create_test_token(test_verifier, "verifier")


@pytest.fixture(scope="function")
def advocate_token(test_advocate):
    """Create a valid token for the test advocate."""
    return create_test_token(test_advocate, "advocate")


@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_headers(worker_token):
    """Create authorization headers for the test worker."""
    return {"Authorization": f"Bearer {worker_token}"}


@pytest.fixture(scope="function")
def verifier_auth_headers(verifier_token):
    """Create authorization headers for the test verifier."""
    return {"Authorization": f"Bearer {verifier_token}"}


@pytest.fixture(scope="function")
def advocate_auth_headers(advocate_token):
    """Create authorization headers for the test advocate."""
    return {"Authorization": f"Bearer {advocate_token}"}