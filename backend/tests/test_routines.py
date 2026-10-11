"""CP del modulo Ejercicios y Rutinas (RF007, RF008, RF012, RF013) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas). `routine_exercises`/
`routine_assignments` no necesitan TRUNCATE explicito: caen en cascada al
truncar `routines`/`client_profiles`.

Casos cubiertos:
    1. Crear rutina como entrenador -> 201, `created_by` correcto, nunca
       inyectable desde el body.
    2. Crear rutina como cliente -> 403.
    3. Agregar ejercicio a rutina inexistente -> 404.
    4. Asignar rutina a cliente propio como entrenador -> 201.
    5. Asignar rutina a cliente ajeno como entrenador -> 403.
    6. Listar historial como cliente ve lo propio pero no lo de otro.
    7. `PATCH /routines/assignments/{id}` como entrenador dueno (200) y
       como entrenador que NO es dueno (403).
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


def _create_routine(client: TestClient, headers: dict[str, str], name: str = "Rutina de prueba"):
    return client.post(
        f"{API}/routines",
        json={"name": name, "description": "Rutina generica"},
        headers=headers,
    )


def _create_exercise(client: TestClient, headers: dict[str, str], name: str = "Sentadilla"):
    return client.post(
        f"{API}/exercises",
        json={"name": name, "muscle_group": "Piernas", "description": "Ejercicio compuesto"},
        headers=headers,
    )


def _assign_routine(
    client: TestClient,
    headers: dict[str, str],
    routine_id: int,
    client_id: int,
    status_value: str = "activa",
):
    return client.post(
        f"{API}/routines/assignments",
        json={
            "routine_id": routine_id,
            "client_id": client_id,
            "assigned_date": date.today().isoformat(),
            "status": status_value,
            "notes": "Asignacion de prueba",
        },
        headers=headers,
    )


def test_crear_rutina_como_entrenador_devuelve_created_by_correcto(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.rut1@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    response = _create_routine(client, headers, "Rutina Fuerza 1")

    assert response.status_code == 201
    body = response.json()
    assert body["created_by"] == trainer.id


def test_crear_rutina_ignora_created_by_inyectado_en_el_body(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.rut2@gmail.com", "ClaveEntrenador123", "entrenador")
    otro = _seed_user("smartgym.qa.admin.otro.rut2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    payload = {"name": "Rutina Fuerza 2", "description": "x", "created_by": otro.id}
    response = client.post(f"{API}/routines", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["created_by"] == trainer.id


def test_crear_rutina_como_cliente_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    created = _register_client(client, admin_headers, "smartgym.qa.cliente.rut3@gmail.com")
    password = created.json()["temporary_password"]
    client_headers = _auth_headers(client, "smartgym.qa.cliente.rut3@gmail.com", password)

    response = _create_routine(client, client_headers, "Rutina Fuerza 3")

    assert response.status_code == 403


def test_agregar_ejercicio_a_rutina_inexistente_devuelve_404(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.rut4@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    exercise_id = _create_exercise(client, headers, "Press banca rut4").json()["id"]

    response = client.post(
        f"{API}/routines/999999/exercises",
        json={"exercise_id": exercise_id, "sets": 3, "reps": 10, "order_index": 0},
        headers=headers,
    )

    assert response.status_code == 404


def test_agregar_ejercicio_inexistente_a_rutina_devuelve_404(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.rut5@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")
    routine_id = _create_routine(client, headers, "Rutina Fuerza 5").json()["id"]

    response = client.post(
        f"{API}/routines/{routine_id}/exercises",
        json={"exercise_id": 999999, "sets": 3, "reps": 10, "order_index": 0},
        headers=headers,
    )

    assert response.status_code == 404


def test_asignar_rutina_a_cliente_propio_como_entrenador_devuelve_201(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.rut6@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.rut6@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]
    routine_id = _create_routine(client, trainer_headers, "Rutina Fuerza 6").json()["id"]

    response = _assign_routine(client, trainer_headers, routine_id, client_id)

    assert response.status_code == 201
    assert response.json()["assigned_by"] == trainer.id


def test_asignar_rutina_a_cliente_ajeno_como_entrenador_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut7@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.rut7@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.rut7@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.rut7@gmail.com", trainer_id=trainer_b.id
    ).json()["client"]["id"]
    routine_id = _create_routine(client, trainer_a_headers, "Rutina Fuerza 7").json()["id"]

    response = _assign_routine(client, trainer_a_headers, routine_id, client_id)

    assert response.status_code == 403


def test_historial_como_cliente_ve_lo_propio_pero_no_lo_de_otro(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut8@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.rut8@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.rut8@gmail.com")
    client_a_id = created_a.json()["client"]["id"]
    client_b_id = created_b.json()["client"]["id"]
    password_a = created_a.json()["temporary_password"]

    routine_id = _create_routine(client, admin_headers, "Rutina Fuerza 8").json()["id"]
    _assign_routine(client, admin_headers, routine_id, client_a_id)
    _assign_routine(client, admin_headers, routine_id, client_b_id)

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.rut8@gmail.com", password_a)

    own = client.get(f"{API}/routines/assignments/clients/{client_a_id}", headers=client_a_headers)
    assert own.status_code == 200
    assert len(own.json()) == 1

    other = client.get(f"{API}/routines/assignments/clients/{client_b_id}", headers=client_a_headers)
    assert other.status_code == 403


def test_patch_assignment_como_entrenador_dueno_devuelve_200(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut9@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.rut9@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.rut9@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]
    routine_id = _create_routine(client, trainer_headers, "Rutina Fuerza 9").json()["id"]
    assignment_id = _assign_routine(client, trainer_headers, routine_id, client_id).json()["id"]

    response = client.patch(
        f"{API}/routines/assignments/{assignment_id}",
        json={"status": "completada", "notes": "Cliente termino el ciclo"},
        headers=trainer_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completada"
    assert body["notes"] == "Cliente termino el ciclo"


def test_patch_assignment_como_entrenador_no_dueno_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.rut10@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.rut10@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.rut10@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.rut10@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    routine_id = _create_routine(client, trainer_a_headers, "Rutina Fuerza 10").json()["id"]
    assignment_id = _assign_routine(client, trainer_a_headers, routine_id, client_id).json()["id"]

    response = client.patch(
        f"{API}/routines/assignments/{assignment_id}",
        json={"status": "completada"},
        headers=trainer_b_headers,
    )

    assert response.status_code == 403
