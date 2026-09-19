"""Entidades de dominio del modulo Payments.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

# Persistidos como VARCHAR + CHECK (DECISIONES.md, correccion #1).
METODOS_PAGO_VALIDOS = ("efectivo", "tarjeta", "transferencia")
ESTADOS_PAGO_VALIDOS = ("completado", "pendiente", "rechazado")


@dataclass
class Payment:
    """Pago asociado a una membresia (RF005).

    Arbitraje de Isai, 2026-09-12 (DECISIONES.md): `registered_by` (FK a
    `User`, quien registro el pago) agregado por consistencia con
    `assigned_by` en routine/diet assignments.
    """

    id: int | None
    membership_id: int
    amount: Decimal
    payment_date: datetime
    method: str  # uno de METODOS_PAGO_VALIDOS
    status: str  # uno de ESTADOS_PAGO_VALIDOS
    registered_by: int
    notes: str | None = None
    created_at: datetime | None = None
