"""Schemas Pydantic (request/response) del modulo Auth."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from src.api.v1.schemas.users import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead
