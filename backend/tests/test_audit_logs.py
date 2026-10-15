"""CP del modulo Bitacora / AuditLog (RF015) -- Entrega 2, ultimo modulo del
orden fijo.

Corre contra una base de datos Postgres real (ver `conftest.py`).
`audit_logs` no necesita TRUNCATE explicito: `user_id` tiene FK hacia
`users.id ON DELETE SET NULL` (no CASCADE) y la tabla no tiene ninguna
columna UNIQUE, asi que un registro de una corrida anterior nunca choca
con uno nuevo -- cada test crea sus propios usuarios con emails unicos y
filtra sobre SUS entradas por `action`/`user_id`, nunca asume que la tabla
esta vacia.

Casos cubiertos (CP18 -- "provocar un error controlado, consultar el log,
el error queda registrado con fecha y detalle"):
    1. Un error de autenticacion (401, login invalido) queda registrado en
       la bitacora automaticamente, sin que nadie llame un endpoint de
       bitacora a proposito.
    2. Un error de validacion de datos (422, payload invalido) tambien
       queda registrado, con el detalle del error.
    3. Un 403 (rol insuficiente) tambien se registra, asociado al usuario
       que lo provoco.
    4. `GET /audit-logs` como no-admin -> 403.
    5. Una peticion exitosa (2xx) NO genera entrada de bitacora -- solo se
       audita lo que fallo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.password import hash_password

API = "/api/v1"


def _seed_user(email: str, password: str, role: str, full_name: str = "Usuario de prueba") -> User:
    session: Session = SessionLocal()
    try:
        repository = SqlAlchemyUserRepository(session)
        created = repository.add(
            User(
                id=None,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                role=role,
                is_active=True,
            )
        )
        session.commit()
        return created
    finally:
        session.close()


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_error_de_login_invalido_queda_registrado_en_bitacora(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.audit.admin1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(
        f"{API}/auth/login",
        json={"email": admin.email, "password": "ClaveIncorrecta999"},
    )
    assert response.status_code == 401

    log = client.get(f"{API}/audit-logs", headers=headers)
    assert log.status_code == 200
    entries = log.json()
    auth_entries = [e for e in entries if e["action"] == "POST /api/v1/auth/login"]
    assert len(auth_entries) >= 1
    assert "401" in auth_entries[0]["details"]
    assert auth_entries[0]["created_at"] is not None


def test_error_de_validacion_queda_registrado_con_detalle(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.audit.admin2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(
        f"{API}/users",
        json={"email": "no-es-un-correo", "password": "x", "full_name": "", "role": "cliente"},
        headers=headers,
    )
    assert response.status_code == 422

    log = client.get(f"{API}/audit-logs", headers=headers)
    entries = log.json()
    user_entries = [
        e for e in entries if e["action"] == "POST /api/v1/users" and e["user_id"] == admin.id
    ]
    assert len(user_entries) >= 1
    assert "422" in user_entries[0]["details"]


def test_error_403_queda_asociado_al_usuario_que_lo_provoco(client: TestClient) -> None:
    cliente = _seed_user("smartgym.qa.audit.cliente1@gmail.com", "ClavePersonal123", "cliente")
    headers = _auth_headers(client, cliente.email, "ClavePersonal123")

    response = client.post(
        f"{API}/users",
        json={
            "email": "smartgym.qa.audit.intento@gmail.com",
            "password": "ClaveSegura123",
            "full_name": "Intento no autorizado",
            "role": "cliente",
        },
        headers=headers,
    )
    assert response.status_code == 403

    admin = _seed_user("smartgym.qa.audit.admin3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    log = client.get(f"{API}/audit-logs", headers=admin_headers)
    entries = log.json()
    forbidden_entries = [e for e in entries if e["user_id"] == cliente.id]
    assert len(forbidden_entries) >= 1
    assert "403" in forbidden_entries[0]["details"]


def test_consultar_bitacora_como_no_admin_devuelve_403(client: TestClient) -> None:
    cliente = _seed_user("smartgym.qa.audit.cliente2@gmail.com", "ClavePersonal123", "cliente")
    headers = _auth_headers(client, cliente.email, "ClavePersonal123")

    response = client.get(f"{API}/audit-logs", headers=headers)

    assert response.status_code == 403


def test_peticion_exitosa_no_genera_entrada_de_bitacora(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.audit.admin4@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    before = client.get(f"{API}/audit-logs", headers=headers).json()
    before_count = len(before)

    ok = client.get(f"{API}/notifications/users/{admin.id}", headers=headers)
    assert ok.status_code == 200

    after = client.get(f"{API}/audit-logs", headers=headers).json()
    # La propia consulta GET /audit-logs es exitosa y no se audita a si
    # misma -- el conteo solo puede crecer por el GET /notifications previo
    # si ese hubiera fallado, lo cual no paso (200).
    assert len(after) == before_count
