"""CP19+ -- Planes y servicios extra (Entrega 3, Fase 2, amplia RF004/RF005).

Corre contra una base de datos Postgres real (ver `conftest.py`: `services`
se trunca de forma explicita, `plan_services`/`membership_services`/
`payments`/`payment_items` caen en cascada al truncar
`membership_plans`/`memberships`).

Casos cubiertos:
    19. Eliminar un plan CON membresias contratadas -> se desactiva
        (`is_active = False`), no se borra.
    20. Eliminar un plan SIN membresias -> se elimina de verdad.
    21. Eliminar un servicio CON contrataciones -> se desactiva.
    22. Eliminar un servicio SIN contrataciones -> se elimina de verdad.
    23. Cambiar el precio de un servicio DESPUES de que un cliente ya lo
        contrato no afecta `price_at_purchase` de lo ya contratado.
    24. Contratar un servicio que ya esta incluido en el plan del cliente
        -> 409 (no se puede cobrar aparte algo que ya esta incluido).
    25. Alta/edicion/eliminacion de catalogo (planes y servicios) como
        no-admin -> 403.
    26. `GET /memberships/{id}/services`: `entrenador` ve la lista sin
        `price_at_purchase`; `admin`/`cliente` si lo ven.
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


def _create_service(
    client: TestClient, headers: dict[str, str], name: str, price: str = "250.00", billing_period: str = "mensual"
):
    payload = {
        "name": name,
        "price": price,
        "billing_period": billing_period,
        "description": "Servicio de prueba",
    }
    return client.post(f"{API}/services", json=payload, headers=headers)


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


def test_eliminar_plan_con_membresias_lo_desactiva(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios19@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Serv19").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.servicios19@gmail.com").json()["client"]["id"]
    _assign_membership(client, headers, client_id, plan["id"])

    response = client.delete(f"{API}/membership-plans/{plan['id']}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == plan["id"]
    assert body["is_active"] is False

    # Sigue existiendo en el catalogo (publico), solo desactivado.
    listed = client.get(f"{API}/membership-plans").json()
    assert any(p["id"] == plan["id"] and p["is_active"] is False for p in listed)


def test_eliminar_plan_sin_membresias_lo_elimina(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios20@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Serv20").json()

    response = client.delete(f"{API}/membership-plans/{plan['id']}", headers=headers)
    assert response.status_code == 200

    listed = client.get(f"{API}/membership-plans").json()
    assert all(p["id"] != plan["id"] for p in listed)


def test_eliminar_servicio_con_contrataciones_lo_desactiva(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios21@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Serv21").json()
    service = _create_service(client, headers, "Casillero Serv21").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.servicios21@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, plan["id"])

    client.post(
        f"{API}/memberships/{membership['id']}/services",
        json={"service_id": service["id"]},
        headers=headers,
    )

    response = client.delete(f"{API}/services/{service['id']}", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == service["id"]
    assert body["is_active"] is False


def test_eliminar_servicio_sin_contrataciones_lo_elimina(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios22@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    service = _create_service(client, headers, "Casillero Serv22").json()

    response = client.delete(f"{API}/services/{service['id']}", headers=headers)
    assert response.status_code == 200

    listed = client.get(f"{API}/services").json()
    assert all(s["id"] != service["id"] for s in listed)


def test_cambio_de_precio_de_servicio_no_afecta_lo_ya_contratado(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios23@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Serv23").json()
    service = _create_service(client, headers, "Entrenador Serv23", price="450.00").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.servicios23@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, plan["id"])

    contracted = client.post(
        f"{API}/memberships/{membership['id']}/services",
        json={"service_id": service["id"]},
        headers=headers,
    ).json()
    assert contracted["price_at_purchase"] == "450.00"

    # Sube el precio del catalogo DESPUES de la contratacion.
    client.patch(
        f"{API}/services/{service['id']}",
        json={
            "name": "Entrenador Serv23",
            "price": "600.00",
            "billing_period": "mensual",
            "description": "Precio actualizado",
        },
        headers=headers,
    )

    response = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers)
    body = response.json()
    assert len(body) == 1
    assert body[0]["price_at_purchase"] == "450.00"  # congelado, no 600.00


def test_contratar_servicio_ya_incluido_en_el_plan_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios24@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Serv24").json()
    service = _create_service(client, headers, "Casillero Serv24").json()
    client.post(
        f"{API}/membership-plans/{plan['id']}/services",
        json={"service_id": service["id"]},
        headers=headers,
    )

    client_id = _register_client(client, headers, "smartgym.qa.cliente.servicios24@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, plan["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/services",
        json={"service_id": service["id"]},
        headers=headers,
    )

    assert response.status_code == 409


def test_catalogo_de_planes_y_servicios_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios25@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.servicios25@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    plan = _create_plan(client, admin_headers, "Basica Serv25").json()
    service = _create_service(client, admin_headers, "Casillero Serv25").json()

    assert _create_plan(client, trainer_headers, "Intento Serv25").status_code == 403
    assert (
        client.patch(
            f"{API}/membership-plans/{plan['id']}",
            json={"name": "x", "price": "1.00", "duration_days": 1, "benefits": []},
            headers=trainer_headers,
        ).status_code
        == 403
    )
    assert client.delete(f"{API}/membership-plans/{plan['id']}", headers=trainer_headers).status_code == 403

    assert (
        client.post(
            f"{API}/services",
            json={"name": "x", "price": "1.00", "billing_period": "unico"},
            headers=trainer_headers,
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"{API}/services/{service['id']}",
            json={"name": "x", "price": "1.00", "billing_period": "unico"},
            headers=trainer_headers,
        ).status_code
        == 403
    )
    assert client.delete(f"{API}/services/{service['id']}", headers=trainer_headers).status_code == 403


def test_entrenador_ve_extras_sin_precio_admin_y_cliente_si(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.servicios26@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.servicios26@gmail.com", "ClaveEntrenador123", "entrenador")

    plan = _create_plan(client, admin_headers, "Basica Serv26").json()
    service = _create_service(client, admin_headers, "Entrenador Serv26", price="450.00").json()
    created_client = _register_client(
        client, admin_headers, "smartgym.qa.cliente.servicios26@gmail.com", trainer_id=trainer.id
    )
    client_id = created_client.json()["client"]["id"]
    password = created_client.json()["temporary_password"]
    membership = _assign_membership(client, admin_headers, client_id, plan["id"])

    client.post(
        f"{API}/memberships/{membership['id']}/services",
        json={"service_id": service["id"]},
        headers=admin_headers,
    )

    admin_view = client.get(f"{API}/memberships/{membership['id']}/services", headers=admin_headers).json()
    assert admin_view[0]["price_at_purchase"] == "450.00"

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    trainer_view = client.get(f"{API}/memberships/{membership['id']}/services", headers=trainer_headers).json()
    assert "price_at_purchase" not in trainer_view[0]

    cliente_headers = _auth_headers(client, "smartgym.qa.cliente.servicios26@gmail.com", password)
    cliente_view = client.get(f"{API}/memberships/{membership['id']}/services", headers=cliente_headers).json()
    assert cliente_view[0]["price_at_purchase"] == "450.00"
