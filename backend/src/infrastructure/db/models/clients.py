"""Modelo SQLAlchemy de la tabla `client_profiles`.

Ver nota de reglas duras en `infrastructure/db/models/users.py`.

Nota (DECISIONES.md, correccion #4): la FK `trainer_id -> users.id` NO
garantiza que ese usuario tenga `role = 'entrenador'`. Esa invariante es
responsabilidad de `application/clients/use_cases.py`.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class ClientProfileModel(Base):
    __tablename__ = "client_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    trainer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): campo unico de texto
    # libre, igual que `address` -- no separado en nombre/telefono.
    emergency_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
