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

Tablero de membresias activas + renovar (Entrega 3, ajuste de UX de
"Membresias" -- ver DECISIONES.md):
    11. Tablero como admin: indicadores (total, por vencer, ingresos del
        mes) + tabla.
    12. Tablero como entrenador: solo sus clientes, sin ingresos.
    13. Tablero como cliente -> 403.
    14. Filtros por plan y por nombre acotan la tabla, no los indicadores.

BUG-12 (ver DECISIONES.md, entrada BUG-12) -- "Renovar" pasa a cobrar en la
misma operacion, con ventana de 7 dias, y se puede deshacer:
    15. Renovar dentro de la ventana extiende `end_date` Y cobra el pago.
    16. Renovar una membresia vencida la reactiva desde hoy.
    17. Renovar fuera de la ventana -> 409, sin cambios (atomico).
    18. Renovar dos veces seguidas -> la segunda falla (409).
    19. Renovar como no-admin -> 403.
    20. Renovar una membresia inexistente -> 404.
    21. Deshacer una renovacion restaura la fecha anterior y anula el pago.
    22. Deshacer una renovacion ya deshecha -> 409.
    23. Deshacer con una renovacion posterior -> 409.
    24. Deshacer como no-admin -> 403.
    25. Un pago anulado no cuenta en los ingresos del mes.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text
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


def _assign_membership(
    client: TestClient,
    headers: dict[str, str],
    client_id: int,
    plan_id: int,
    end_date_override: date | None = None,
) -> dict:
    today = date.today()
    response = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (end_date_override or (today + timedelta(days=30))).isoformat(),
            "status": "activa",
        },
        headers=headers,
    )
    return response.json()


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


