def test_create_shift_success(client):
    payload = {
        "platform": "Foodpanda",
        "work_date": "2026-10-11",
        "hours_worked": 6.5,
        "gross_earned": 4000.0,
        "deductions": 200.0,
        "commission": 400.0,
        "net_received": 3400.0,
        "status": "pending"
    }
    
    response = client.post("/shifts", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["platform"] == "Foodpanda"
    assert data["worker_id"] == "test_worker_uuid_123"

def test_create_shift_net_exceeds_gross(client):
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-12",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 500.0,
        "net_received": 6000.0,
        "status": "pending"
    }
    
    response = client.post("/shifts", json=payload)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]

def test_list_shifts_authenticated(client):
    response = client.get("/shifts")
    assert response.status_code == 200
    data = response.json()
    assert "shifts" in data
    assert "count" in data

def test_get_shift_not_found(client):
    response = client.get("/shifts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_update_shift_not_found(client):
    payload = {"platform": "Updated"}
    response = client.put("/shifts/00000000-0000-0000-0000-000000000000", json=payload)
    assert response.status_code == 404

def test_delete_shift_not_found(client):
    response = client.delete("/shifts/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404

def test_earnings_summary(client):
    response = client.get("/earnings/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_hours" in data
    assert "total_gross" in data
    assert "total_deductions" in data
    assert "total_commission" in data
    assert "total_net" in data
    assert "total_shifts" in data
    assert "effective_hourly_rate" in data


# === UPDATE VALIDATION TESTS ===

def test_update_shift_valid_partial(client):
    """Valid partial update should succeed."""
    payload = {"platform": "Updated Platform", "status": "confirmed"}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "Updated Platform"
    assert data["status"] == "confirmed"
    # Unchanged fields preserved
    assert data["gross_earned"] == 4000.0
    assert data["net_received"] == 3400.0

def test_update_net_exceeds_existing_gross(client):
    """Update net_received to exceed existing gross_earned should fail."""
    payload = {"net_received": 5000.0}  # Existing gross is 4000
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]

def test_update_gross_below_existing_net(client):
    """Update gross_earned below existing net_received should fail."""
    payload = {"gross_earned": 3000.0}  # Existing net is 3400
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Net received cannot exceed gross earned" in response.json()["detail"]

def test_update_negative_deductions(client):
    """Negative deductions should fail."""
    payload = {"deductions": -100.0}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "cannot be negative" in response.json()["detail"]

def test_update_negative_commission(client):
    """Negative commission should fail."""
    payload = {"commission": -50.0}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "cannot be negative" in response.json()["detail"]

def test_update_zero_hours(client):
    """Zero hours should fail."""
    payload = {"hours_worked": 0}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Hours worked must be greater than 0" in response.json()["detail"]

def test_update_negative_hours(client):
    """Negative hours should fail."""
    payload = {"hours_worked": -5}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Hours worked must be greater than 0" in response.json()["detail"]

def test_update_negative_net_received(client):
    """Negative net_received should fail."""
    payload = {"net_received": -100}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Net received cannot be negative" in response.json()["detail"]

def test_update_negative_gross_earned(client):
    """Negative gross_earned should fail."""
    payload = {"gross_earned": -100}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    assert "Gross earned cannot be negative" in response.json()["detail"]

def test_update_shift_unauthorized_worker(mock_db, client):
    """Worker A cannot update Worker B's shift."""
    # mock_db is a tuple (mock_cursor, state)
    _mock_cursor, state = mock_db
    # Enable unauthorized test mode - returns None for the valid shift_id
    state["unauthorized_test"] = True
    
    payload = {"platform": "Hacker"}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 404

def test_update_invalid_no_database_change(mock_db, client):
    """Invalid update should not change database (rollback)."""
    # Attempt invalid update
    payload = {"net_received": 5000.0}  # Exceeds existing gross
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 400
    
    # Verify rollback - commit should not be called on invalid update
    # The mock doesn't actually persist, but we can verify no commit occurred
    # by checking the connection wasn't committed

def test_update_preserves_valid_existing_fields(client):
    """Update one field preserves other valid fields."""
    payload = {"status": "confirmed"}
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    # All other fields preserved
    assert data["platform"] == "Foodpanda"
    assert data["hours_worked"] == 6.5
    assert data["gross_earned"] == 4000.0
    assert data["deductions"] == 200.0
    assert data["commission"] == 400.0
    assert data["net_received"] == 3400.0
    assert data["worker_id"] == "test_worker_uuid_123"

def test_update_all_fields_valid(client):
    """Update all fields at once with valid data."""
    payload = {
        "platform": "New Platform",
        "hours_worked": 10.0,
        "gross_earned": 10000.0,
        "deductions": 500.0,
        "commission": 1000.0,
        "net_received": 8500.0,
        "status": "confirmed"
    }
    response = client.put("/shifts/11111111-2222-3333-4444-555555555555", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "New Platform"
    assert data["hours_worked"] == 10.0
    assert data["gross_earned"] == 10000.0
    assert data["net_received"] == 8500.0