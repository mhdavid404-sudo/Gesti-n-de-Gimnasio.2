"""Entidades de dominio del modulo Diets.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# Persistido como VARCHAR + CHECK (DECISIONES.md, correccion #1).
ESTADOS_ASIGNACION_VALIDOS = ("activa", "completada", "cancelada")


@dataclass
class DietPlan:
    """Plan de dieta (RF009).

    `created_by` apunta a un `User`.

    IMPORTANTE (DECISIONES.md, correccion #4): igual que `Routine`, la FK no
    garantiza que `created_by` sea entrenador/admin -- invariante explicita
    en `application/diets` (ver `application/diets/use_cases.py`).
    """

    id: int | None
    name: str
    created_by: int
    description: str | None = None
    calories_target: int | None = None
    created_at: datetime | None = None


@dataclass
class DietAssignment:
    """Asignacion de un plan de dieta a un cliente (RF009, RF012)."""

    id: int | None
    diet_plan_id: int
    client_id: int
    assigned_by: int  # User.id
    assigned_date: date
    status: str  # uno de ESTADOS_ASIGNACION_VALIDOS
