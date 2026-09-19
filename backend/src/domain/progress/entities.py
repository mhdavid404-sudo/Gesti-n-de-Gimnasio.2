"""Entidades de dominio del modulo Progress.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class BodyProgress:
    """Registro de progreso corporal de un cliente (RF010, RF011).

    Nota (DECISIONES.md, punto menor no bloqueante): `height_cm` se deja
    aqui y no en `ClientProfile` por ahora; pendiente de confirmar con el
    negocio real en una entrega posterior.

    Arbitraje de Isai, 2026-09-12 (DECISIONES.md): RF010 pide "peso,
    medidas, fecha de registro" -- `chest_cm/waist_cm/hip_cm/arm_cm`
    restauradas (nullable, sin exclusion mutua con `muscle_mass_kg`).
    """

    id: int | None
    client_id: int
    record_date: date
    weight_kg: Decimal
    height_cm: Decimal | None = None
    body_fat_pct: Decimal | None = None
    muscle_mass_kg: Decimal | None = None
    chest_cm: Decimal | None = None
    waist_cm: Decimal | None = None
    hip_cm: Decimal | None = None
    arm_cm: Decimal | None = None
    notes: str | None = None
