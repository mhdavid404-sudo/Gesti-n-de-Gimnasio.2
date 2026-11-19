"""Modelos SQLAlchemy de `membership_plans` y `memberships`.

Ver nota de reglas duras en `infrastructure/db/models/users.py`.
`status` es VARCHAR + CHECK (DECISIONES.md, correccion #1).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class MembershipPlanModel(Base):
    __tablename__ = "membership_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Backlog de alineacion de modelo (DECISIONES.md, 2026-10-10): el
    # frontend ya tenia `benefits: string[]` sin respaldo en el backend.
    # JSON porque es una lista de texto libre, nunca se filtra/consulta
    # por beneficio individual -- no amerita tabla puente.
    benefits: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list, server_default="[]"
    )
    # Entrega 3: antes no existia ningun concepto de activo/inactivo.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MembershipModel(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint(
            "status IN ('activa', 'vencida', 'cancelada', 'pendiente')",
            name="ck_memberships_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="RESTRICT"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ServiceModel(Base):
    """Entrega 3, Fase 2: catalogo de servicios extra."""

    __tablename__ = "services"
    __table_args__ = (
        CheckConstraint(
            "billing_period IN ('unico', 'mensual', 'periodo')",
            name="ck_services_billing_period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    billing_period: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class PlanServiceModel(Base):
    """Tabla puente `plan_services` -- sin `id` propio, relacion pura."""

    __tablename__ = "plan_services"

    plan_id: Mapped[int] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="CASCADE"), primary_key=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), primary_key=True
    )


class MembershipServiceModel(Base):
    """Entrega 3, Fase 2: un `Service` contratado por un cliente sobre una
    `Membership` concreta."""

    __tablename__ = "membership_services"
    __table_args__ = (
        CheckConstraint(
            "status IN ('activa', 'vencida', 'cancelada', 'cancelado_por_cambio_de_plan')",
            name="ck_membership_services_status",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    # String(40), no 20: "cancelado_por_cambio_de_plan" (29 caracteres) no
    # entraba en VARCHAR(20) -- ver migracion 0004.
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class MembershipRenewalModel(Base):
    """BUG-12 (ver DECISIONES.md): historial de renovaciones, usado para
    poder deshacer la ULTIMA renovacion de una membresia. Tabla nueva --
    ver migracion 0005."""

    __tablename__ = "membership_renewals"

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="RESTRICT"), nullable=False
    )
    previous_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    new_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    performed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reversed_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reversed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
