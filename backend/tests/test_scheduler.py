"""CP del job diario de vencimientos (RF006) -- Entrega 3.

No se prueba "corre todos los dias a las 06:00" (no es practico esperar un
dia en un test) -- se prueba lo que SI se puede verificar de forma
determinista:
    1. `start_scheduler()` registra el job diario con el trigger cron
       esperado.
    2. `run_daily_expiring_detection()` (la funcion que ese job ejecuta)
       hace exactamente lo mismo que `DetectExpiringMembershipsUseCase` via
       el endpoint manual -- transiciona una membresia vencida y genera su
       notificacion -- probado aqui llamandola directo, sin pasar por HTTP
       ni por el ciclo de vida de FastAPI (evita depender de si
       `TestClient` dispara o no los eventos `startup`/`shutdown`).
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.notifications import SqlAlchemyNotificationRepository
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.scheduler import (
    DAILY_JOB_ID,
    run_daily_expiring_detection,
    shutdown_scheduler,
    start_scheduler,
)
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


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_start_scheduler_registra_el_job_diario() -> None:
    try:
        scheduler = start_scheduler()
        job = scheduler.get_job(DAILY_JOB_ID)

        assert job is not None
        field_by_name = {field.name: str(field) for field in job.trigger.fields}
        assert field_by_name["hour"] == "6"
        assert field_by_name["minute"] == "0"
    finally:
        shutdown_scheduler()


def test_run_daily_expiring_detection_transiciona_y_notifica(client) -> None:
    admin = _seed_user("smartgym.qa.admin.scheduler1@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    plan_payload = {
        "name": "Plan Scheduler",
        "price": "399.00",
        "duration_days": 30,
        "description": "Plan de prueba",
        "benefits": ["Acceso general"],
    }
    plan_id = client.post(f"{API}/membership-plans", json=plan_payload, headers=admin_headers).json()["id"]

    client_payload = {
        "email": "smartgym.qa.cliente.scheduler1@gmail.com",
        "full_name": "Cliente Scheduler",
        "trainer_id": None,
        "phone": "5512345678",
        "birth_date": "1995-05-20",
        "address": "Calle Falsa 123",
        "emergency_contact_name": "Alguien",
        "emergency_contact_phone": "555-0000",
    }
    created_client = client.post(f"{API}/clients", json=client_payload, headers=admin_headers).json()
    client_id = created_client["client"]["id"]
    user_id = created_client["client"]["user_id"]

    past_start = date.today() - timedelta(days=40)
    past_end = date.today() - timedelta(days=5)
    membership_payload = {
        "client_id": client_id,
        "plan_id": plan_id,
        "start_date": past_start.isoformat(),
        "end_date": past_end.isoformat(),
        "status": "activa",
    }
    membership_id = client.post(f"{API}/memberships", json=membership_payload, headers=admin_headers).json()["id"]

    run_daily_expiring_detection()

    membership = client.get(f"{API}/memberships/{membership_id}", headers=admin_headers).json()
    assert membership["status"] == "vencida"

    session: Session = SessionLocal()
    try:
        notifications = SqlAlchemyNotificationRepository(session).list_by_user(user_id)
    finally:
        session.close()
    assert any(n.type == "membresia_vencida" for n in notifications)
