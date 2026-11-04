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
    benefits: list[str] = Field(default_factory=list)


class MembershipPlanUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    duration_days: int = Field(gt=0)
    description: str | None = None
    benefits: list[str] = Field(default_factory=list)


class MembershipPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    duration_days: int
    description: str | None
    benefits: list[str]
    is_active: bool
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


# ---------------------------------------------------------------------------
# Planes y servicios extra (Entrega 3, Fase 2) -- amplia RF004/RF005.
# ---------------------------------------------------------------------------

BillingPeriod = Literal["unico", "mensual", "periodo"]
MembershipServiceStatus = Literal["activa", "vencida", "cancelada"]


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    billing_period: BillingPeriod
    description: str | None = None


class ServiceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: Decimal = Field(gt=0)
    billing_period: BillingPeriod
    description: str | None = None


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    billing_period: BillingPeriod
    description: str | None
    is_active: bool
    created_at: datetime


class PlanServiceAdd(BaseModel):
    """Body de `POST /membership-plans/{plan_id}/services` -- referencia un
    `Service` ya existente del catalogo por id (a diferencia de
    `ServiceCreate`, que da de alta un servicio nuevo)."""

    service_id: int


class PlanServiceRead(BaseModel):
    plan_id: int
    service_id: int


class MembershipServiceCreate(BaseModel):
    service_id: int
    start_date: date | None = None
    end_date: date | None = None


class MembershipServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    membership_id: int
    service_id: int
    price_at_purchase: Decimal
    start_date: date
    end_date: date
    status: MembershipServiceStatus
    created_at: datetime


class MembershipServiceReadLimited(BaseModel):
    """Vista del entrenador (RF: "ve los extras de sus clientes
    asignados (no precios ni pagos)") -- mismo registro que
    `MembershipServiceRead` pero sin `price_at_purchase`."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    membership_id: int
    service_id: int
    start_date: date
    end_date: date
    status: MembershipServiceStatus
