"""Modelo SQLAlchemy de la tabla `body_progress`.

Ver nota de reglas duras en `infrastructure/db/models/users.py`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class BodyProgressModel(Base):
    __tablename__ = "body_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    # Nota (DECISIONES.md, punto menor no bloqueante): height_cm se deja
    # aqui y no en client_profiles por ahora.
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    body_fat_pct: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    muscle_mass_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): RF010 pide "medidas"
    # explicitamente; restauradas tras haberse omitido en la propuesta original.
    chest_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    waist_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    hip_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    arm_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
