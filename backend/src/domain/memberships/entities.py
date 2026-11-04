"""Entidades de dominio del modulo Memberships.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

# Persistido como VARCHAR + CHECK (DECISIONES.md, correccion #1).
ESTADOS_MEMBRESIA_VALIDOS = ("activa", "vencida", "cancelada", "pendiente")

# Entrega 3 (Fase 2, amplia RF004/RF005): catalogo de servicios extra y lo
# que un cliente contrata sobre su membresia. Persistidos como VARCHAR +
# CHECK, mismo criterio que el resto del modelo.
PERIODOS_FACTURACION_VALIDOS = ("unico", "mensual", "periodo")
ESTADOS_MEMBERSHIP_SERVICE_VALIDOS = ("activa", "vencida", "cancelada")


@dataclass
class MembershipPlan:
    """Plan de membresia (Basica/VIP/Premium) (RF004)."""

    id: int | None
    name: str
    price: Decimal
    duration_days: int
    description: str | None = None
    # Backlog de alineacion de modelo (DECISIONES.md, 2026-10-10): lista
    # de beneficios en texto libre, ya modelada en el frontend.
    benefits: list[str] = field(default_factory=list)
    # Entrega 3: antes no existia ningun concepto de activo/inactivo --
    # ver `DeleteOrDeactivateMembershipPlanUseCase`.
    is_active: bool = True
    created_at: datetime | None = None


@dataclass
class Membership:
    """Membresia asignada a un cliente (RF004, RF006)."""

    id: int | None
    client_id: int
    plan_id: int
    start_date: date
    end_date: date
    status: str  # uno de ESTADOS_MEMBRESIA_VALIDOS
    created_at: datetime | None = None


@dataclass
class Service:
    """Servicio extra del gimnasio, no incluido necesariamente en todos
    los planes (Entrega 3, Fase 2): rutinas personalizadas, casillero,
    clases grupales, plan de dieta personalizado, entrenador asignado,
    evaluacion de progreso quincenal, etc."""

    id: int | None
    name: str
    price: Decimal
    billing_period: str  # uno de PERIODOS_FACTURACION_VALIDOS
    description: str | None = None
    is_active: bool = True
    created_at: datetime | None = None


@dataclass
class PlanService:
    """Relacion pura: que `Service` incluye un `MembershipPlan` (tabla
    puente `plan_services`, sin `id` propio -- ver migracion 0003)."""

    plan_id: int
    service_id: int


@dataclass
class MembershipService:
    """Un `Service` CONTRATADO por un cliente sobre una `Membership`
    concreta (Entrega 3, Fase 2).

    `price_at_purchase` congela el precio del servicio al momento de la
    contratacion -- un cambio de precio posterior en el catalogo
    (`Service.price`) no debe afectar lo ya contratado (regla de negocio
    explicita del encargo). Separado de `Service` (el catalogo) de la
    misma forma que `Membership` ya esta separado de `MembershipPlan`.
    """

    id: int | None
    membership_id: int
    service_id: int
    price_at_purchase: Decimal
    start_date: date
    end_date: date
    status: str  # uno de ESTADOS_MEMBERSHIP_SERVICE_VALIDOS
    created_at: datetime | None = None
