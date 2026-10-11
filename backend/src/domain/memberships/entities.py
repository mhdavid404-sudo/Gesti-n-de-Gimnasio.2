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
