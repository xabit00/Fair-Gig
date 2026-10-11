from contextlib import asynccontextmanager
from uuid import UUID

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from psycopg import Connection
from psycopg.errors import UniqueViolation

from .config import settings
from .db import get_connection, pool
from .dependencies import get_current_user, require_roles
from .models import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RoleUpdateRequest,
    UserResponse,
)
from .security import (
    create_token_pair,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="FairGig Auth Service", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def issue_auth_response(connection: Connection, user: dict) -> AuthResponse:
    pair = create_token_pair(user["id"], user["role"])
    connection.execute(
        """
        INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
        VALUES (%s, %s, %s, %s)
        """,
        (pair.refresh_id, user["id"], hash_token(pair.refresh_token), pair.refresh_expires_at),
    )
    connection.commit()
    return AuthResponse(
        access_token=pair.access_token,
        refresh_token=pair.refresh_token,
        expires_in=settings.access_token_minutes * 60,
        user=UserResponse(**user),
    )


@app.get("/health")
def health(connection: Connection = Depends(get_connection)) -> dict:
    connection.execute("SELECT 1")
    return {"service": "auth-service", "status": "ok", "database": "connected"}


@app.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, connection: Connection = Depends(get_connection)) -> AuthResponse:
    try:
        user = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, role, city_zone, category)
            VALUES (%s, %s, %s, 'worker', %s, %s)
            RETURNING id, name, email, role, city_zone, category, created_at
            """,
            (
                payload.name.strip(),
                payload.email.lower(),
                hash_password(payload.password),
                payload.city_zone.strip(),
                payload.category,
            ),
        ).fetchone()
        connection.commit()
    except UniqueViolation as error:
        connection.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered") from error
    return issue_auth_response(connection, user)


@app.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, connection: Connection = Depends(get_connection)) -> AuthResponse:
    row = connection.execute(
        """
        SELECT id, name, email, password_hash, role, city_zone, category, created_at
        FROM users WHERE email = %s
        """,
        (payload.email.lower(),),
    ).fetchone()
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    user = {key: value for key, value in row.items() if key != "password_hash"}
    return issue_auth_response(connection, user)


@app.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, connection: Connection = Depends(get_connection)) -> AuthResponse:
    try:
        claims = decode_token(payload.refresh_token, "refresh")
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from error

    with connection.transaction():
        token_row = connection.execute(
            """
            SELECT id FROM refresh_tokens
            WHERE id = %s AND user_id = %s AND token_hash = %s
              AND revoked_at IS NULL AND expires_at > NOW()
            FOR UPDATE
            """,
            (claims["jti"], claims["sub"], hash_token(payload.refresh_token)),
        ).fetchone()
        if token_row is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is not active")
        connection.execute("UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = %s", (claims["jti"],))

    user = connection.execute(
        """
        SELECT id, name, email, role, city_zone, category, created_at
        FROM users WHERE id = %s
        """,
        (claims["sub"],),
    ).fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")
    return issue_auth_response(connection, user)


@app.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**user)


@app.patch("/users/{user_id}/role", response_model=UserResponse)
def update_role(
    user_id: UUID,
    payload: RoleUpdateRequest,
    _: dict = Depends(require_roles("advocate")),
    connection: Connection = Depends(get_connection),
) -> UserResponse:
    user = connection.execute(
        """
        UPDATE users SET role = %s WHERE id = %s
        RETURNING id, name, email, role, city_zone, category, created_at
        """,
        (payload.role, user_id),
    ).fetchone()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    connection.commit()
    return UserResponse(**user)

