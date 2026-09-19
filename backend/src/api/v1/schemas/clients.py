"""Schemas Pydantic (request/response) del modulo Clients."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientProfileCreate(BaseModel):
    user_id: int
    trainer_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact: str | None = Field(default=None, max_length=255)


class ClientProfileUpdate(BaseModel):
    trainer_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact: str | None = Field(default=None, max_length=255)


class ClientProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    trainer_id: int | None
    phone: str | None
    birth_date: date | None
    address: str | None
    emergency_contact: str | None
    created_at: datetime
    updated_at: datetime
