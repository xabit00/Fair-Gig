import uuid
from datetime import datetime, timezone

from app.models import LoginRequest, UserResponse
from app.security import create_token_pair, decode_token, hash_password, verify_password


def test_password_and_tokens_round_trip() -> None:
    password_hash = hash_password("FairGig123!")
    assert verify_password("FairGig123!", password_hash)
    assert not verify_password("wrong-password", password_hash)

    user_id = uuid.uuid4()
    pair = create_token_pair(user_id, "worker")
    access = decode_token(pair.access_token, "access")
    refresh = decode_token(pair.refresh_token, "refresh")
    assert access["sub"] == str(user_id)
    assert access["role"] == "worker"
    assert refresh["jti"] == str(pair.refresh_id)


def test_seeded_staff_test_domain_is_accepted() -> None:
    login = LoginRequest(email="verifier@fairgig.test", password="FairGig123!")
    user = UserResponse(
        id=uuid.uuid4(),
        name="Demo Verifier",
        email=login.email,
        role="verifier",
        city_zone=None,
        category=None,
        created_at=datetime.now(timezone.utc),
    )

    assert user.email == "verifier@fairgig.test"
