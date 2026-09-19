"""Schemas Pydantic (request/response) del modulo Payments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["efectivo", "tarjeta", "transferencia"]
PaymentStatus = Literal["completado", "pendiente", "rechazado"]


class PaymentCreate(BaseModel):
    membership_id: int
    amount: Decimal = Field(gt=0)
    payment_date: datetime
    method: PaymentMethod
    status: PaymentStatus = "completado"
    registered_by: int
    notes: str | None = None


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    membership_id: int
    amount: Decimal
    payment_date: datetime
    method: PaymentMethod
    status: PaymentStatus
    registered_by: int
    notes: str | None
    created_at: datetime
