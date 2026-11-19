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
# "anulado" agregado por BUG-12 (ver DECISIONES.md): un pago de una
# renovacion deshecha no se borra (se conserva el historial) -- se marca
# con este status, que lo excluye de ingresos/totales en vez de inventar
# una columna nueva para lo mismo.
ESTADOS_PAGO_VALIDOS = ("completado", "pendiente", "rechazado", "anulado")

# Entrega 3 (Fase 2): desglose de un pago por concepto.
CONCEPTOS_PAYMENT_ITEM_VALIDOS = ("plan", "servicio")


@dataclass
class Payment:
    """Pago asociado a una membresia (RF005).

    Arbitraje de la revision de arquitectura, 2026-09-12 (DECISIONES.md): `registered_by` (FK a
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


@dataclass
class PaymentItem:
    """Una linea del desglose de un `Payment` (Entrega 3, Fase 2): el plan
    en si, o un servicio extra contratado aparte. `service_id` es
    `None` para el concepto `'plan'` -- el plan no es un `Service`."""

    id: int | None
    payment_id: int
    concept: str  # uno de CONCEPTOS_PAYMENT_ITEM_VALIDOS
    amount: Decimal
    service_id: int | None = None
