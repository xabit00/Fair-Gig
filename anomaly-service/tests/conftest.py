from unittest.mock import MagicMock, patch

import pytest
from app.auth import require_roles, verify_token
from app.main import app
from fastapi.testclient import TestClient

MOCK_WORKER = {
    "sub": "test_worker_uuid_123",
    "role": "worker"
}

MOCK_VERIFIER = {
    "sub": "verifier_uuid_456",
    "role": "verifier"
}

MOCK_ADVOCATE = {
    "sub": "advocate_uuid_789",
    "role": "advocate"
}

# Mock the pool at module level - patch app.db.pool since that's where it's defined
@pytest.fixture(autouse=True)
def mock_pool():
    with patch("app.db.pool") as mock_pool:
        mock_pool.open = MagicMock()
        mock_pool.close = MagicMock()
        yield mock_pool

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_db():
    with patch("app.main.get_connection") as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        # Default earnings for test worker - using date objects
        from datetime import date
        earnings = [
            {
                "date": date(2026, 1, 1),
                "platform": "Careem",
                "gross_earned": 2000.0,
                "deductions": 200.0,
                "net_received": 1800.0,
            },
            {
                "date": date(2026, 1, 10),
                "platform": "Careem",
                "gross_earned": 3000.0,
                "deductions": 1800.0,  # High deduction
                "net_received": 1200.0,
            },
            {
                "date": date(2026, 2, 10),
                "platform": "Careem",
                "gross_earned": 3000.0,
                "deductions": 200.0,
                "net_received": 2800.0,
            },
        ]
        
        state = {"earnings": earnings, "worker_exists": True}
        
        def execute_side_effect(query, params=None):
            q = query.strip().upper()
            
            if "SELECT ID FROM USERS WHERE ID = %S" in q:
                mock_cursor.fetchone.return_value = {"id": params[0]} if state["worker_exists"] else None
            elif "SELECT WORK_DATE AS DATE, PLATFORM, GROSS_EARNED, DEDUCTIONS, NET_RECEIVED FROM SHIFTS" in q:
                if params and params[0]:
                    worker_id = params[0]
                    if worker_id == "test_worker_uuid_123":
                        mock_cursor.fetchall.return_value = state["earnings"]
                    elif worker_id == "other_worker_uuid_999":
                        mock_cursor.fetchall.return_value = [
                            {
                                "date": date(2026, 1, 1),
                                "platform": "Uber",
                                "gross_earned": 5000.0,
                                "deductions": 100.0,
                                "net_received": 4900.0,
                            }
                        ]
                    else:
                        mock_cursor.fetchall.return_value = []
                else:
                    mock_cursor.fetchall.return_value = state["earnings"]
            else:
                mock_cursor.fetchall.return_value = state["earnings"]
        
        mock_cursor.execute.side_effect = execute_side_effect
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        yield mock_cursor, state

@pytest.fixture
def worker_auth():
    """Override auth to worker."""
    def worker_verify():
        return MOCK_WORKER
    
    def worker_require_roles(*roles):
        if "worker" in roles:
            return worker_verify
        else:
            def deny():
                from fastapi import HTTPException, status
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
            return deny
    
    app.dependency_overrides[verify_token] = worker_verify
    app.dependency_overrides[require_roles] = worker_require_roles
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def verifier_auth():
    """Override auth to verifier."""
    def verifier_verify():
        return MOCK_VERIFIER
    
    def verifier_require_roles(*roles):
        if "verifier" in roles or "advocate" in roles:
            return verifier_verify
        else:
            def deny():
                from fastapi import HTTPException, status
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
            return deny
    
    app.dependency_overrides[verify_token] = verifier_verify
    app.dependency_overrides[require_roles] = verifier_require_roles
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def advocate_auth():
    """Override auth to advocate."""
    def advocate_verify():
        return MOCK_ADVOCATE
    
    def advocate_require_roles(*roles):
        if "advocate" in roles:
            return advocate_verify
        else:
            def deny():
                from fastapi import HTTPException, status
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
            return deny
    
    app.dependency_overrides[verify_token] = advocate_verify
    app.dependency_overrides[require_roles] = advocate_require_roles
    yield
    app.dependency_overrides.clear()