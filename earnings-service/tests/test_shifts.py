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