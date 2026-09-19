"""Entidades de dominio del modulo Users.

Regla dura (DECISIONES.md, correccion #2 de Isai): estas clases son
dataclasses planas. CERO imports de SQLAlchemy, FastAPI o cualquier otro
detalle de infraestructura. El mapeo a la tabla real vive en
`infrastructure/db/models/users.py`, y la conversion entidad <-> modelo ORM
ocurre unicamente en `infrastructure/repositories/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Valores permitidos para `role`. Persistidos como VARCHAR + CHECK constraint
# en la base de datos (DECISIONES.md, correccion #1) -- NUNCA como ENUM
# nativo de PostgreSQL. Esta tupla es la fuente de verdad en el dominio;
# el CHECK de la migracion debe reflejar exactamente estos valores.
ROLES_VALIDOS = ("admin", "entrenador", "cliente")


@dataclass
class User:
    """Usuario del sistema (RF001, RF002).

    Cubre admin/entrenador/cliente en una sola tabla de identidad; los datos
    especificos de cliente (telefono, entrenador asignado, etc.) viven en
    `ClientProfile` (modulo `clients`) para no ensuciar esta entidad con
    columnas que admin/entrenador nunca usan.
    """

    id: int | None
    email: str
    password_hash: str
    full_name: str
    role: str  # uno de ROLES_VALIDOS
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
