"""Configuracion compartida de pytest para el backend.

Estrategia de aislamiento entre pruebas (decision de diseno registrada en
DECISIONES.md, 2026-10-10): TRUNCATE de las tablas `users` y
`client_profiles` (con CASCADE) antes y despues de cada test. Se descarto
el patron de "transaccion por test" (envolver cada test en una
transaccion/SAVEPOINT que se revierte al final) porque el codigo de
aplicacion hace `commit()` explicito dentro de los routers
(`register_user`, `update_user`, `delete_user`, y ahora los de
`clients.py`); combinar eso de forma segura con una sesion de prueba atada
a una transaccion externa exige el patron de SAVEPOINT + evento
`after_transaction_end` de SQLAlchemy, complejidad que no se justifica
todavia con pocos modulos de pruebas de integracion real. TRUNCATE es mas
simple, explicito y perfectamente suficiente para este alcance. Si en una
entrega posterior crece el numero de modulos con pruebas de integracion
reales sobre tablas relacionadas, reevaluar hacia transaccion-por-test.

`client_profiles` se trunca de forma explicita (no solo por el efecto
CASCADE de truncar `users`) para que quede documentado en el propio codigo
que el modulo Clientes (Entrega 2) tambien necesita aislamiento entre
tests -- aunque TRUNCATE ... CASCADE sobre `users` ya arrastra
`client_profiles` por la FK `client_profiles.user_id -> users.id`.

`membership_plans`/`memberships` se agregan al mismo TRUNCATE (modulo
Planes y Membresias, Entrega 2): `memberships` tambien cae en cascada al
truncar `client_profiles` (FK `memberships.client_id -> client_profiles.id
ON DELETE CASCADE`), pero `membership_plans` NO tiene ninguna FK hacia
`users`/`client_profiles` -- sin truncarla de forma explicita, el `name`
`UNIQUE` del catalogo de planes rompe cualquier segundo test que intente
crear un plan con el mismo nombre.

`notifications` (modulo Vencimientos/Notificaciones, Entrega 2) NO se
agrega de forma explicita a este TRUNCATE -- a diferencia de
`membership_plans`, `notifications.user_id` SI tiene FK directa hacia
`users.id` (`ON DELETE CASCADE`, ver
`infrastructure/db/models/notifications.py`), asi que `TRUNCATE ...
CASCADE` sobre `users` ya la arrastra automaticamente (Postgres hace
cascade de TRUNCATE siguiendo cualquier FK hacia una tabla truncada,
independientemente de su `ON DELETE`). Verificado con
`pytest tests/test_notifications.py` corrido dos veces seguidas sin
colisiones de datos entre corridas.

Requiere una base de datos real corriendo y con las migraciones aplicadas
antes de correr pytest:

    docker compose up -d db
    cd backend
    DATABASE_URL=postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev alembic upgrade head

Variables de entorno: si no estan ya seteadas en el entorno, este archivo
las rellena con el mismo valor de desarrollo de `.env.example` (raiz del
repo) para que `pytest backend/tests/test_auth.py` funcione out-of-the-box
en local sin Docker, apuntando a `localhost` en vez de `db`.
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev",
)
os.environ.setdefault("JWT_SECRET", "test-only-secret-no-usar-en-produccion")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from src.api.main import app  # noqa: E402
from src.infrastructure.db.session import engine  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_users_table() -> None:
    """Deja `users`/`client_profiles` vacias antes y despues de cada test
    (ver estrategia arriba)."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE users, client_profiles, membership_plans, memberships "
                "RESTART IDENTITY CASCADE"
            )
        )
    yield
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE users, client_profiles, membership_plans, memberships "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
