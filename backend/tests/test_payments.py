"""CP del modulo Pagos (RF005) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas). `payments` no necesita TRUNCATE
explicito: cae en cascada al truncar `client_profiles`/`memberships`
(`payments.membership_id -> memberships.id ON DELETE CASCADE`, y
`memberships.client_id -> client_profiles.id ON DELETE CASCADE`).

Casos cubiertos:
    1. Registrar pago exitoso (admin) -> 201, `registered_by` en la
       respuesta es el id del admin autenticado (nunca un valor inyectado
       en el body -- el body ya no acepta ese campo).
    2. Registrar pago con `membership_id` inexistente -> 404.
    3. Registrar pago como no-admin -> 403.
    4. Listado como admin ve todos los pagos.
    5. Listado como entrenador ve solo los de sus clientes.
    6. Cliente accede a su propio pago, pero no al de otro -> 403.
"""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

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


def _assign_membership(client: TestClient, headers: dict[str, str], client_id: int, plan_id: int) -> dict:
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
    return response.json()


def _payment_payload(membership_id: int) -> dict:
    return {
        "membership_id": membership_id,
        "amount": "399.00",
        "payment_date": datetime.now(timezone.utc).isoformat(),
        "method": "efectivo",
        "status": "completado",
        "notes": "Pago de prueba",
    }


def test_registrar_pago_exitoso_como_admin(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Pago1").json()["id"]
    client_id = _register_client(client, headers, "smartgym.qa.cliente.pagos1@gmail.com").json()["client"]["id"]
    membership_id = _assign_membership(client, headers, client_id, plan_id)["id"]

    response = client.post(f"{API}/payments", json=_payment_payload(membership_id), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["membership_id"] == membership_id
    assert body["registered_by"] == admin.id


def test_registrar_pago_ignora_registered_by_inyectado_en_el_body(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos2@gmail.com", "AdminPass123", "admin")
    otro_admin = _seed_user("smartgym.qa.admin.otro.pagos2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Pago2").json()["id"]
    client_id = _register_client(client, headers, "smartgym.qa.cliente.pagos2@gmail.com").json()["client"]["id"]
    membership_id = _assign_membership(client, headers, client_id, plan_id)["id"]

    payload = _payment_payload(membership_id)
    payload["registered_by"] = otro_admin.id  # el schema ya no lo acepta; debe ser ignorado

    response = client.post(f"{API}/payments", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["registered_by"] == admin.id


def test_registrar_pago_con_membership_id_inexistente_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos3@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(f"{API}/payments", json=_payment_payload(999999), headers=headers)

    assert response.status_code == 404
    assert "999999" in response.json()["detail"]


def test_registrar_pago_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.pagos4@gmail.com", "ClaveEntrenador123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Pago4").json()["id"]
    client_id = _register_client(client, admin_headers, "smartgym.qa.cliente.pagos4@gmail.com").json()["client"]["id"]
    membership_id = _assign_membership(client, admin_headers, client_id, plan_id)["id"]

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    response = client.post(f"{API}/payments", json=_payment_payload(membership_id), headers=trainer_headers)

    assert response.status_code == 403


def test_listado_de_pagos_como_admin_ve_todos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Pago5").json()["id"]
    client_a_id = _register_client(client, headers, "smartgym.qa.cliente.a.pagos5@gmail.com").json()["client"]["id"]
    client_b_id = _register_client(client, headers, "smartgym.qa.cliente.b.pagos5@gmail.com").json()["client"]["id"]
    membership_a_id = _assign_membership(client, headers, client_a_id, plan_id)["id"]
    membership_b_id = _assign_membership(client, headers, client_b_id, plan_id)["id"]

    client.post(f"{API}/payments", json=_payment_payload(membership_a_id), headers=headers)
    client.post(f"{API}/payments", json=_payment_payload(membership_b_id), headers=headers)

    response = client.get(f"{API}/payments", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_listado_de_pagos_como_entrenador_ve_solo_los_de_sus_clientes(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.pagos6@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.pagos6@gmail.com", "ClaveEntrenadorB123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Pago6").json()["id"]
    client_a_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.a.pagos6@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    client_b_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.b.pagos6@gmail.com", trainer_id=trainer_b.id
    ).json()["client"]["id"]
    membership_a_id = _assign_membership(client, admin_headers, client_a_id, plan_id)["id"]
    membership_b_id = _assign_membership(client, admin_headers, client_b_id, plan_id)["id"]

    client.post(f"{API}/payments", json=_payment_payload(membership_a_id), headers=admin_headers)
    client.post(f"{API}/payments", json=_payment_payload(membership_b_id), headers=admin_headers)

    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    response = client.get(f"{API}/payments", headers=trainer_a_headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["membership_id"] == membership_a_id


def test_cliente_accede_a_su_propio_pago_pero_no_al_de_otro(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.pagos7@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, admin_headers, "Basica Pago7").json()["id"]
    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.pagos7@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.pagos7@gmail.com")
    client_a_id = created_a.json()["client"]["id"]
    client_b_id = created_b.json()["client"]["id"]
    password_a = created_a.json()["temporary_password"]

    membership_a_id = _assign_membership(client, admin_headers, client_a_id, plan_id)["id"]
    membership_b_id = _assign_membership(client, admin_headers, client_b_id, plan_id)["id"]

    payment_a_id = client.post(
        f"{API}/payments", json=_payment_payload(membership_a_id), headers=admin_headers
    ).json()["id"]
    payment_b_id = client.post(
        f"{API}/payments", json=_payment_payload(membership_b_id), headers=admin_headers
    ).json()["id"]

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.pagos7@gmail.com", password_a)

    own = client.get(f"{API}/payments/{payment_a_id}", headers=client_a_headers)
    assert own.status_code == 200

    other = client.get(f"{API}/payments/{payment_b_id}", headers=client_a_headers)
    assert other.status_code == 403
