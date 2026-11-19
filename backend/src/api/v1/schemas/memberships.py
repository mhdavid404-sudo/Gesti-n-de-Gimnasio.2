"""Schemas Pydantic (request/response) del modulo Memberships."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.api.v1.schemas.payments import PaymentMethod, PaymentRead

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
MembershipServiceStatus = Literal[
    "activa", "vencida", "cancelada", "cancelado_por_cambio_de_plan"
]


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


# ---------------------------------------------------------------------------
# Tablero de membresias activas (Entrega 3, ajuste de UX de "Membresias") --
# ver DECISIONES.md: el catalogo de planes/servicios se muda por completo a
# la pantalla "Planes y servicios"; esta pantalla pasa a ser un tablero
# operativo de membresias ACTIVAS (ni catalogo, ni vencidas).
# ---------------------------------------------------------------------------


class ActiveMembershipRow(BaseModel):
    membership_id: int
    client_id: int
    client_name: str
    plan_id: int
    plan_name: str
    active_extras: list[str]
    start_date: date
    end_date: date
    days_remaining: int
    expiring_soon: bool


class ActiveMembershipsIndicators(BaseModel):
    total_active: int
    expiring_soon: int
    # `None` para `entrenador` -- regla explicita del encargo ("sin
    # ingresos"), no solo un valor en 0.
    monthly_revenue: Decimal | None = None


class ActiveMembershipsBoard(BaseModel):
    indicators: ActiveMembershipsIndicators
    items: list[ActiveMembershipRow]


# ---------------------------------------------------------------------------
# Cambio de plan (amplia RF004/RF005 de nuevo) -- ver DECISIONES.md, entrada
# "Cambio de plan: efecto en servicios extra". `PlanChangeRequest` sirve
# para AMBOS endpoints (previsualizar y confirmar) a proposito: el mismo
# body, el mismo calculo -- `notes` solo tiene efecto en la confirmacion.
# ---------------------------------------------------------------------------


class PlanChangeRequest(BaseModel):
    new_plan_id: int
    notes: str | None = None


class PlanChangeExtraRow(BaseModel):
    membership_service_id: int
    service_id: int
    service_name: str
    price_at_purchase: Decimal


class PlanChangeContractableRow(BaseModel):
    service_id: int
    service_name: str
    price: Decimal


class PlanChangePreview(BaseModel):
    membership_id: int
    client_id: int
    old_plan_id: int
    old_plan_name: str
    old_plan_price: Decimal
    new_plan_id: int
    new_plan_name: str
    new_plan_price: Decimal
    price_difference: Decimal
    cancelled_extras: list[PlanChangeExtraRow]
    cancelled_extras_total: Decimal
    kept_extras: list[PlanChangeExtraRow]
    newly_contractable_services: list[PlanChangeContractableRow]


# ---------------------------------------------------------------------------
# Renovar + cobrar, y deshacer (BUG-12, ver DECISIONES.md). "Renovar" dejo de
# ser una accion separada de "cobrar" -- ver `RenewAndChargeMembershipUseCase`
# y `UndoMembershipRenewalUseCase` en `application/memberships/use_cases.py`.
# ---------------------------------------------------------------------------


class MembershipRenewRequest(BaseModel):
    method: PaymentMethod
    # Ninguna pantalla lo manda hoy -- por defecto "ahora mismo" (mismo
    # criterio que `PaymentCreate.payment_date`, aqui opcional porque el
    # momento del cobro de una renovacion siempre es "en este instante").
    payment_date: datetime | None = None


class MembershipRenewalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    membership_id: int
    payment_id: int
    previous_end_date: date
    new_end_date: date
    previous_status: MembershipStatus
    performed_by: int
    reversed_at: datetime | None
    reversed_reason: str | None
    reversed_by: int | None
    created_at: datetime


class MembershipRenewResult(BaseModel):
    membership: MembershipRead
    payment: PaymentRead
    renewal: MembershipRenewalRead


class MembershipRenewalUndoRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class MembershipRenewalUndoResult(BaseModel):
    membership: MembershipRead
    payment: PaymentRead
    renewal: MembershipRenewalRead
