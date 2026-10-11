import uuid

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

