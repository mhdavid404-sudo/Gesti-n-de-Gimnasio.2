"""Configuracion de engine/sesion de SQLAlchemy.

La cadena de conexion viene SIEMPRE de la variable de entorno
`DATABASE_URL` (COORDINACION-ENTREGA1.md, seccion 3) -- nunca hardcodeada,
para que funcione igual en local (fuera de Docker) y dentro del contenedor
`backend` de docker-compose (host `db`, no `localhost`).

En dev, via docker-compose, el valor esperado es:
    postgresql+psycopg2://smartgym:smartgym_dev_pass@db:5432/smartgym_dev

Este modulo NO corre migraciones ni crea tablas al importarse -- eso es
exclusivamente responsabilidad de `alembic upgrade head`, corrido a mano
(ver COORDINACION-ENTREGA1.md, seccion 5).
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev",
)

# `pool_pre_ping` evita errores por conexiones muertas que Postgres cerro
# por inactividad; barato de tener y evita sorpresas en dev con Docker.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: entrega una `Session` y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
