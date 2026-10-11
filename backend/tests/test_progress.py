"""CP del modulo Progreso Corporal (RF010, RF011) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas). `body_progress` no necesita
TRUNCATE explicito: cae en cascada al truncar `client_profiles`.

A diferencia de `test_routines.py`/`test_diets.py`, este modulo no tiene
ningun campo de autoria (`created_by`/`assigned_by`) que verificar --
`BodyProgress` es solo peso/medidas/fecha ligadas a un `client_id`, sin
invariante de rol de creador. Casos cubiertos:
    1. Registrar progreso como admin -> 201.
    2. Registrar progreso para cliente ajeno como entrenador -> 403.
    3. Registrar progreso para `client_id` inexistente -> 404.
    4. Registrar como `cliente` -> 403 (no tiene esta accion).
    5. Timeline como admin ve cualquiera.
    6. Timeline como entrenador ve solo el de sus clientes (403 si no).
    7. Timeline como cliente ve lo propio pero no lo de otro (403).
"""

from __future__ import annotations

from datetime import date

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


def _register_progress(
    client: TestClient,
    headers: dict[str, str],
    client_id: int,
    weight_kg: str = "80.5",
    record_date: str | None = None,
):
    return client.post(
        f"{API}/progress",
        json={
            "client_id": client_id,
            "record_date": record_date or date.today().isoformat(),
            "weight_kg": weight_kg,
            "waist_cm": "90.0",
            "notes": "Medicion de prueba",
        },
        headers=headers,
    )


def test_registrar_progreso_como_admin_devuelve_201(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress1@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.progress1@gmail.com"
    ).json()["client"]["id"]

    response = _register_progress(client, admin_headers, client_id)

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == client_id
    assert float(body["waist_cm"]) == 90.0


def test_registrar_progreso_para_cliente_ajeno_como_entrenador_devuelve_403(
    client: TestClient,
) -> None:
    admin = _seed_user("smartgym.qa.admin.progress2@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user(
        "smartgym.qa.entrenador.a.progress2@gmail.com", "ClaveEntrenadorA123", "entrenador"
    )
    trainer_b = _seed_user(
        "smartgym.qa.entrenador.b.progress2@gmail.com", "ClaveEntrenadorB123", "entrenador"
    )
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")

    client_id = _register_client(
        client,
        admin_headers,
        "smartgym.qa.cliente.progress2@gmail.com",
        trainer_id=trainer_b.id,
    ).json()["client"]["id"]

    response = _register_progress(client, trainer_a_headers, client_id)

    assert response.status_code == 403


def test_registrar_progreso_para_cliente_inexistente_devuelve_404(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    response = _register_progress(client, admin_headers, client_id=999999)

    assert response.status_code == 404


def test_registrar_progreso_como_cliente_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    created = _register_client(client, admin_headers, "smartgym.qa.cliente.progress4@gmail.com")
    client_id = created.json()["client"]["id"]
    password = created.json()["temporary_password"]
    client_headers = _auth_headers(client, "smartgym.qa.cliente.progress4@gmail.com", password)

    response = _register_progress(client, client_headers, client_id)

    assert response.status_code == 403


def test_timeline_como_admin_ve_cualquiera(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress5@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.progress5@gmail.com"
    ).json()["client"]["id"]
    _register_progress(client, admin_headers, client_id)

    response = client.get(f"{API}/progress/clients/{client_id}", headers=admin_headers)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_timeline_como_entrenador_ve_solo_sus_clientes(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user(
        "smartgym.qa.entrenador.a.progress6@gmail.com", "ClaveEntrenadorA123", "entrenador"
    )
    trainer_b = _seed_user(
        "smartgym.qa.entrenador.b.progress6@gmail.com", "ClaveEntrenadorB123", "entrenador"
    )
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")

    client_a_id = _register_client(
        client,
        admin_headers,
        "smartgym.qa.cliente.a.progress6@gmail.com",
        trainer_id=trainer_a.id,
    ).json()["client"]["id"]
    client_b_id = _register_client(
        client,
        admin_headers,
        "smartgym.qa.cliente.b.progress6@gmail.com",
        trainer_id=trainer_b.id,
    ).json()["client"]["id"]
    _register_progress(client, admin_headers, client_a_id)
    _register_progress(client, admin_headers, client_b_id)

    own = client.get(f"{API}/progress/clients/{client_a_id}", headers=trainer_a_headers)
    assert own.status_code == 200
    assert len(own.json()) == 1

    other = client.get(f"{API}/progress/clients/{client_b_id}", headers=trainer_a_headers)
    assert other.status_code == 403


def test_timeline_como_cliente_ve_lo_propio_pero_no_lo_de_otro(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.progress7@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.progress7@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.progress7@gmail.com")
    client_a_id = created_a.json()["client"]["id"]
    client_b_id = created_b.json()["client"]["id"]
    password_a = created_a.json()["temporary_password"]

    _register_progress(client, admin_headers, client_a_id)
    _register_progress(client, admin_headers, client_b_id)

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.progress7@gmail.com", password_a)

    own = client.get(f"{API}/progress/clients/{client_a_id}", headers=client_a_headers)
    assert own.status_code == 200
    assert len(own.json()) == 1

    other = client.get(f"{API}/progress/clients/{client_b_id}", headers=client_a_headers)
    assert other.status_code == 403
