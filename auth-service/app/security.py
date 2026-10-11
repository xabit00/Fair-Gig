from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import uuid

import bcrypt
import jwt

from .config import settings


ISSUER = "fairgig-auth"
AUDIENCE = "fairgig-services"


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    refresh_id: uuid.UUID
    refresh_expires_at: datetime


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_token_pair(user_id: uuid.UUID, role: str) -> TokenPair:
    now = datetime.now(timezone.utc)
    access_expires = now + timedelta(minutes=settings.access_token_minutes)
    refresh_expires = now + timedelta(days=settings.refresh_token_days)
    refresh_id = uuid.uuid4()
    common = {
        "sub": str(user_id),
        "role": role,
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
    }
    access_token = jwt.encode(
        {**common, "type": "access", "exp": access_expires},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    refresh_token = jwt.encode(
        {**common, "type": "refresh", "jti": str(refresh_id), "exp": refresh_expires},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return TokenPair(access_token, refresh_token, refresh_id, refresh_expires)


def decode_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        audience=AUDIENCE,
        issuer=ISSUER,
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Expected a {expected_type} token")
    return payload

