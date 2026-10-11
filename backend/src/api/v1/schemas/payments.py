"""Schemas Pydantic (request/response) del modulo Payments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["efectivo", "tarjeta", "transferencia"]
PaymentStatus = Literal["completado", "pendiente", "rechazado"]


class PaymentCreate(BaseModel):
    """Defecto de diseno corregido (DECISIONES.md, modulo Pagos): el
    esqueleto original traia `registered_by: int` aqui, es decir, el
    CLIENTE HTTP decidia quien registro el pago -- cualquier llamada podia
    falsificar esa autoria. Se quita del payload; el router lo rellena
    siempre con `current_user.id` (el admin autenticado que hace la
    peticion), nunca con un valor que venga del body.
    """

    membership_id: int
    amount: Decimal = Field(gt=0)
    payment_date: datetime
    method: PaymentMethod
    status: PaymentStatus = "completado"
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
