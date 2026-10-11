"""CP de Auth/Roles (RF001, RF002) -- modulo B1 de Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas: TRUNCATE de `users` por test).

Casos cubiertos:
    1. Registro exitoso de un usuario nuevo (admin autenticado).
    2. Registro con email duplicado -> 409.
    3. Login con credenciales correctas -> devuelve token.
    4. Login con password incorrecto -> 401.
    5. Login con usuario inexistente -> 401.
    6. Acceso a ruta protegida sin token -> 401.
    7. Acceso con rol insuficiente -> 403.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.password import hash_password

API = "/api/v1"


def _seed_user(
    email: str,
    password: str,
    role: str,
    full_name: str = "Usuario de prueba",
    is_active: bool = True,
) -> User:
    """Inserta un usuario directo en la base real, sin pasar por la API.

    Simula una cuenta que ya existia antes del test (ej. el admin que va a
    hacer login para registrar a alguien mas) -- no usa el endpoint
    `POST /users` porque ese es exactamente lo que algunos de estos tests
    estan verificando.
    """
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
                is_active=is_active,
            )
        )
        session.commit()
        return created
    finally:
        session.close()


def _login(client: TestClient, email: str, password: str):
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    token = _login(client, email, password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_registro_exitoso(client: TestClient) -> None:
    _seed_user("smartgym.qa.admin1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, "smartgym.qa.admin1@gmail.com", "AdminPass123")

    response = client.post(
        f"{API}/users",
        json={
            "email": "smartgym.qa.nuevo.entrenador@gmail.com",
            "password": "ClaveSegura123",
            "full_name": "Nuevo Entrenador",
            "role": "entrenador",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "smartgym.qa.nuevo.entrenador@gmail.com"
    assert body["role"] == "entrenador"
    assert body["is_active"] is True
    assert "password" not in body
    assert "password_hash" not in body


def test_registro_con_email_duplicado_devuelve_409(client: TestClient) -> None:
    _seed_user("smartgym.qa.admin2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, "smartgym.qa.admin2@gmail.com", "AdminPass123")

    payload = {
        "email": "smartgym.qa.duplicado@gmail.com",
        "password": "ClaveSegura123",
        "full_name": "Cliente Duplicado",
        "role": "cliente",
    }

    primero = client.post(f"{API}/users", json=payload, headers=headers)
    assert primero.status_code == 201

    segundo = client.post(f"{API}/users", json=payload, headers=headers)
    assert segundo.status_code == 409
    assert "email" in segundo.json()["detail"].lower()


def test_login_con_credenciales_correctas_devuelve_token(client: TestClient) -> None:
    _seed_user("smartgym.qa.cliente1@gmail.com", "ClavePersonal123", "cliente")

    response = _login(client, "smartgym.qa.cliente1@gmail.com", "ClavePersonal123")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert len(body["access_token"]) > 20
    assert body["user"]["email"] == "smartgym.qa.cliente1@gmail.com"
    assert body["user"]["role"] == "cliente"


def test_login_con_password_incorrecto_devuelve_401(client: TestClient) -> None:
    _seed_user("smartgym.qa.cliente2@gmail.com", "ClaveCorrecta123", "cliente")

    response = _login(client, "smartgym.qa.cliente2@gmail.com", "ClaveIncorrecta999")

    assert response.status_code == 401


def test_login_con_usuario_inexistente_devuelve_401(client: TestClient) -> None:
    response = _login(client, "smartgym.qa.no.existe@gmail.com", "CualquierClave123")

    assert response.status_code == 401


def test_acceso_sin_token_a_ruta_protegida_devuelve_401(client: TestClient) -> None:
    response = client.get(f"{API}/users")

    assert response.status_code == 401


def test_acceso_con_rol_insuficiente_devuelve_403(client: TestClient) -> None:
    _seed_user("smartgym.qa.cliente3@gmail.com", "ClaveCliente123", "cliente")
    headers = _auth_headers(client, "smartgym.qa.cliente3@gmail.com", "ClaveCliente123")

    response = client.post(
        f"{API}/users",
        json={
            "email": "smartgym.qa.intento.alta@gmail.com",
            "password": "ClaveSegura123",
            "full_name": "Intento de alta no autorizado",
            "role": "cliente",
        },
        headers=headers,
    )

    assert response.status_code == 403
