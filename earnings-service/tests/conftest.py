from unittest.mock import MagicMock, patch

import pytest
from app.auth import verify_token
from app.main import app
from fastapi.testclient import TestClient

MOCK_WORKER = {
    "sub": "test_worker_uuid_123",
    "role": "worker"
}

@pytest.fixture(autouse=True)
def override_auth():
    app.dependency_overrides[verify_token] = lambda: MOCK_WORKER
    yield
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_db():
    with patch("app.main.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Default shift return value - this will be mutated
        valid_shift = {
            "shift_id": "11111111-2222-3333-4444-555555555555",
            "worker_id": "test_worker_uuid_123",
            "platform": "Foodpanda",
            "work_date": "2026-10-11",
            "hours_worked": 6.5,
            "gross_earned": 4000.0,
            "deductions": 200.0,
            "commission": 400.0,
            "net_received": 3400.0,
            "status": "pending",
            "created_at": "2026-10-11T12:00:00"
        }
        
        # Summary return value with actual int/float numbers
        summary_data = {
            "total_hours": 8.0,
            "total_gross": 5000.0,
            "total_deductions": 200.0,
            "total_commission": 500.0,
            "total_net": 4300.0,
            "total_shifts": 1
        }
        
        # Track state for dynamic responses
        state = {"current_shift": valid_shift.copy(), "unauthorized_test": False}
        
        def execute_side_effect(query, params=None):
            q = query.strip().upper()
            
            if "SUM(HOURS_WORKED)" in q:
                mock_cursor.fetchone.return_value = summary_data
            elif "SELECT * FROM SHIFTS WHERE SHIFT_ID = %S" in q and params and params[0] == "00000000-0000-0000-0000-000000000000" or "DELETE FROM SHIFTS WHERE SHIFT_ID = %S" in q and params and params[0] == "00000000-0000-0000-0000-000000000000":
                mock_cursor.fetchone.return_value = None
            elif "INSERT INTO SHIFTS" in q:
                mock_cursor.fetchone.return_value = state["current_shift"]
            elif "UPDATE SHIFTS" in q:
                # Parse SET clause to update state
                if params:
                    set_clause_start = q.find("SET ")
                    where_clause_start = q.find(" WHERE ")
                    if set_clause_start != -1 and where_clause_start != -1:
                        set_clause = q[set_clause_start + 4:where_clause_start].strip()
                        columns = [c.split("=")[0].strip().lower() for c in set_clause.split(",")]
                        values = params[:-2] if len(params) > 2 else params
                        for col, val in zip(columns, values):
                            if col in state["current_shift"]:
                                state["current_shift"][col] = val
                mock_cursor.fetchone.return_value = state["current_shift"]
            elif "SELECT * FROM SHIFTS WHERE SHIFT_ID = %S" in q:
                # Check if this is an unauthorized test - return None if flag set
                if state.get("unauthorized_test") and params and params[0] == "11111111-2222-3333-4444-555555555555":
                    mock_cursor.fetchone.return_value = None
                else:
                    mock_cursor.fetchone.return_value = state["current_shift"]
            else:
                mock_cursor.fetchone.return_value = state["current_shift"]
            
            # For fetchall (list shifts)
            if "SELECT * FROM SHIFTS WHERE WORKER_ID" in q:
                mock_cursor.fetchall.return_value = [state["current_shift"]]

        mock_cursor.execute.side_effect = execute_side_effect
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        yield mock_cursor, state

@pytest.fixture
def client():
    return TestClient(app)