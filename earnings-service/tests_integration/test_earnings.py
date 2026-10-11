"""
Integration tests for earnings-service.

These tests require a real PostgreSQL database.
Set DATABASE_URL environment variable to point to a test database.
The test database should have the FairGig schema applied (see db/schema.sql).

Run with: pytest tests_integration/ -v
"""

from datetime import UTC

from fastapi.testclient import TestClient


def test_health_check_database_connected(client: TestClient, auth_headers: dict):
    """Health endpoint should verify database connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "earnings-service"
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_create_shift_success(client: TestClient, auth_headers: dict):
    """Creating a shift should persist it to the database."""
    payload = {
        "platform": "Foodpanda",
        "work_date": "2026-10-11",
        "start_time": "09:00:00",
        "end_time": "17:00:00",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 400.0,
        "net_received": 4400.0,
        "status": "pending"
    }

    response = client.post("/shifts", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["platform"] == "Foodpanda"
    assert data["gross_earned"] == 5000.0
    assert data["net_received"] == 4400.0
    assert "shift_id" in data
    assert data["worker_id"] is not None


def test_create_shift_net_exceeds_gross_rejected(client: TestClient, auth_headers: dict):
    """Creating a shift with net > gross should be rejected by database constraint."""
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-12",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 500.0,
        "net_received": 6000.0,  # Exceeds gross
        "status": "pending"
    }

    response = client.post("/shifts", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]


def test_create_shift_duplicate_worker_platform_date_rejected(client: TestClient, auth_headers: dict):
    """Creating a duplicate shift for same worker/platform/date should be rejected by unique constraint."""
    payload = {
        "platform": "Careem",
        "work_date": "2026-10-13",
        "hours_worked": 6.0,
        "gross_earned": 3000.0,
        "deductions": 100.0,
        "commission": 200.0,
        "net_received": 2700.0,
        "status": "pending"
    }

    # First creation should succeed
    response1 = client.post("/shifts", json=payload, headers=auth_headers)
    assert response1.status_code == 201

    # Second creation with same worker/platform/date should fail
    response2 = client.post("/shifts", json=payload, headers=auth_headers)
    assert response2.status_code == 400


def test_list_shifts_authenticated(client: TestClient, auth_headers: dict):
    """Listing shifts should return only the authenticated worker's shifts."""
    # Create a shift
    payload = {
        "platform": "Foodpanda",
        "work_date": "2026-10-14",
        "hours_worked": 4.0,
        "gross_earned": 2000.0,
        "deductions": 50.0,
        "commission": 100.0,
        "net_received": 1850.0,
        "status": "pending"
    }
    client.post("/shifts", json=payload, headers=auth_headers)

    response = client.get("/shifts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "shifts" in data
    assert "count" in data
    assert data["count"] >= 1
    for shift in data["shifts"]:
        assert shift["worker_id"] is not None


def test_get_shift_not_found(client: TestClient, auth_headers: dict):
    """Getting a non-existent shift should return 404."""
    import uuid
    fake_id = str(uuid.uuid4())
    response = client.get(f"/shifts/{fake_id}", headers=auth_headers)
    assert response.status_code == 404


def test_get_shift_own_data(client: TestClient, auth_headers: dict):
    """Getting own shift should return the shift data."""
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-15",
        "hours_worked": 5.0,
        "gross_earned": 2500.0,
        "deductions": 100.0,
        "commission": 200.0,
        "net_received": 2200.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    response = client.get(f"/shifts/{shift_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["shift_id"] == shift_id
    assert data["platform"] == "Uber"


def test_update_shift_valid_partial(client: TestClient, auth_headers: dict):
    """Valid partial update should succeed and persist changes."""
    payload = {
        "platform": "Careem",
        "work_date": "2026-10-16",
        "hours_worked": 6.0,
        "gross_earned": 3000.0,
        "deductions": 100.0,
        "commission": 200.0,
        "net_received": 2700.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    # Partial update - only change platform and status
    update_payload = {"platform": "Updated Platform", "status": "confirmed"}
    response = client.put(f"/shifts/{shift_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "Updated Platform"
    assert data["status"] == "confirmed"
    # Unchanged fields preserved
    assert data["gross_earned"] == 3000.0
    assert data["net_received"] == 2700.0


def test_update_shift_net_exceeds_gross_rejected(client: TestClient, auth_headers: dict):
    """Update that makes net > gross should be rejected."""
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-17",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 400.0,
        "net_received": 4400.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    # Try to update net_received to exceed existing gross_earned
    update_payload = {"net_received": 6000.0}  # Exceeds gross of 5000
    response = client.put(f"/shifts/{shift_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]


def test_update_shift_gross_below_existing_net_rejected(client: TestClient, auth_headers: dict):
    """Update that makes gross < existing net should be rejected."""
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-18",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 400.0,
        "net_received": 4400.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    # Try to update gross_earned below existing net_received
    update_payload = {"gross_earned": 4000.0}  # Below net of 4400
    response = client.put(f"/shifts/{shift_id}", json=update_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]


def test_update_shift_unauthorized_worker(client: TestClient, auth_headers: dict, test_verifier: str):
    """Worker A cannot update Worker B's shift."""
    # Create a shift as worker A
    payload = {
        "platform": "Foodpanda",
        "work_date": "2026-10-19",
        "hours_worked": 6.0,
        "gross_earned": 3000.0,
        "deductions": 100.0,
        "commission": 200.0,
        "net_received": 2700.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    # Try to update as worker B (using verifier token which has different sub)
    from datetime import datetime, timedelta

    import jwt
    from app.auth import ALGORITHM, SECRET_KEY
    worker_b_token = jwt.encode(
        {"sub": test_verifier, "role": "worker", "exp": datetime.now(UTC) + timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    worker_b_headers = {"Authorization": f"Bearer {worker_b_token}"}

    update_payload = {"platform": "Hacker"}
    response = client.put(f"/shifts/{shift_id}", json=update_payload, headers=worker_b_headers)
    assert response.status_code == 404  # Not found for this worker


def test_delete_shift_own_data(client: TestClient, auth_headers: dict):
    """Deleting own shift should succeed."""
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-20",
        "hours_worked": 4.0,
        "gross_earned": 2000.0,
        "deductions": 50.0,
        "commission": 100.0,
        "net_received": 1850.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    response = client.delete(f"/shifts/{shift_id}", headers=auth_headers)
    assert response.status_code == 204

    # Verify it's deleted
    get_resp = client.get(f"/shifts/{shift_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_shift_unauthorized_worker(client: TestClient, auth_headers: dict, test_verifier: str):
    """Worker A cannot delete Worker B's shift."""
    payload = {
        "platform": "Foodpanda",
        "work_date": "2026-10-21",
        "hours_worked": 6.0,
        "gross_earned": 3000.0,
        "deductions": 100.0,
        "commission": 200.0,
        "net_received": 2700.0,
        "status": "pending"
    }
    create_resp = client.post("/shifts", json=payload, headers=auth_headers)
    assert create_resp.status_code == 201
    shift_id = create_resp.json()["shift_id"]

    # Try to delete as different worker
    from datetime import datetime, timedelta

    import jwt
    from app.auth import ALGORITHM, SECRET_KEY
    worker_b_token = jwt.encode(
        {"sub": test_verifier, "role": "worker", "exp": datetime.now(UTC) + timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    worker_b_headers = {"Authorization": f"Bearer {worker_b_token}"}

    response = client.delete(f"/shifts/{shift_id}", headers=worker_b_headers)
    assert response.status_code == 404


def test_earnings_summary(client: TestClient, auth_headers: dict):
    """Earnings summary should return aggregated data for authenticated worker."""
    # Create a few shifts
    shifts = [
        {
            "platform": "Foodpanda",
            "work_date": "2026-10-22",
            "hours_worked": 8.0,
            "gross_earned": 5000.0,
            "deductions": 200.0,
            "commission": 400.0,
            "net_received": 4400.0,
            "status": "pending"
        },
        {
            "platform": "Uber",
            "work_date": "2026-10-23",
            "hours_worked": 6.0,
            "gross_earned": 3000.0,
            "deductions": 100.0,
            "commission": 200.0,
            "net_received": 2700.0,
            "status": "pending"
        }
    ]
    for shift in shifts:
        resp = client.post("/shifts", json=shift, headers=auth_headers)
        assert resp.status_code == 201

    response = client.get("/earnings/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_hours" in data
    assert "total_gross" in data
    assert "total_deductions" in data
    assert "total_commission" in data
    assert "total_net" in data
    assert "total_shifts" in data
    assert "effective_hourly_rate" in data
    assert data["total_shifts"] >= 2
    assert data["total_hours"] >= 14.0


def test_missing_jwt_rejected(client: TestClient):
    """Request without JWT should be rejected."""
    response = client.get("/shifts")
    assert response.status_code == 403  # HTTPBearer auto_error=True returns 403


def test_invalid_jwt_signature_rejected(client: TestClient):
    """Request with invalid JWT signature should be rejected."""
    import jwt
    from app.auth import ALGORITHM
    # Create token with wrong secret
    wrong_token = jwt.encode({"sub": "test", "role": "worker"}, "wrong-secret", algorithm=ALGORITHM)
    headers = {"Authorization": f"Bearer {wrong_token}"}
    response = client.get("/shifts", headers=headers)
    assert response.status_code == 401


def test_expired_jwt_rejected(client: TestClient):
    """Request with expired JWT should be rejected."""
    from datetime import datetime, timedelta

    import jwt
    from app.auth import ALGORITHM, SECRET_KEY
    expired_token = jwt.encode(
        {"sub": "test", "role": "worker", "exp": datetime.now(UTC) - timedelta(hours=1)},
        SECRET_KEY, algorithm=ALGORITHM
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/shifts", headers=headers)
    assert response.status_code == 401


def test_malformed_jwt_rejected(client: TestClient):
    """Request with malformed JWT should be rejected."""
    headers = {"Authorization": "Bearer not.a.valid.jwt"}
    response = client.get("/shifts", headers=headers)
    assert response.status_code == 401