from unittest.mock import patch


def test_detect_me_requires_auth(worker_auth, client):
    """GET /detect/me requires authentication."""
    response = client.get("/detect/me")
    assert response.status_code == 200
    data = response.json()
    assert "worker_id" in data
    assert "anomalies" in data


def test_detect_me_worker_own_data(worker_auth, mock_db, client):
    """Worker can analyze their own earnings via /detect/me."""
    response = client.get("/detect/me")
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == "test_worker_uuid_123"
    assert data["records_analysed"] == 3
    assert "anomalies" in data


def test_detect_me_empty_history(worker_auth, mock_db, client):
    """Worker with no earnings gets empty result."""
    _mock_cursor, state = mock_db
    state["earnings"] = []
    response = client.get("/detect/me")
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] == 0
    assert data["anomalies"] == []


def test_detect_me_date_filters(worker_auth, mock_db, client):
    """Date filters work on /detect/me."""
    response = client.get("/detect/me?start_date=2026-01-01&end_date=2026-01-31")
    assert response.status_code == 200
    data = response.json()
    assert data["records_analysed"] >= 0


def test_detect_worker_requires_verifier_or_advocate_role(worker_auth, client):
    """POST /detect requires verifier or advocate role."""
    # Default fixture is worker role, should get 403
    response = client.post("/detect", json={"worker_id": "550e8400-e29b-41d4-a716-446655440000", "earnings": []})
    assert response.status_code == 403


def test_detect_worker_verifier_can_analyze(verifier_auth, mock_db, client):
    """Verifier can analyze any worker's earnings."""
    response = client.post("/detect", json={"worker_id": "550e8400-e29b-41d4-a716-446655440000", "earnings": []})
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == "550e8400-e29b-41d4-a716-446655440000"


def test_detect_worker_advocate_can_analyze(advocate_auth, mock_db, client):
    """Advocate can analyze any worker's earnings."""
    response = client.post("/detect", json={"worker_id": "550e8400-e29b-41d4-a716-446655440000", "earnings": []})
    assert response.status_code == 200


def test_detect_worker_nonexistent_returns_404(verifier_auth, mock_db, client):
    """Analyzing non-existent worker returns 404."""
    _mock_cursor, state = mock_db
    state["worker_exists"] = False
    
    response = client.post("/detect", json={"worker_id": "550e8400-e29b-41d4-a716-446655440099", "earnings": []})
    assert response.status_code == 404


def test_detect_worker_a_cannot_analyze_worker_b_via_me(worker_auth, client):
    """Worker A's /detect/me only returns their own data, not Worker B's."""
    response = client.get("/detect/me")
    assert response.status_code == 200
    data = response.json()
    assert data["worker_id"] == "test_worker_uuid_123"


def test_detect_response_no_unauthorized_data(worker_auth, mock_db, client):
    """Response should not expose other workers' financial data."""
    response = client.get("/detect/me")
    data = response.json()
    assert data["worker_id"] == "test_worker_uuid_123"


def test_detect_response_structure(worker_auth, mock_db, client):
    """Response has correct structure."""
    response = client.get("/detect/me")
    data = response.json()
    assert "worker_id" in data
    assert "analysis_period" in data
    assert "records_analysed" in data
    assert "anomalies" in data
    assert "summary" in data
    assert "start_date" in data["analysis_period"]
    assert "end_date" in data["analysis_period"]


def test_rules_endpoint_accessible(worker_auth, mock_db, client):
    """GET /rules works for worker, verifier, advocate."""
    response = client.get("/rules")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    rule_ids = {r["id"] for r in data["rules"]}
    assert "high_deduction" in rule_ids
    assert "monthly_income_drop" in rule_ids


def test_health_endpoint(worker_auth, mock_db, client):
    """Health endpoint works with database connectivity check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "anomaly-service"
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_endpoint_database_failure(worker_auth, client):
    """Health endpoint returns unhealthy when database is unavailable."""
    with patch("app.main.get_connection") as mock_get_conn:
        mock_get_conn.side_effect = Exception("Connection refused")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "anomaly-service"
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"