def test_listar_planes_sin_autenticacion_es_publico(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.membresias.publico@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    _create_plan(client, admin_headers, "Publico Memb1")

    response = client.get(f"{API}/membership-plans")

    assert response.status_code == 200
    assert any(p["name"] == "Publico Memb1" for p in response.json())


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


# --- Tablero de membresias activas (Entrega 3, ajuste de UX "Membresias") --


def test_tablero_de_membresias_activas_como_admin(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.tablero1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_id = _create_plan(client, headers, "Basica Tablero1").json()["id"]
    client_a_id = _register_client(client, headers, "smartgym.qa.cliente.a.tablero1@gmail.com").json()["client"]["id"]
    client_b_id = _register_client(client, headers, "smartgym.qa.cliente.b.tablero1@gmail.com").json()["client"]["id"]

    today = date.today()
    # A: vence en 3 dias (dentro de la ventana de 7). B: vence en 20 (fuera).
    membership_a = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_a_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=3)).isoformat(),
            "status": "activa",
        },
        headers=headers,
    ).json()
    client.post(
        f"{API}/memberships",
        json={
            "client_id": client_b_id,
            "plan_id": plan_id,
            "start_date": today.isoformat(),
            "end_date": (today + timedelta(days=20)).isoformat(),
            "status": "activa",
        },
        headers=headers,
    )

    client.post(
        f"{API}/payments",
        json={
            "membership_id": membership_a["id"],
            "amount": "399.00",
            "payment_date": datetime.now(timezone.utc).isoformat(),
            "method": "efectivo",
            "status": "completado",
        },
        headers=headers,
    )

    response = client.get(f"{API}/memberships/board", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["indicators"]["total_active"] == 2
    assert body["indicators"]["expiring_soon"] == 1
    assert Decimal(body["indicators"]["monthly_revenue"]) == Decimal("399.00")
    assert len(body["items"]) == 2
    expiring_row = next(r for r in body["items"] if r["membership_id"] == membership_a["id"])
    assert expiring_row["expiring_soon"] is True
    assert expiring_row["days_remaining"] == 3


def test_tablero_como_entrenador_ve_solo_sus_clientes_y_sin_ingresos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.tablero2@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.tablero2@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.tablero2@gmail.com", "ClaveEntrenadorB123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Tablero2").json()["id"]
    client_a_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.a.tablero2@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    client_b_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.b.tablero2@gmail.com", trainer_id=trainer_b.id
    ).json()["client"]["id"]

    for cid in (client_a_id, client_b_id):
        _assign_membership(client, admin_headers, cid, plan_id)

    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    response = client.get(f"{API}/memberships/board", headers=trainer_a_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["indicators"]["total_active"] == 1
    assert body["indicators"]["monthly_revenue"] is None
    assert len(body["items"]) == 1
    assert body["items"][0]["client_id"] == client_a_id


def test_tablero_como_cliente_devuelve_403(client: TestClient) -> None:
    cliente = _seed_user("smartgym.qa.cliente.tablero3@gmail.com", "ClaveCliente123", "cliente")
    headers = _auth_headers(client, cliente.email, "ClaveCliente123")

    response = client.get(f"{API}/memberships/board", headers=headers)

    assert response.status_code == 403


def test_tablero_filtra_por_plan_y_por_nombre_sin_afectar_indicadores(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.tablero4@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_a_id = _create_plan(client, headers, "Basica Tablero4").json()["id"]
    plan_b_id = _create_plan(client, headers, "VIP Tablero4").json()["id"]
    client_a_id = _register_client(
        client, headers, "smartgym.qa.cliente.ana.tablero4@gmail.com", full_name="Ana Perez"
    ).json()["client"]["id"]
    client_b_id = _register_client(
        client, headers, "smartgym.qa.cliente.luis.tablero4@gmail.com", full_name="Luis Gomez"
    ).json()["client"]["id"]

    _assign_membership(client, headers, client_a_id, plan_a_id)
    _assign_membership(client, headers, client_b_id, plan_b_id)

    by_plan = client.get(f"{API}/memberships/board?plan_id={plan_a_id}", headers=headers).json()
    assert by_plan["indicators"]["total_active"] == 2  # indicadores SIN filtrar
    assert len(by_plan["items"]) == 1
    assert by_plan["items"][0]["client_id"] == client_a_id

    by_name = client.get(f"{API}/memberships/board?q=ana", headers=headers).json()
    assert len(by_name["items"]) == 1
    assert by_name["items"][0]["client_id"] == client_a_id


def _force_membership_end_date(membership_id: int, new_end_date: date, new_status: str = "activa") -> None:
    """Pone `end_date`/`status` directo en la base (sin pasar por la API,
    mismo patron que `_seed_user`) -- usado SOLO para simular "paso el
    tiempo" en pruebas de BUG-12 (ej. que ya haya una renovacion
    posterior), sin tener que esperar dias reales."""
    session: Session = SessionLocal()
    try:
        session.execute(
            text("UPDATE memberships SET end_date = :end_date, status = :status WHERE id = :id"),
            {"end_date": new_end_date, "status": new_status, "id": membership_id},
        )
        session.commit()
    finally:
        session.close()


def test_renovar_membresia_extiende_la_vigencia_y_cobra(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Renovar1").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.renovar1@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=3))

    response = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    expected_end = date.fromisoformat(membership["end_date"]) + timedelta(days=plan["duration_days"])
    assert body["membership"]["end_date"] == expected_end.isoformat()
    assert body["membership"]["status"] == "activa"
    assert Decimal(body["payment"]["amount"]) == Decimal(plan["price"])
    assert body["payment"]["method"] == "efectivo"
    assert body["payment"]["status"] == "completado"
    assert body["renewal"]["previous_end_date"] == membership["end_date"]
    assert body["renewal"]["new_end_date"] == expected_end.isoformat()
    assert body["renewal"]["reversed_at"] is None


def test_renovar_membresia_vencida_la_reactiva_desde_hoy(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Renovar2").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.renovar2@gmail.com").json()["client"]["id"]

    today = date.today()
    membership = client.post(
        f"{API}/memberships",
        json={
            "client_id": client_id,
            "plan_id": plan["id"],
            "start_date": (today - timedelta(days=40)).isoformat(),
            "end_date": (today - timedelta(days=10)).isoformat(),
            "status": "vencida",
        },
        headers=headers,
    ).json()

    response = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "tarjeta"}, headers=headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["membership"]["status"] == "activa"
    assert body["membership"]["end_date"] == (today + timedelta(days=plan["duration_days"])).isoformat()
    assert body["renewal"]["previous_status"] == "vencida"


def test_renovar_fuera_de_la_ventana_devuelve_409_y_no_cambia_nada(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Renovar5").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.renovar5@gmail.com").json()["client"]["id"]
    # `_assign_membership` por defecto vence en 30 dias -- fuera de la ventana de 7.
    membership = _assign_membership(client, headers, client_id, plan["id"])

    response = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    )

    assert response.status_code == 409
    assert "vence en" in response.json()["detail"].lower() or "7" in response.json()["detail"]

    sin_cambios = client.get(f"{API}/memberships/{membership['id']}", headers=headers).json()
    assert sin_cambios["end_date"] == membership["end_date"]
    pagos = client.get(f"{API}/payments?membership_id={membership['id']}", headers=headers).json()
    assert pagos == []


def test_renovar_dos_veces_seguidas_la_segunda_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar6@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Renovar6").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.renovar6@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=2))

    first = client.post(f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers)
    assert first.status_code == 200

    second = client.post(f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers)
    assert second.status_code == 409

    pagos = client.get(f"{API}/payments?membership_id={membership['id']}", headers=headers).json()
    assert len(pagos) == 1


def test_renovar_membresia_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.renovar3@gmail.com", "ClaveEntrenador123", "entrenador")

    plan_id = _create_plan(client, admin_headers, "Basica Renovar3").json()["id"]
    client_id = _register_client(client, admin_headers, "smartgym.qa.cliente.renovar3@gmail.com").json()["client"]["id"]
    membership = _assign_membership(client, admin_headers, client_id, plan_id)

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    response = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=trainer_headers
    )

    assert response.status_code == 403


