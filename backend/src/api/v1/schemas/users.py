"""Schemas Pydantic (request/response) del modulo Users.

Viven en `api/`, no en `domain/`, porque son detalle de transporte HTTP
(validacion de entrada/salida), no un concepto del negocio.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Role = Literal["admin", "entrenador", "cliente"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password en texto plano; se hashea en application/.")
    full_name: str = Field(min_length=1, max_length=255)
    role: Role


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime
