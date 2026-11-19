"""CP del modulo Dietas (RF009, RF012, RF013) -- Entrega 2.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas). `diet_assignments` no necesita
TRUNCATE explicito: cae en cascada al truncar `diet_plans`/
`client_profiles`.

Mismo patron que `test_routines.py` (Dietas es casi identico en
estructura a Rutinas, solo mas simple: sin catalogo de sub-items
equivalente a `Exercise`/`RoutineExercise`). Casos cubiertos:
    1. Crear plan como entrenador -> 201, `created_by` correcto, nunca
       inyectable desde el body.
    2. Crear plan como cliente -> 403.
    3. Asignar plan a cliente propio como entrenador -> 201.
    4. Asignar plan a cliente ajeno como entrenador -> 403.
    5. Listar historial como cliente ve lo propio pero no lo de otro.
    6. `PATCH /diets/assignments/{id}` como entrenador dueno (200) y
       como entrenador que NO es dueno (403).

2026-11-18 (ampliacion de RF009/RF012, "editar/eliminar dieta" -- ver
DECISIONES.md). Casos nuevos, mismo patron que `test_routines.py`:
    7. Editar plan como admin -> 200, queda en bitacora.
    8. Editar plan ajeno como entrenador (no lo creo) -> 403.
    9. Eliminar plan SIN asignaciones -> se borra de verdad.
    10. Eliminar plan CON asignaciones -> se desactiva, conserva historial.
    11. Eliminar plan como cliente -> 403.
    12. Corregir una asignacion (plan/fecha, "error de dedo") como
        entrenador dueno -> 200, queda en bitacora.
    13. Eliminar una asignacion -> 204, bitacora sobrevive.
    14. Eliminar una asignacion como entrenador que NO es dueno -> 403.
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


def _create_diet_plan(client: TestClient, headers: dict[str, str], name: str = "Plan de prueba"):
    return client.post(
        f"{API}/diets/plans",
        json={"name": name, "description": "Plan generico", "calories_target": 2000},
        headers=headers,
    )


def _assign_diet(
    client: TestClient,
    headers: dict[str, str],
    diet_plan_id: int,
    client_id: int,
    status_value: str = "activa",
):
    return client.post(
        f"{API}/diets/assignments",
        json={
            "diet_plan_id": diet_plan_id,
            "client_id": client_id,
            "assigned_date": date.today().isoformat(),
            "status": status_value,
            "notes": "Asignacion de prueba",
        },
        headers=headers,
    )


def test_crear_plan_como_entrenador_devuelve_created_by_correcto(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.diet1@gmail.com", "ClaveEntrenador123", "entrenador")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    response = _create_diet_plan(client, headers, "Plan Volumen 1")

    assert response.status_code == 201
    body = response.json()
    assert body["created_by"] == trainer.id


def test_crear_plan_ignora_created_by_inyectado_en_el_body(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.diet2@gmail.com", "ClaveEntrenador123", "entrenador")
    otro = _seed_user("smartgym.qa.admin.otro.diet2@gmail.com", "AdminPass123", "admin")
    headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    payload = {"name": "Plan Volumen 2", "description": "x", "created_by": otro.id}
    response = client.post(f"{API}/diets/plans", json=payload, headers=headers)

    assert response.status_code == 201
    assert response.json()["created_by"] == trainer.id


def test_crear_plan_como_cliente_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    created = _register_client(client, admin_headers, "smartgym.qa.cliente.diet3@gmail.com")
    password = created.json()["temporary_password"]
    client_headers = _auth_headers(client, "smartgym.qa.cliente.diet3@gmail.com", password)

    response = _create_diet_plan(client, client_headers, "Plan Volumen 3")

    assert response.status_code == 403


def test_asignar_plan_a_cliente_propio_como_entrenador_devuelve_201(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.diet6@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet6@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_headers, "Plan Volumen 6").json()["id"]

    response = _assign_diet(client, trainer_headers, plan_id, client_id)

    assert response.status_code == 201
    assert response.json()["assigned_by"] == trainer.id


def test_asignar_plan_a_cliente_ajeno_como_entrenador_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet7@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.diet7@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.diet7@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet7@gmail.com", trainer_id=trainer_b.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_a_headers, "Plan Volumen 7").json()["id"]

    response = _assign_diet(client, trainer_a_headers, plan_id, client_id)

    assert response.status_code == 403


def test_historial_como_cliente_ve_lo_propio_pero_no_lo_de_otro(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet8@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    created_a = _register_client(client, admin_headers, "smartgym.qa.cliente.a.diet8@gmail.com")
    created_b = _register_client(client, admin_headers, "smartgym.qa.cliente.b.diet8@gmail.com")
    client_a_id = created_a.json()["client"]["id"]
    client_b_id = created_b.json()["client"]["id"]
    password_a = created_a.json()["temporary_password"]

    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 8").json()["id"]
    _assign_diet(client, admin_headers, plan_id, client_a_id)
    _assign_diet(client, admin_headers, plan_id, client_b_id)

    client_a_headers = _auth_headers(client, "smartgym.qa.cliente.a.diet8@gmail.com", password_a)

    own = client.get(f"{API}/diets/assignments/clients/{client_a_id}", headers=client_a_headers)
    assert own.status_code == 200
    assert len(own.json()) == 1

    other = client.get(f"{API}/diets/assignments/clients/{client_b_id}", headers=client_a_headers)
    assert other.status_code == 403


def test_patch_assignment_como_entrenador_dueno_devuelve_200(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet9@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.diet9@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet9@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_headers, "Plan Volumen 9").json()["id"]
    assignment_id = _assign_diet(client, trainer_headers, plan_id, client_id).json()["id"]

    response = client.patch(
        f"{API}/diets/assignments/{assignment_id}",
        json={"status": "completada", "notes": "Cliente termino el ciclo"},
        headers=trainer_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completada"
    assert body["notes"] == "Cliente termino el ciclo"


def test_patch_assignment_como_entrenador_no_dueno_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet10@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.diet10@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.diet10@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet10@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_a_headers, "Plan Volumen 10").json()["id"]
    assignment_id = _assign_diet(client, trainer_a_headers, plan_id, client_id).json()["id"]

    response = client.patch(
        f"{API}/diets/assignments/{assignment_id}",
        json={"status": "completada"},
        headers=trainer_b_headers,
    )

    assert response.status_code == 403


# --- Ampliacion 2026-11-18: editar/eliminar dieta y sus asignaciones ------


def test_editar_plan_como_admin_actualiza_datos(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet11@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 11").json()["id"]

    response = client.patch(
        f"{API}/diets/plans/{plan_id}",
        json={"name": "Plan Volumen 11 (editado)", "calories_target": 2500},
        headers=admin_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Plan Volumen 11 (editado)"
    assert body["calories_target"] == 2500

    audit = client.get(f"{API}/audit-logs?limit=5", headers=admin_headers).json()
    entry = next(a for a in audit if a["action"] == "editar_dieta" and a["entity_id"] == str(plan_id))
    assert entry["user_id"] == admin.id


def test_editar_plan_ajeno_como_entrenador_devuelve_403(client: TestClient) -> None:
    trainer_a = _seed_user("smartgym.qa.entrenador.a.diet12@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.diet12@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    plan_id = _create_diet_plan(client, trainer_a_headers, "Plan Volumen 12").json()["id"]

    response = client.patch(
        f"{API}/diets/plans/{plan_id}",
        json={"name": "Intento ajeno"},
        headers=trainer_b_headers,
    )

    assert response.status_code == 403


def test_eliminar_plan_sin_asignaciones_borra_de_verdad(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet13@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 13").json()["id"]

    response = client.delete(f"{API}/diets/plans/{plan_id}", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is True
    assert body["diet_plan"] is None

    catalog = client.get(f"{API}/diets/plans", headers=admin_headers).json()
    assert all(p["id"] != plan_id for p in catalog)


def test_eliminar_plan_con_asignaciones_lo_desactiva(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet14@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet14@gmail.com"
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 14").json()["id"]
    _assign_diet(client, admin_headers, plan_id, client_id)

    response = client.delete(f"{API}/diets/plans/{plan_id}", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is False
    assert body["diet_plan"]["is_active"] is False

    catalog = client.get(f"{API}/diets/plans", headers=admin_headers).json()
    still_there = next(p for p in catalog if p["id"] == plan_id)
    assert still_there["is_active"] is False


def test_eliminar_plan_como_cliente_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet15@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 15").json()["id"]
    created = _register_client(client, admin_headers, "smartgym.qa.cliente.diet15@gmail.com")
    password = created.json()["temporary_password"]
    client_headers = _auth_headers(client, "smartgym.qa.cliente.diet15@gmail.com", password)

    response = client.delete(f"{API}/diets/plans/{plan_id}", headers=client_headers)

    assert response.status_code == 403


def test_corregir_asignacion_dieta_como_entrenador_dueno_actualiza_y_registra_bitacora(
    client: TestClient,
) -> None:
    admin = _seed_user("smartgym.qa.admin.diet16@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer = _seed_user("smartgym.qa.entrenador.diet16@gmail.com", "ClaveEntrenador123", "entrenador")
    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet16@gmail.com", trainer_id=trainer.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_headers, "Plan Volumen 16 - original").json()["id"]
    otro_plan_id = _create_diet_plan(client, trainer_headers, "Plan Volumen 16 - correcto").json()["id"]
    assignment_id = _assign_diet(client, trainer_headers, plan_id, client_id).json()["id"]

    response = client.patch(
        f"{API}/diets/assignments/{assignment_id}",
        json={"diet_plan_id": otro_plan_id, "assigned_date": date.today().isoformat()},
        headers=trainer_headers,
    )

    assert response.status_code == 200
    assert response.json()["diet_plan_id"] == otro_plan_id

    audit = client.get(f"{API}/audit-logs?limit=5", headers=admin_headers).json()
    entry = next(
        a for a in audit if a["action"] == "editar_asignacion_dieta" and a["entity_id"] == str(assignment_id)
    )
    assert entry["user_id"] == trainer.id


def test_eliminar_asignacion_dieta_borra_la_fila_pero_bitacora_sobrevive(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet17@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet17@gmail.com"
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, admin_headers, "Plan Volumen 17").json()["id"]
    assignment_id = _assign_diet(client, admin_headers, plan_id, client_id).json()["id"]

    response = client.delete(f"{API}/diets/assignments/{assignment_id}", headers=admin_headers)
    assert response.status_code == 204

    historial = client.get(
        f"{API}/diets/assignments/clients/{client_id}", headers=admin_headers
    ).json()
    assert all(a["id"] != assignment_id for a in historial)

    audit = client.get(f"{API}/audit-logs?limit=5", headers=admin_headers).json()
    entry = next(
        a
        for a in audit
        if a["action"] == "eliminar_asignacion_dieta" and a["entity_id"] == str(assignment_id)
    )
    assert entry["user_id"] == admin.id


def test_eliminar_asignacion_dieta_como_entrenador_no_dueno_devuelve_403(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.diet18@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")
    trainer_a = _seed_user("smartgym.qa.entrenador.a.diet18@gmail.com", "ClaveEntrenadorA123", "entrenador")
    trainer_b = _seed_user("smartgym.qa.entrenador.b.diet18@gmail.com", "ClaveEntrenadorB123", "entrenador")
    trainer_a_headers = _auth_headers(client, trainer_a.email, "ClaveEntrenadorA123")
    trainer_b_headers = _auth_headers(client, trainer_b.email, "ClaveEntrenadorB123")

    client_id = _register_client(
        client, admin_headers, "smartgym.qa.cliente.diet18@gmail.com", trainer_id=trainer_a.id
    ).json()["client"]["id"]
    plan_id = _create_diet_plan(client, trainer_a_headers, "Plan Volumen 18").json()["id"]
    assignment_id = _assign_diet(client, trainer_a_headers, plan_id, client_id).json()["id"]

    response = client.delete(
        f"{API}/diets/assignments/{assignment_id}", headers=trainer_b_headers
    )

    assert response.status_code == 403