def test_renovar_membresia_inexistente_falla(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.renovar4@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(f"{API}/memberships/999999/renew", json={"method": "efectivo"}, headers=headers)

    assert response.status_code == 404


def test_deshacer_renovacion_restaura_fecha_y_anula_pago(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.deshacer1@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Deshacer1").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.deshacer1@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=3))
    original_end_date = membership["end_date"]

    renewed = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    ).json()
    renewal_id = renewed["renewal"]["id"]
    payment_id = renewed["payment"]["id"]

    response = client.post(
        f"{API}/memberships/renewals/{renewal_id}/undo",
        json={"reason": "Click equivocado, el cliente no pidio renovar"},
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["membership"]["end_date"] == original_end_date
    assert body["membership"]["status"] == "activa"
    assert body["payment"]["id"] == payment_id
    assert body["payment"]["status"] == "anulado"
    assert body["renewal"]["reversed_at"] is not None
    assert body["renewal"]["reversed_reason"] == "Click equivocado, el cliente no pidio renovar"

    sin_cambios = client.get(f"{API}/memberships/{membership['id']}", headers=headers).json()
    assert sin_cambios["end_date"] == original_end_date

    bitacora = client.get(f"{API}/audit-logs", headers=headers).json()
    acciones = [e["action"] for e in bitacora]
    assert "renovar_membresia" in acciones
    assert "deshacer_renovacion_membresia" in acciones


def test_deshacer_renovacion_ya_deshecha_devuelve_409(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.deshacer2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Deshacer2").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.deshacer2@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=3))

    renewed = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    ).json()
    renewal_id = renewed["renewal"]["id"]

    primero = client.post(
        f"{API}/memberships/renewals/{renewal_id}/undo", json={"reason": "primer intento"}, headers=headers
    )
    assert primero.status_code == 200

    segundo = client.post(
        f"{API}/memberships/renewals/{renewal_id}/undo", json={"reason": "segundo intento"}, headers=headers
    )
    assert segundo.status_code == 409


def test_deshacer_renovacion_con_renovacion_posterior_devuelve_409(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.deshacer3@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Deshacer3").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.deshacer3@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=3))

    primera_renovacion = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    ).json()
    primer_renewal_id = primera_renovacion["renewal"]["id"]

    # Simula que paso el tiempo (la membresia vuelve a estar en ventana) para
    # poder renovar una segunda vez sin esperar dias reales.
    _force_membership_end_date(membership["id"], today + timedelta(days=2))
    segunda_renovacion = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    )
    assert segunda_renovacion.status_code == 200

    response = client.post(
        f"{API}/memberships/renewals/{primer_renewal_id}/undo",
        json={"reason": "intenta deshacer la vieja"},
        headers=headers,
    )

    assert response.status_code == 409


def test_deshacer_renovacion_como_no_admin_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.deshacer4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.deshacer4@gmail.com", "ClaveEntrenador123", "entrenador")

    plan = _create_plan(client, admin_headers, "Basica Deshacer4").json()
    client_id = _register_client(client, admin_headers, "smartgym.qa.cliente.deshacer4@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(
        client, admin_headers, client_id, plan["id"], end_date_override=today + timedelta(days=3)
    )
    renewed = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=admin_headers
    ).json()
    renewal_id = renewed["renewal"]["id"]

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    response = client.post(
        f"{API}/memberships/renewals/{renewal_id}/undo", json={"reason": "no deberia poder"}, headers=trainer_headers
    )

    assert response.status_code == 403


def test_pago_anulado_no_cuenta_en_ingresos_del_mes(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.deshacer5@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, admin.email, "AdminPass123")

    plan = _create_plan(client, headers, "Basica Deshacer5").json()
    client_id = _register_client(client, headers, "smartgym.qa.cliente.deshacer5@gmail.com").json()["client"]["id"]
    today = date.today()
    membership = _assign_membership(client, headers, client_id, plan["id"], end_date_override=today + timedelta(days=3))

    renewed = client.post(
        f"{API}/memberships/{membership['id']}/renew", json={"method": "efectivo"}, headers=headers
    ).json()

    before_undo = client.get(f"{API}/memberships/board", headers=headers).json()
    assert Decimal(before_undo["indicators"]["monthly_revenue"]) == Decimal(plan["price"])

    client.post(
        f"{API}/memberships/renewals/{renewed['renewal']['id']}/undo",
        json={"reason": "no debe contar en ingresos"},
        headers=headers,
    )

    after_undo = client.get(f"{API}/memberships/board", headers=headers).json()
    assert Decimal(after_undo["indicators"]["monthly_revenue"]) == Decimal("0")
