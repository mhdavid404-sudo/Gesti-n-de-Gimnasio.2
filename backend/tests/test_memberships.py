"""CP del modulo Planes y Membresias (RF004) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas: TRUNCATE de
`users`/`client_profiles`/`membership_plans`/`memberships` por test).

Casos cubiertos:
    1. Crear plan como admin -> 201.
    2. Crear plan como no-admin -> 403.
    3. Listar planes como cualquier rol autenticado -> 200.
    4. Asignar membresia exitosa (admin) -> 201.
    5. Asignar membresia con `plan_id` inexistente -> 404, mensaje claro.
    6. Asignar membresia con `end_date <= start_date` -> 400.
    7. Listado de membresias como admin -> ve todas.
    8. Listado de membresias como entrenador -> ve solo las de sus clientes.
    9. Cliente accede a su propia membresia -> 200; a la de otro -> 403.
    10. Cambio de status como no-admin -> 403.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.password import hash_password

API = "/api/v1"


def _seed_user(email: str, password: str, role: str, full_name: str = "Usuario de prueba") -> User:
    """Inserta un usuario directo en la base real, sin pasar por la API
    (mismo patron que `test_auth.py`/`test_clients.py`)."""
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


def _create_plan(client: TestClient, headers: dict[str, str], name: str = "Basica"):
    payload = {
        "name": name,
        "price": "399.00",
        "duration_days": 30,
        "description": "Plan de acceso basico",
        "benefits": ["Acceso a area de pesas"],
    }
    return client.post(f"{API}/membership-plans", json=payload, headers=headers)


def test_crear_plan_como_admin(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    response = _create_plan(client, headers, "Basica Memb1")

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Basica Memb1"
    assert body["duration_days"] == 30
    assert body["benefits"] == ["Acceso a area de pesas"]


def test_crear_plan_como_no_admin_devuelve_403(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.membresias1@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    response = _create_plan(client, headers, "Basica Memb2")

    assert response.status_code == 403


def test_listar_planes_como_cualquier_rol_autenticado(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias2@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    _create_plan(client, admin_headers, "VIP Memb3")

    cliente = _seed_user("smartgym.qa.cliente.membresias3@gmail.com", "ClaveCliente123", "cliente")
    cliente_headers = _auth_headers(client, cliente.email, "ClaveCliente123")

    response = client.get(f"{API}/membership-plans", headers=cliente_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "VIP Memb3"


def test_asignar_membresia_exitosa(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias4@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Premium Memb4").json()["id"]
    client_id = _register_client(client, headers, "smartgym.qa.cliente.membresias4@gmail.com").json()["client"]["id"]

    today = date.today()
    response = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "status": "activa",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client_id
    assert body["plan_id"] == plan_id
    assert body["status"] == "activa"


def test_asignar_membresia_con_plan_inexistente_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    client_id = _register_client(client, headers, "smartgym.qa.cliente.membresias5@gmail.com").json()["client"]["id"]

    today = date.today()
    response = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": 999999,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "status": "activa",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


def test_asignar_membresia_con_fechas_invalidas_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias6@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Memb6").json()["id"]
    client_id = _register_client(client, headers, "smartgym.qa.cliente.membresias6@gmail.com").json()["client"]["id"]

    today = date.today()
    response = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today - timedelta(days=1)).isoformat(),
            "status": "activa",
        },
        headers=headers,
    )

    assert response.status_code == 400


def test_listado_de_membresias_como_admin_ve_todas(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias7@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Memb7").json()["id"]
    client_a_id = _register_client(client, headers, "smartgym.qa.cliente.a.memb7@gmail.com").json()["client"]["id"]
    client_b_id = _register_client(client, headers, "smartgym.qa.cliente.b.memb7@gmail.com").json()["client"]["id"]

    today = date.today()
    for cid in (client_a_id, client_b_id):
        client.post(
            f"{API}/memberships",
            json={
                "client_id": cid,
                "plan_id": plan_id,
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=30)).isoformat(),
                "status": "activa",
            },
            headers=headers,
        )

    response = client.get(f"{API}/memberships", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listado_de_membresias_como_entrenador_ve_solo_las_de_sus_clientes(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias8@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.memb8@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.memb8@gmail.com", "ClaveEntrenadorB123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Memb8").json()["id"]
    client_a_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.a.memb8@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    client_b_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.b.memb8@gmail.com", trainer_id=trainer_b.id
    ).json()["client"]["id"]

    today = date.today()
    for cid in (client_a_id, client_b_id):
        client.post(
            f"{API}/memberships",
            json={
                "client_id": cid,
                "plan_id": plan_id,
                "start_date": today.isoformat(),
                "end_date": (today + timedelta(days=30)).isoformat(),
                "status": "activa",
            },
            headers=admin_headers,
        )

    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    response = client.get(f"{API}/memberships", headers=trainer_a_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == client_a_id


def test_cliente_accede_a_su_propia_membresia_pero_no_a_la_de_otro(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias9@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, admin_headers, "Basica Memb9").json()["id"]
    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.memb9@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.memb9@gmail.com")
    client_a_id = created_a.json()["client"]["id"]
    client_b_id = created_b.json()["client"]["id"]
    password_a = created_a.json()["temporary_password"]

    today = date.today()
    membership_a = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_a_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "status": "activa",
        },
        headers=admin_headers,
    ).json()
    membership_b = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_b_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "status": "activa",
        },
        headers=admin_headers,
    ).json()

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.memb9@gmail.com", password_a)

    own = client.get(f"{API}/memberships/{membership_a['id']}", headers=client_a_headers)
    assert own.status_code == 200

    other = client.get(f"{API}/memberships/{membership_b['id']}", headers=client_a_headers)
    assert other.status_code == 403


def test_cambio_de_status_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias10@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.membresias10@gmail.com", "ClaveEntrenador123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Memb10").json()["id"]
    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.membresias10@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]

    today = date.today()
    membership = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=30)).isoformat(),
            "status": "activa",
        },
        headers=admin_headers,
    ).json()

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    response = client.patch(
        f"{API}/memberships/{membership['id']}",
        json={"status": "cancelada"},
        headers=trainer_headers,
    )

    assert response.status_code == 403
