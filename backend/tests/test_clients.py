"""CP del modulo Clientes (RF003, bases de RF012/RF013) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas: TRUNCATE de `users`/`client_profiles`
por test).

Casos cubiertos:
    1. Alta exitosa de cliente (admin).
    2. Alta rechazada para rol no-admin -> 403.
    3. Listado como admin -> ve todos.
    4. Listado como entrenador -> ve solo los suyos.
    5. Acceso de cliente a su propio perfil -> 200.
    6. Acceso de cliente al perfil de otro -> 403.
    7. Reasignar entrenador con un `trainer_id` que NO es rol entrenador -> falla con mensaje correcto.
    8. Eliminar como no-admin -> 403.
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
) -> User:
    """Inserta un usuario directo en la base real, sin pasar por la API
    (mismo patron que `test_auth.py`)."""
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


def _register_client(
    client: TestClient,
    headers: dict[str, str],
    email: str,
    full_name: str = "Cliente de prueba",
    trainer_id: int | None = None,
):
    payload = {
        "email": email,
        "full_name": full_name,
        "trainer_id": trainer_id,
        "phone": "5512345678",
        "birth_date": "1995-05-20",
        "address": "Calle Falsa 123",
        "emergency_contact": "Alguien - 555-0000",
    }
    return client.post(f"{API}/clients", json=payload, headers=headers)


def test_alta_exitosa_de_cliente_como_admin(client: TestClient) -> None:
    _seed_user("smartgym.qa.admin.clientes1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, "smartgym.qa.admin.clientes1@gmail.com", "AdminPass123")

    response = _register_client(client, headers, "smartgym.qa.nuevo.cliente1@gmail.com", "Karla Jiménez")

    assert response.status_code == 201
    body = response.json()
    assert body["client"]["email"] == "smartgym.qa.nuevo.cliente1@gmail.com"
    assert body["client"]["full_name"] == "Karla Jiménez"
    assert body["client"]["trainer_id"] is None
    assert len(body["temporary_password"]) == 12


def test_alta_rechazada_para_rol_no_admin_devuelve_403(client: TestClient) -> None:
    _seed_user("smartgym.qa.entrenador.clientes1@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, "smartgym.qa.entrenador.clientes1@gmail.com", "ClaveEntrenador123")

    response = _register_client(client, headers, "smartgym.qa.intento.cliente@gmail.com")

    assert response.status_code == 403


def test_listado_como_admin_ve_todos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes2@gmail.com", "AdminPass123", "admin")
    trainer = _seed_user("smartgym.qa.entrenador.clientes2@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    _register_client(client, headers, "smartgym.qa.cliente.a@gmail.com", "Cliente A", trainer_id=trainer.id)
    _register_client(client, headers, "smartgym.qa.cliente.b@gmail.com", "Cliente B")

    response = client.get(f"{API}/clients", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2


def test_listado_como_entrenador_ve_solo_los_suyos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes3@gmail.com", "AdminPass123", "admin")
    trainer_a = _seed_user("smartgym.qa.entrenador.a@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b@gmail.com", "ClaveEntrenadorB123", "entrenador")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    _register_client(
        client, admin_headers, "smartgym.qa.cliente.de.a@gmail.com", "Cliente de A", trainer_id=trainer_a.id
    )
    _register_client(
        client, admin_headers, "smartgym.qa.cliente.de.b@gmail.com", "Cliente de B", trainer_id=trainer_b.id
    )

    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    response = client.get(f"{API}/clients", headers=trainer_a_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["email"] == "smartgym.qa.cliente.de.a@gmail.com"


def test_cliente_accede_a_su_propio_perfil(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created = _register_client(client, admin_headers, "smartgym.qa.cliente.propio@gmail.com", "Cliente Propio")
    client_id = created.json()["client"]["id"]
    temporary_password = created.json()["temporary_password"]

    client_headers = _auth_headers(client, "smartgym.qa.cliente.propio@gmail.com", temporary_password)
    response = client.get(f"{API}/clients/{client_id}", headers=client_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "smartgym.qa.cliente.propio@gmail.com"


def test_cliente_no_accede_al_perfil_de_otro_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes5@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.otro.a@gmail.com", "Cliente Otro A")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.otro.b@gmail.com", "Cliente Otro B")
    client_b_id = created_b.json()["client"]["id"]
    temporary_password_a = created_a.json()["temporary_password"]

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.otro.a@gmail.com", temporary_password_a)
    response = client.get(f"{API}/clients/{client_b_id}", headers=client_a_headers)

    assert response.status_code == 403


def test_reasignar_entrenador_con_trainer_id_invalido_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes6@gmail.com", "AdminPass123", "admin")
    cliente_no_entrenador = _seed_user(
        "smartgym.qa.cliente.no.entrenador@gmail.com", "ClaveCliente123", "cliente"
    )
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created = _register_client(client, admin_headers, "smartgym.qa.cliente.reasignar@gmail.com", "Cliente Reasignar")
    client_id = created.json()["client"]["id"]

    response = client.patch(
        f"{API}/clients/{client_id}",
        json={"trainer_id": cliente_no_entrenador.id},
        headers=admin_headers,
    )

    assert response.status_code == 400
    assert "entrenador" in response.json()["detail"].lower()


def test_eliminar_cliente_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.clientes7@gmail.com", "AdminPass123", "admin")
    trainer = _seed_user("smartgym.qa.entrenador.clientes7@gmail.com", "ClaveEntrenador123", "entrenador")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created = _register_client(client, admin_headers, "smartgym.qa.cliente.a.borrar@gmail.com", "Cliente a Borrar")
    client_id = created.json()["client"]["id"]

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    response = client.delete(f"{API}/clients/{client_id}", headers=trainer_headers)

    assert response.status_code == 403
