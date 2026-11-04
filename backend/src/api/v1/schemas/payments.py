"""Schemas Pydantic (request/response) del modulo Payments."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["efectivo", "tarjeta", "transferencia"]
PaymentStatus = Literal["completado", "pendiente", "rechazado"]
PaymentItemConcept = Literal["plan", "servicio"]


class PaymentItemCreate(BaseModel):
    """Entrega 3, Fase 2: una linea del desglose de un pago. `service_id`
    obligatorio solo para concepto `'servicio'` -- validado en el router,
    no aqui (Pydantic no expresa bien "requerido si X", y el dominio ya
    lo valida de cualquier forma del lado del caso de uso)."""

    concept: PaymentItemConcept
    amount: Decimal = Field(gt=0)
    service_id: int | None = None


class PaymentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_id: int
    concept: PaymentItemConcept
    amount: Decimal
    service_id: int | None


class PaymentCreate(BaseModel):
    """Defecto de diseno corregido (DECISIONES.md, modulo Pagos): el
    esqueleto original traia `registered_by: int` aqui, es decir, el
    CLIENTE HTTP decidia quien registro el pago -- cualquier llamada podia
    falsificar esa autoria. Se quita del payload; el router lo rellena
    siempre con `current_user.id` (el admin autenticado que hace la
    peticion), nunca con un valor que venga del body.

    `items` (Entrega 3, Fase 2): desglose opcional del pago (plan vs.
    servicios extra). Si se manda, la suma de sus montos debe coincidir
    exactamente con `amount` -- lo valida `RegisterPaymentUseCase`.
    """

    membership_id: int
    amount: Decimal = Field(gt=0)
    payment_date: datetime
    method: PaymentMethod
    status: PaymentStatus = "completado"
    notes: str | None = None
    items: list[PaymentItemCreate] = Field(default_factory=list)


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
    items: list[PaymentItemRead] = Field(default_factory=list)
