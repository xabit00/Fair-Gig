
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.auth import require_roles, verify_token
from app.main import app


MOCK_WORKER = {
    "sub": "11111111-2222-3333-4444-555555555555",
    "role": "worker",
}


@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[verify_token] = lambda: MOCK_WORKER

    # The earnings endpoints use require_roles("worker"),
    # so override those dependencies too.
    for route in app.routes:
        dependant = getattr(route, "dependant", None)
        if dependant is None:
            continue

        for dependency in dependant.dependencies:
            if (
                dependency.call is not None
                and dependency.call is not verify_token
            ):
                # Only override dependencies used for role checks.
                if getattr(dependency.call, "__name__", "") == "dependency":
                    app.dependency_overrides[dependency.call] = (
                        lambda: MOCK_WORKER
                    )

    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_db():
    valid_shift = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "worker_id": MOCK_WORKER["sub"],
        "platform": "Foodpanda",
        "date": "2026-10-11",
        "hours_worked": 6.5,
        "gross_earned": 4000.0,
        "deductions": 600.0,
        "net_received": 3400.0,
        "verification_status": "pending",
        "screenshot_url": None,
        "created_at": "2026-10-11T12:00:00Z",
    }

    summary = {
        "total_hours": 8.0,
        "total_gross": 5000.0,
        "total_deductions": 700.0,
        "total_net": 4300.0,
        "total_shifts": 1,
    }

    connection = MagicMock()

    def execute(query, params=None):
        result = MagicMock()
        normalized = " ".join(query.upper().split())

        missing = (
            params
            and str(params[0])
            == "00000000-0000-0000-0000-000000000000"
        )

        if "SUM(HOURS_WORKED)" in normalized:
            result.fetchone.return_value = summary

        elif missing and (
            "WHERE ID = %S" in normalized
            or "DELETE FROM SHIFTS" in normalized
        ):
            result.fetchone.return_value = None

        elif "SELECT * FROM SHIFTS WHERE WORKER_ID" in normalized:
            result.fetchall.return_value = [valid_shift]

        else:
            result.fetchone.return_value = valid_shift

        return result

    connection.execute.side_effect = execute

    @contextmanager
    def connection_context():
        yield connection

    with patch("app.main.get_connection", connection_context):
        yield connection


@pytest.fixture
def client():
    return TestClient(app)
