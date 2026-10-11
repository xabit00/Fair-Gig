"""
Integration tests for anomaly-service.

These tests require a real PostgreSQL database.
Set DATABASE_URL environment variable to point to a test database.
The test database should have the FairGig schema applied (see db/schema.sql).

Run with: pytest tests_integration/ -v
"""

from datetime import date
from fastapi.testclient import TestClient


def test_health_check_database_connected(client: TestClient, auth_headers: dict):
    """Health endpoint should verify database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "anomaly-service"
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_rules_endpoint_accessible(client: TestClient, auth_headers: dict):
    """Rules endpoint should be accessible to workers."""
    response = client.get("/rules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    rule_ids = {r["id"] for r in data["rules"]}
    assert "high_deduction" in rule_ids
    assert "monthly_income_drop" in rule_ids


def test_detect_me_requires_auth(client: TestClient):
    """Detect/me endpoint should require authentication."""
    response = client.get("/detect/me")
    assert response.status_code == 403  # HTTPBearer auto_error=True returns 403


def test_detect_me_worker_own_data(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """Worker can analyze their own earnings via /detect/me."""
    # Insert some earnings data directly into database
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 10), 8.0, 3000.0, 1800.0, 1200.0, "confirmed")  # High deduction
        )
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 2, 10), 8.0, 3000.0, 200.0, 2800.0, "confirmed")
        )
        db_connection.commit()

    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == test_user
    assert data["records_analysed"] == 3
    assert "anomalies" in data
    assert len(data["anomalies"]) >= 1


def test_detect_me_empty_history(client: TestClient, auth_headers: dict):
    """Worker with no earnings gets empty result."""
    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] == 0
    assert data["anomalies"] == []


def test_detect_me_date_filters(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """Date filters work on /detect/me."""
    # Insert earnings across different months
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 2, 1), 8.0, 3000.0, 200.0, 2800.0, "confirmed")
        )
        db_connection.commit()

    # Filter to January only
    response = client.get("/detect/me?start_date=2026-01-01&end_date=2026-01-31", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] == 1


def test_detect_worker_requires_verifier_or_advocate_role(client: TestClient, auth_headers: dict):
    """POST /detect requires verifier or advocate role."""
    import uuid
    response = client.post("/detect", json={"worker_id": str(uuid.uuid4()), "earnings": []}, headers=auth_headers)
    assert response.status_code == 403


def test_detect_worker_verifier_can_analyze(client: TestClient, verifier_auth_headers: dict, db_connection, test_user: str):
    """Verifier can analyze any worker's earnings."""
    # Insert earnings for test_user
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        db_connection.commit()

    response = client.post("/detect", json={"worker_id": test_user, "earnings": []}, headers=verifier_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == test_user


def test_detect_worker_advocate_can_analyze(client: TestClient, advocate_auth_headers: dict, db_connection, test_user: str):
    """Advocate can analyze any worker's earnings."""
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        db_connection.commit()

    response = client.post("/detect", json={"worker_id": test_user, "earnings": []}, headers=advocate_auth_headers)
    assert response.status_code == 200


def test_detect_worker_nonexistent_returns_404(client: TestClient, verifier_auth_headers: dict):
    """Analyzing non-existent worker returns 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.post("/detect", json={"worker_id": fake_id, "earnings": []}, headers=verifier_auth_headers)
    assert response.status_code == 404


def test_detect_worker_a_cannot_analyze_worker_b_via_me(client: TestClient, auth_headers: dict, db_connection, test_user: str, test_verifier: str):
    """Worker A's /detect/me only returns their own data, not Worker B's."""
    # Insert data for test_user
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        # Insert different data for test_verifier
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_verifier, "Uber", date(2026, 1, 1), 8.0, 5000.0, 100.0, 4900.0, "confirmed")
        )
        db_connection.commit()

    # Worker A calls /detect/me - should only see their own data
    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == test_user
    assert data["records_analysed"] == 1


def test_detect_response_no_unauthorized_data(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """Response should not expose other workers' financial data."""
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        db_connection.commit()

    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == test_user


def test_detect_response_structure(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """Response has correct structure."""
    with db_connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 1), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        db_connection.commit()

    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "worker_id" in data
    assert "analysis_period" in data
    assert "records_analysed" in data
    assert "anomalies" in data
    assert "summary" in data
    assert "start_date" in data["analysis_period"]
    assert "end_date" in data["analysis_period"]


def test_missing_jwt_rejected(client: TestClient):
    """Request without JWT should be rejected."""
    response = client.get("/detect/me")
    assert response.status_code == 403


def test_invalid_jwt_signature_rejected(client: TestClient):
    """Request with invalid JWT signature should be rejected."""
    import jwt
    from app.auth import SECRET_KEY, ALGORITHM
    wrong_token = jwt.encode({"sub": "test", "role": "worker"}, "wrong-secret", algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {wrong_token}"}
    response = client.get("/detect/me", headers=headers)
    assert response.status_code == 401


def test_expired_jwt_rejected(client: TestClient):
    """Request with expired JWT should be rejected."""
    import jwt
    from datetime import datetime, timedelta
    from app.auth import SECRET_KEY, ALGORITHM
    expired_token = jwt.encode(
        {"sub": "test", "role": "worker", "exp": datetime.utcnow() - timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/detect/me", headers=headers)
    assert response.status_code == 401


def test_malformed_jwt_rejected(client: TestClient):
    """Request with malformed JWT should be rejected."""
    headers = {"Authorization": "Bearer not.a.valid.jwt"}
    response = client.get("/detect/me", headers=headers)
    assert response.status_code == 401


def test_high_deduction_anomaly_detected(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """High deduction anomaly should be detected from real database data."""
    # Insert earnings with one high deduction
    with db_connection.cursor() as cur:
        # Normal deductions around 200
        for day in range(1, 10):
            cur.execute(
                """
                INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (test_user, "Careem", date(2026, 1, day), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
            )
        # High deduction day
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 10), 8.0, 3000.0, 1800.0, 1200.0, "confirmed")
        )
        db_connection.commit()

    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] == 10
    anomaly_types = {a["type"] for a in data["anomalies"]}
    assert "high_deduction" in anomaly_types


def test_monthly_income_drop_anomaly_detected(client: TestClient, auth_headers: dict, db_connection, test_user: str):
    """Monthly income drop anomaly should be detected from real database data."""
    # Insert earnings with significant month-on-month drop
    with db_connection.cursor() as cur:
        # January - high income
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 1, 15), 8.0, 5000.0, 500.0, 4500.0, "confirmed")
        )
        # February - low income (more than 20% drop)
        cur.execute(
            """
            INSERT INTO shifts (worker_id, platform, date, hours_worked, gross_earned, deductions, net_received, verification_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (test_user, "Careem", date(2026, 2, 15), 8.0, 2000.0, 200.0, 1800.0, "confirmed")
        )
        db_connection.commit()

    response = client.get("/detect/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] == 2
    anomaly_types = {a["type"] for a in data["anomalies"]}
    assert "monthly_income_drop" in anomaly_types