"""Base declarativa de SQLAlchemy.

Unico punto de la app que define la `DeclarativeBase`. Todos los modelos en
`infrastructure/db/models/*` heredan de aqui. Alembic (`migrations/env.py`)
importa `Base.metadata` desde este modulo para autogenerar/validar
migraciones.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
