"""Modelo SQLAlchemy de la tabla `payments`.

Ver nota de reglas duras en `infrastructure/db/models/users.py`.
`method` y `status` son VARCHAR + CHECK (DECISIONES.md, correccion #1).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class PaymentModel(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('efectivo', 'tarjeta', 'transferencia')",
            name="ck_payments_method",
        ),
        CheckConstraint(
            "status IN ('completado', 'pendiente', 'rechazado')",
            name="ck_payments_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): FK de "quien lo hizo",
    # consistente con `assigned_by` en routine/diet assignments.
    registered_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
