from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


Role = Literal["worker", "verifier", "advocate"]
Category = Literal["ride_hailing", "delivery", "freelancing"]


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    city_zone: str = Field(min_length=2, max_length=80)
    category: Category


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class RefreshRequest(BaseModel):
    refresh_token: str


class RoleUpdateRequest(BaseModel):
    role: Role


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: Role
    city_zone: str | None
    category: Category | None
    created_at: datetime


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

