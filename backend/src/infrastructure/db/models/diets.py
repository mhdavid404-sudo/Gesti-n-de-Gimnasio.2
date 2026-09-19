"""Modelos SQLAlchemy de `diet_plans` y `diet_assignments`.

Ver nota de reglas duras en `infrastructure/db/models/users.py`.
`status` en `diet_assignments` es VARCHAR + CHECK (correccion #1).

Nota (DECISIONES.md, correccion #4): la FK `diet_plans.created_by ->
users.id` NO garantiza el rol del usuario. Ver
`application/diets/use_cases.py`.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class DietPlanModel(Base):
    __tablename__ = "diet_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    calories_target: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DietAssignmentModel(Base):
    __tablename__ = "diet_assignments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('activa', 'completada', 'cancelada')",
            name="ck_diet_assignments_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    diet_plan_id: Mapped[int] = mapped_column(
        ForeignKey("diet_plans.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    assigned_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    assigned_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
