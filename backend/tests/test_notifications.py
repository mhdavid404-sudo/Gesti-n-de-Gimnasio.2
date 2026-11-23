"""CP del modulo Vencimientos/Notificaciones (RF006) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas). `notifications` no necesita
TRUNCATE explicito: cae en cascada al truncar `users`
(`notifications.user_id -> users.id ON DELETE CASCADE`, ver nota agregada
en `conftest.py`).

Casos cubiertos:
    1. Detectar una membresia ya vencida (`end_date` pasada) -> pasa a
       `status="vencida"` y genera una `Notification` tipo
       `membresia_vencida` para el usuario (cliente) correcto.
    2. Detectar una membresia por vencer (`end_date` dentro de la ventana)
       -> genera `Notification` tipo `membresia_por_vencer` SIN cambiar el
       `status` (sigue "activa").
    3. Correr la deteccion dos veces seguidas sobre el mismo caso "por
       vencer" -> NO se duplica la notificacion (sigue habiendo solo una).
    4. `POST /memberships/detect-expiring` como no-admin -> 403.
    5. `GET /memberships/expiring` refleja vencidas/por vencer SIN
       necesidad de haber corrido el POST antes.
    6. `GET /notifications/users/{id}`: el propio usuario -> 200; otro
       usuario sin ser admin -> 403.
    7. `POST /notifications/{id}/read` marca correctamente `is_read`.
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


def _register_client(client: TestClient, headers: dict[str, str], email: str) -> dict:
    payload = {
        "email": email,
        "full_name": "Cliente de prueba",
        "trainer_id": None,
        "phone": "5512345678",
        "birth_date": "1995-05-20",
        "address": "Calle Falsa 123",
        "emergency_contact_name": "Alguien",
        "emergency_contact_phone": "555-0000",
    }
    return client.post(f"{API}/clients", json=payload, headers=headers).json()


def _create_plan(client: TestClient, headers: dict[str, str], name: str) -> int:
    payload = {
        "name": name,
        "price": "399.00",
        "duration_days": 30,
        "description": "Plan de acceso basico",
        "benefits": ["Acceso a area de pesas"],
    }
    return client.post(f"{API}/membership-plans", json=payload, headers=headers).json()["id"]


def _assign_membership(
    client: TestClient,
    headers: dict[str, str],
    client_id: int,
    plan_id: int,
    start_date: date,
    end_date: date,
    status: str = "activa",
) -> dict:
    response = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": status,
        },
        headers=headers,
    )
    return response.json()


def _setup_client_with_membership(
    client: TestClient,
    admin_headers: dict[str, str],
    plan_id: int,
    tag: str,
    start_date: date,
    end_date: date,
    status: str = "activa",
) -> tuple[int, int, int]:
    """Da de alta un cliente nuevo con una membresia con las fechas dadas.

    Devuelve (membership_id, client_id, user_id_del_cliente).
    """
    created_client = _register_client(client, admin_headers, f"smartgym.qa.cliente.{tag}@gmail.com")
    client_id = created_client["client"]["id"]
    user_id = created_client["client"]["user_id"]
    membership = _assign_membership(client, admin_headers, client_id, plan_id, start_date, end_date, status)
    return membership["id"], client_id, user_id


def test_deteccion_marca_membresia_vencida_y_notifica_al_usuario_correcto(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_plan(client, headers, "Basica Notif1")

    today = date.today()
    membership_id, _client_id, user_id = _setup_client_with_membership(
        client, headers, plan_id, "notif1",
        start_date=today - timedelta(days=60),
        end_date=today - timedelta(days=5),
    )

    response = client.post(f"{API}/memberships/detect-expiring", headers=headers)
    assert response.status_code == 200
    affected = response.json()
    assert any(m["id"] == membership_id and m["status"] == "vencida" for m in affected)

    membership_after = client.get(f"{API}/memberships/{membership_id}", headers=headers).json()
    assert membership_after["status"] == "vencida"

    notifications = client.get(f"{API}/notifications/users/{user_id}", headers=headers).json()
    assert any(n["type"] == "membresia_vencida" for n in notifications)


def test_deteccion_de_membresia_por_vencer_notifica_sin_cambiar_status(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_plan(client, headers, "Basica Notif2")

    today = date.today()
    membership_id, _client_id, user_id = _setup_client_with_membership(
        client, headers, plan_id, "notif2",
        start_date=today - timedelta(days=20),
        end_date=today + timedelta(days=3),
    )

    response = client.post(f"{API}/memberships/detect-expiring", headers=headers)
    assert response.status_code == 200
    affected = response.json()
    assert any(m["id"] == membership_id for m in affected)

    membership_after = client.get(f"{API}/memberships/{membership_id}", headers=headers).json()
    assert membership_after["status"] == "activa"

    notifications = client.get(f"{API}/notifications/users/{user_id}", headers=headers).json()
    por_vencer = [n for n in notifications if n["type"] == "membresia_por_vencer"]
    assert len(por_vencer) == 1


def test_deteccion_repetida_de_por_vencer_no_duplica_la_notificacion(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif3@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_plan(client, headers, "Basica Notif3")

    today = date.today()
    _membership_id, _client_id, user_id = _setup_client_with_membership(
        client, headers, plan_id, "notif3",
        start_date=today - timedelta(days=20),
        end_date=today + timedelta(days=3),
    )

    client.post(f"{API}/memberships/detect-expiring", headers=headers)
    client.post(f"{API}/memberships/detect-expiring", headers=headers)

    notifications = client.get(f"{API}/notifications/users/{user_id}", headers=headers).json()
    por_vencer = [n for n in notifications if n["type"] == "membresia_por_vencer"]
    assert len(por_vencer) == 1


def test_detect_expiring_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.notif4@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    _create_plan(client, admin_headers, "Basica Notif4")

    response = client.post(f"{API}/memberships/detect-expiring", headers=trainer_headers)
    assert response.status_code == 403


def test_get_expiring_refleja_vencidas_y_por_vencer_sin_correr_el_post_antes(client: TestClient) -> None:
    """`GET /memberships/expiring` no depende de haber corrido
    `POST /memberships/detect-expiring` antes: lee el `status` tal como
    esta persistido (aqui, "vencida" se asigna directo al crear la
    membresia, sin pasar por el flujo de deteccion) y calcula "por vencer"
    siempre al vuelo sobre una membresia que sigue "activa"."""
    admin = _seed_user("smartgym.qa.admin.notif5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_plan(client, headers, "Basica Notif5")

    today = date.today()
    # Membresia con status "vencida" asignado directamente (no via POST de
    # deteccion) -- GET /expiring debe reflejarla de todas formas, porque
    # lee el status ya persistido, igual que el criterio del frontend.
    vencida_id, _, _ = _setup_client_with_membership(
        client, headers, plan_id, "notif5a",
        start_date=today - timedelta(days=60),
        end_date=today - timedelta(days=5),
        status="vencida",
    )
    # Membresia por vencer dentro de la ventana default (7 dias).
    por_vencer_id, _, _ = _setup_client_with_membership(
        client, headers, plan_id, "notif5b",
        start_date=today - timedelta(days=20),
        end_date=today + timedelta(days=3),
    )
    # Membresia sana, lejos de vencer -- no debe aparecer.
    sana_id, _, _ = _setup_client_with_membership(
        client, headers, plan_id, "notif5c",
        start_date=today - timedelta(days=5),
        end_date=today + timedelta(days=60),
    )

    response = client.get(f"{API}/memberships/expiring", headers=headers)
    assert response.status_code == 200
    ids = {m["id"] for m in response.json()}

    assert vencida_id in ids
    assert por_vencer_id in ids
    assert sana_id not in ids


def test_get_notifications_de_otro_usuario_sin_ser_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.notif6@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.notif6@gmail.com")
    user_a_id = created_a["client"]["user_id"]
    user_b_id = created_b["client"]["user_id"]
    password_a = created_a["temporary_password"]

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.notif6@gmail.com", password_a)

    own = client.get(f"{API}/notifications/users/{user_a_id}", headers=client_a_headers)
    assert own.status_code == 200

    other = client.get(f"{API}/notifications/users/{user_b_id}", headers=client_a_headers)
    assert other.status_code == 403

    # Admin si puede ver las notificaciones de cualquier usuario.
    as_admin = client.get(f"{API}/notifications/users/{user_b_id}", headers=admin_headers)
    assert as_admin.status_code == 200


def test_marcar_notificacion_como_leida(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.notif7@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_plan(client, headers, "Basica Notif7")

    today = date.today()
    _membership_id, _client_id, user_id = _setup_client_with_membership(
        client, headers, plan_id, "notif7",
        start_date=today - timedelta(days=60),
        end_date=today - timedelta(days=5),
    )

    client.post(f"{API}/memberships/detect-expiring", headers=headers)
    notifications = client.get(f"{API}/notifications/users/{user_id}", headers=headers).json()
    notification_id = notifications[0]["id"]
    assert notifications[0]["is_read"] is False

    response = client.post(f"{API}/notifications/{notification_id}/read", headers=headers)
    assert response.status_code == 200
    assert response.json()["is_read"] is True
