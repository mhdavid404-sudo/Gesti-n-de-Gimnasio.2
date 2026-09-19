"""Schemas Pydantic (request/response) del modulo Memberships."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MembershipStatus = Literal["activa", "vencida", "cancelada", "pendiente"]


class MembershipPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    duration_days: int = Field(gt=0)
    description: str | None = None


class MembershipPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    duration_days: int
    description: str | None
    created_at: datetime


class MembershipCreate(BaseModel):
    client_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: MembershipStatus = "activa"


class MembershipUpdate(BaseModel):
    status: MembershipStatus


class MembershipRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: MembershipStatus
    created_at: datetime
