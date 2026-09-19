"""Entry point de Alembic.

Nota de robustez de imports: se inserta la raiz de `backend/` en `sys.path`
explicitamente (en vez de depender de que `alembic` se invoque siempre
desde ese directorio con el cwd ya en el path) para que `import src...`
funcione sin importar desde donde se dispare el comando `alembic`.

La URL de conexion se toma de la variable de entorno `DATABASE_URL`
(COORDINACION-ENTREGA1.md, seccion 3) -- nunca hardcodeada aqui.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# backend/src/infrastructure/migrations/env.py -> backend/
BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from src.infrastructure.db.base import Base  # noqa: E402
from src.infrastructure.db import models  # noqa: E402, F401  (registra todos los modelos)

# Objeto de configuracion de Alembic, provee acceso a alembic.ini.
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata objetivo para `--autogenerate` (en Entrega 1 escribimos las
# migraciones a mano, pero dejamos esto correcto para Entrega 2).
target_metadata = Base.metadata


def get_database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev",
    )


def run_migrations_offline() -> None:
    """Genera SQL sin conectarse a una BD real (`alembic upgrade head --sql`)."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Corre las migraciones conectandose a la BD real."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
