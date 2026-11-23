"""Cambio de plan y su efecto en servicios extra (amplia RF004/RF005 de
nuevo) -- Entrega 3.

Corre contra una base de datos Postgres real (ver `conftest.py`). Casos
cubiertos:

    1. Subir de plan con un extra incluido en el plan nuevo: el extra
       queda cancelado (`status = "cancelado_por_cambio_de_plan"`,
       `end_date = hoy`) y deja de ofrecerse para cobrar.
    2. Subir de plan con un extra NO incluido en el plan nuevo: se
       conserva tal cual (sigue "activa").
    3. Bajar de plan: los servicios que el plan viejo incluia y el nuevo
       no, se reportan como "contratables" pero NUNCA se agregan solos
       ni se cobran (no se crea ninguna `MembershipService` para ellos).
    4. El historial de pagos y de extras no se borra -- sigue disponible
       despues del cambio.
    5. La transaccion es atomica: si el paso de validacion falla (plan
       destino inexistente), nada cambia (ni el plan de la membresia ni
       el status de los extras).
    6. Entrenador y Cliente no pueden cambiar el plan (403), ni
       previsualizarlo.
    7. Preview no persiste nada.
    8. Confirmar genera un AuditLog y una Notification para el cliente.
    9. Plan igual al actual -> 400. Plan destino desactivado -> 400.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

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
        "emergency_contact_name": "Alguien",
        "emergency_contact_phone": "555-0000",
    }
    return client.post(f"{API}/clients", json=payload, headers=headers)


def _create_plan(client: TestClient, headers: dict[str, str], name: str = "Basica", price: str = "399.00"):
    payload = {
        "name": name,
        "price": price,
        "duration_days": 30,
        "description": "Plan de prueba",
        "benefits": [],
    }
    return client.post(f"{API}/membership-plans", json=payload, headers=headers)


def _create_service(
    client: TestClient, headers: dict[str, str], name: str, price: str = "250.00", billing_period: str = "mensual"
):
    payload = {"name": name, "price": price, "billing_period": billing_period, "description": None}
    return client.post(f"{API}/services", json=payload, headers=headers)


def _include_service_in_plan(client: TestClient, headers: dict[str, str], plan_id: int, service_id: int):
    return client.post(
        f"{API}/membership-plans/{plan_id}/services", json={"service_id": service_id}, headers=headers
    )


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


def _contract_service(client: TestClient, headers: dict[str, str], membership_id: int, service_id: int):
    return client.post(
        f"{API}/memberships/{membership_id}/services", json={"service_id": service_id}, headers=headers
    )


def test_subir_de_plan_cancela_el_extra_ya_incluido_en_el_nuevo(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP1", "399.00").json()
    premium = _create_plan(client, headers, "Premium CP1", "999.00").json()
    casillero = _create_service(client, headers, "Casillero CP1", price="120.00").json()
    _include_service_in_plan(client, headers, premium["id"], casillero["id"])

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan1@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])
    contracted = _contract_service(client, headers, membership["id"], casillero["id"]).json()

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": premium["id"], "notes": "Sube a Premium"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["old_plan_id"] == basica["id"]
    assert body["new_plan_id"] == premium["id"]
    assert body["price_difference"] == "600.00"
    assert len(body["cancelled_extras"]) == 1
    assert body["cancelled_extras"][0]["membership_service_id"] == contracted["id"]
    assert body["cancelled_extras_total"] == "120.00"
    assert body["kept_extras"] == []

    extras = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    cancelled = next(e for e in extras if e["id"] == contracted["id"])
    assert cancelled["status"] == "cancelado_por_cambio_de_plan"
    assert cancelled["end_date"] == date.today().isoformat()

    membership_after = client.get(f"{API}/memberships/{membership['id']}", headers=headers).json()
    assert membership_after["plan_id"] == premium["id"]


def test_subir_de_plan_conserva_extras_no_incluidos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP2", "399.00").json()
    vip = _create_plan(client, headers, "VIP CP2", "649.00").json()
    entrenador_asignado = _create_service(client, headers, "Entrenador asignado CP2", price="450.00").json()
    # El servicio NO se incluye en ningun plan -- sigue siendo un extra puro.

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan2@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])
    contracted = _contract_service(client, headers, membership["id"], entrenador_asignado["id"]).json()

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": vip["id"]},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["cancelled_extras"] == []
    assert len(body["kept_extras"]) == 1
    assert body["kept_extras"][0]["membership_service_id"] == contracted["id"]

    extras = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    kept = next(e for e in extras if e["id"] == contracted["id"])
    assert kept["status"] == "activa"


def test_bajar_de_plan_no_agrega_ni_cobra_los_servicios_que_se_dejan_de_incluir(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan3@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    premium = _create_plan(client, headers, "Premium CP3", "999.00").json()
    basica = _create_plan(client, headers, "Basica CP3", "399.00").json()
    casillero = _create_service(client, headers, "Casillero CP3", price="120.00").json()
    _include_service_in_plan(client, headers, premium["id"], casillero["id"])
    # Basica NO incluye casillero -- es una bajada real.

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan3@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, premium["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": basica["id"]},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["newly_contractable_services"]) == 1
    assert body["newly_contractable_services"][0]["service_id"] == casillero["id"]

    # No se creo ninguna MembershipService -- sigue sin extras contratados.
    extras = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    assert extras == []


def test_historial_de_pagos_y_extras_no_se_borra(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan4@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP4", "399.00").json()
    premium = _create_plan(client, headers, "Premium CP4", "999.00").json()
    casillero = _create_service(client, headers, "Casillero CP4", price="120.00").json()
    _include_service_in_plan(client, headers, premium["id"], casillero["id"])

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan4@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])
    contracted = _contract_service(client, headers, membership["id"], casillero["id"]).json()

    payment = client.post(
        f"{API}/payments",
        json={
            "membership_id": membership["id"],
            "amount": "399.00",
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "method": "efectivo",
            "status": "completado",
        },
        headers=headers,
    ).json()

    client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": premium["id"]},
        headers=headers,
    )

    # El pago ya hecho sigue intacto.
    fetched_payment = client.get(f"{API}/payments/{payment['id']}", headers=headers).json()
    assert fetched_payment["amount"] == "399.00"

    # El extra cancelado sigue existiendo (no se borro), con su historial.
    extras = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    assert any(e["id"] == contracted["id"] for e in extras)


def test_cambio_de_plan_es_atomico_si_el_plan_destino_no_existe(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP5", "399.00").json()
    service = _create_service(client, headers, "Casillero CP5", price="120.00").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan5@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])
    contracted = _contract_service(client, headers, membership["id"], service["id"]).json()

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": 999999},
        headers=headers,
    )
    assert response.status_code == 404

    membership_after = client.get(f"{API}/memberships/{membership['id']}", headers=headers).json()
    assert membership_after["plan_id"] == basica["id"]

    extras_after = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    assert extras_after[0]["id"] == contracted["id"]
    assert extras_after[0]["status"] == "activa"


def test_entrenador_y_cliente_no_pueden_cambiar_ni_previsualizar_el_plan(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.cambioplan6@gmail.com", "ClaveEntrenador123", "entrenador")

    basica = _create_plan(client, admin_headers, "Basica CP6", "399.00").json()
    vip = _create_plan(client, admin_headers, "VIP CP6", "649.00").json()
    created_client = _register_client(
        client, admin_headers, "smartgym.qa.cliente.cambioplan6@gmail.com", trainer_id=trainer.id
    )
    client_id = created_client.json()["client"]["id"]
    password = created_client.json()["temporary_password"]
    membership = _assign_membership(client, admin_headers, client_id, basica["id"])

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    cliente_headers = _auth_headers(client, "smartgym.qa.cliente.cambioplan6@gmail.com", password)

    for headers in (trainer_headers, cliente_headers):
        preview = client.post(
            f"{API}/memberships/{membership['id']}/change-plan/preview",
            json={"new_plan_id": vip["id"]},
            headers=headers,
        )
        assert preview.status_code == 403

        confirm = client.post(
            f"{API}/memberships/{membership['id']}/change-plan",
            json={"new_plan_id": vip["id"]},
            headers=headers,
        )
        assert confirm.status_code == 403

    membership_after = client.get(f"{API}/memberships/{membership['id']}", headers=admin_headers).json()
    assert membership_after["plan_id"] == basica["id"]


def test_preview_no_persiste_nada(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan7@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP7", "399.00").json()
    premium = _create_plan(client, headers, "Premium CP7", "999.00").json()
    service = _create_service(client, headers, "Casillero CP7", price="120.00").json()
    _include_service_in_plan(client, headers, premium["id"], service["id"])

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan7@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])
    contracted = _contract_service(client, headers, membership["id"], service["id"]).json()

    preview = client.post(
        f"{API}/memberships/{membership['id']}/change-plan/preview",
        json={"new_plan_id": premium["id"]},
        headers=headers,
    )
    assert preview.status_code == 200
    assert len(preview.json()["cancelled_extras"]) == 1

    membership_after = client.get(f"{API}/memberships/{membership['id']}", headers=headers).json()
    assert membership_after["plan_id"] == basica["id"]

    extras_after = client.get(f"{API}/memberships/{membership['id']}/services", headers=headers).json()
    assert extras_after[0]["id"] == contracted["id"]
    assert extras_after[0]["status"] == "activa"


def test_confirmar_genera_auditoria_y_notifica_al_cliente(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan8@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP8", "399.00").json()
    vip = _create_plan(client, headers, "VIP CP8", "649.00").json()
    created_client = _register_client(client, headers, "smartgym.qa.cliente.cambioplan8@gmail.com")
    client_id = created_client.json()["client"]["id"]
    client_user_id = created_client.json()["client"]["user_id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan",
        json={"new_plan_id": vip["id"], "notes": "Acuerdo: sin reembolso"},
        headers=headers,
    )
    assert response.status_code == 200

    audit = client.get(f"{API}/audit-logs?limit=5", headers=headers).json()
    entry = next(a for a in audit if a["action"] == "cambio_de_plan" and a["entity_id"] == str(membership["id"]))
    assert "Acuerdo: sin reembolso" in entry["details"]

    notifications = client.get(f"{API}/notifications/users/{client_user_id}", headers=headers).json()
    assert any(n["type"] == "plan_cambiado" for n in notifications)


def test_cambiar_al_mismo_plan_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan9@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP9", "399.00").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan9@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan/preview",
        json={"new_plan_id": basica["id"]},
        headers=headers,
    )
    assert response.status_code == 400


def test_cambiar_a_un_plan_desactivado_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.cambioplan10@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    basica = _create_plan(client, headers, "Basica CP10", "399.00").json()
    descontinuado = _create_plan(client, headers, "Descontinuado CP10", "299.00").json()
    client.delete(f"{API}/membership-plans/{descontinuado['id']}", headers=headers)  # sin contrataciones -> elimina

    # Para desactivar (no eliminar) el plan descontinuado, le asigna una
    # membresia primero y luego intenta reusarlo como destino de otro cliente.
    other_client_id = _register_client(
        client, headers, "smartgym.qa.cliente.otro.cambioplan10@gmail.com"
    ).json()["client"]["id"]
    descontinuado2 = _create_plan(client, headers, "Descontinuado2 CP10", "299.00").json()
    _assign_membership(client, headers, other_client_id, descontinuado2["id"])
    client.delete(f"{API}/membership-plans/{descontinuado2['id']}", headers=headers)  # con contratacion -> desactiva

    client_id = _register_client(client, headers, "smartgym.qa.cliente.cambioplan10@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, headers, client_id, basica["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/change-plan/preview",
        json={"new_plan_id": descontinuado2["id"]},
        headers=headers,
    )
    assert response.status_code == 400
