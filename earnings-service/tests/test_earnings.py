from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "earnings-service"
    assert data["status"] == "healthy"

def test_create_shift_validation():
    payload = {
        "platform": "Uber",
        "work_date": "2026-10-11",
        "hours_worked": 8.0,
        "gross_earned": 5000.0,
        "deductions": 200.0,
        "commission": 500.0,
        "net_received": 6000.0,
        "status": "pending"
    }
    response = client.post("/shifts", json=payload)
    assert response.status_code == 400