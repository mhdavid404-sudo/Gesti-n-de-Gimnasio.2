"""Modelo SQLAlchemy de la tabla `users`.

Regla dura (DECISIONES.md, correccion #2): este modelo es infraestructura
pura. La entidad de dominio equivalente vive en `domain/users/entities.py`
y no sabe nada de SQLAlchemy. El mapeo entidad <-> modelo ocurre solo en
`infrastructure/repositories/users.py`.

Regla dura (DECISIONES.md, correccion #1): `role` es VARCHAR + CHECK
constraint, NUNCA un ENUM nativo de PostgreSQL (mas caro de migrar con
Alembic; es casi seguro que aparezca un rol/estado nuevo en Entrega 2).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.base import Base


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'entrenador', 'cliente')", name="ck_users_role"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
