"""CP del modulo Users (RF001, RF002) -- pantalla "Usuarios": alta,
restablecimiento de contraseña y activar/desactivar, todo por Admin.

Corre contra una base de datos Postgres real (ver `conftest.py` para la
estrategia de aislamiento entre pruebas: TRUNCATE de `users` por test).

Casos cubiertos:
    1. Restablecer la contraseña de otro usuario (un entrenador) como admin
       -> 200, la contraseña anterior deja de funcionar, la temporal nueva
       sí funciona, y queda un AuditLog con action="restablecer_password".
    2. Restablecer como rol no-admin (entrenador) -> 403.
    3. Restablecer la contraseña de un usuario que no existe -> 404.
    4. Alta de usuario como admin -> 201 Y queda registrado en AuditLog
       (action="crear_usuario") -- `test_auth.py` ya cubre el 201 por sí
       solo (`test_registro_exitoso`) y los casos de rol no-admin (403,
       `test_acceso_con_rol_insuficiente_devuelve_403`) y correo duplicado
       (409, `test_registro_con_email_duplicado_devuelve_409`); no se
       duplican aquí, solo se agrega la verificación de bitácora que faltaba.
    5. Desactivar y reactivar a otro usuario como admin -> ambas acciones
       quedan en AuditLog ("desactivar_usuario"/"activar_usuario") y la
       cuenta desactivada no puede iniciar sesión mientras lo está.
    6. Un admin no puede desactivarse a sí mismo -> 400, sigue activo.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.password import hash_password

API = "/api/v1"


def _seed_user(
    email: str,
    password: str,
    role: str,
    full_name: str = "Usuario de prueba",
) -> User:
    """Inserta un usuario directo en la base real, sin pasar por la API
    (mismo patron que `test_clients.py`)."""
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


def test_restablecer_password_como_admin_funciona_y_queda_en_bitacora(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.users1@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    objetivo = _seed_user(
        "smartgym.qa.entrenador.users1@gmail.com", "ClaveOriginal123", "entrenador", "Entrenador Original"
    )

    response = client.post(f"{API}/users/{objetivo.id}/reset-password", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    temporal = body["temporary_password"]
    assert len(temporal) == 12

    # La contraseña anterior ya no sirve.
    login_viejo = client.post(
        f"{API}/auth/login", json={"email": objetivo.email, "password": "ClaveOriginal123"}
    )
    assert login_viejo.status_code == 401

    # La temporal nueva sí funciona.
    login_nuevo = client.post(f"{API}/auth/login", json={"email": objetivo.email, "password": temporal})
    assert login_nuevo.status_code == 200

    # Queda registrado en la bitácora (RF015), atribuido al admin que lo hizo.
    audit = client.get(f"{API}/audit-logs?limit=5", headers=admin_headers).json()
    entry = next(a for a in audit if a["action"] == "restablecer_password" and a["entity_id"] == str(objetivo.id))
    assert entry["user_id"] == admin.id


def test_restablecer_password_como_no_admin_devuelve_403(client: TestClient) -> None:
    trainer = _seed_user("smartgym.qa.entrenador.users2@gmail.com", "ClaveEntrenador123", "entrenador")
    objetivo = _seed_user("smartgym.qa.cliente.users2@gmail.com", "ClaveCliente123", "cliente")

    trainer_headers = _auth_headers(client, trainer.email, "ClaveEntrenador123")

    response = client.post(f"{API}/users/{objetivo.id}/reset-password", headers=trainer_headers)

    assert response.status_code == 403

    # La contraseña del objetivo sigue siendo la original -- el intento
    # rechazado no debe haber cambiado nada.
    login = client.post(f"{API}/auth/login", json={"email": objetivo.email, "password": "ClaveCliente123"})
    assert login.status_code == 200


def test_restablecer_password_de_usuario_inexistente_devuelve_404(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.users3@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(f"{API}/users/999999/reset-password", headers=admin_headers)

    assert response.status_code == 404


def test_alta_de_usuario_como_admin_queda_en_bitacora(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.users4@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.post(
        f"{API}/users",
        json={
            "email": "smartgym.qa.entrenador.nuevo.users4@gmail.com",
            "password": "ClaveSegura123",
            "full_name": "Entrenador Creado Por Admin",
            "role": "entrenador",
        },
        headers=admin_headers,
    )

    assert response.status_code == 201
    nuevo_id = response.json()["id"]

    audit = client.get(f"{API}/audit-logs?limit=5", headers=admin_headers).json()
    entry = next(a for a in audit if a["action"] == "crear_usuario" and a["entity_id"] == str(nuevo_id))
    assert entry["user_id"] == admin.id
    assert "entrenador" in entry["details"]


def test_desactivar_y_reactivar_usuario_como_admin_queda_en_bitacora(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.users5@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    objetivo = _seed_user(
        "smartgym.qa.entrenador.users5@gmail.com", "ClaveEntrenador123", "entrenador", "Entrenador A Desactivar"
    )

    # Desactivar.
    desactivar = client.patch(f"{API}/users/{objetivo.id}", json={"is_active": False}, headers=admin_headers)
    assert desactivar.status_code == 200
    assert desactivar.json()["is_active"] is False

    login_desactivado = client.post(
        f"{API}/auth/login", json={"email": objetivo.email, "password": "ClaveEntrenador123"}
    )
    assert login_desactivado.status_code == 401

    # Reactivar.
    activar = client.patch(f"{API}/users/{objetivo.id}", json={"is_active": True}, headers=admin_headers)
    assert activar.status_code == 200
    assert activar.json()["is_active"] is True

    login_reactivado = client.post(
        f"{API}/auth/login", json={"email": objetivo.email, "password": "ClaveEntrenador123"}
    )
    assert login_reactivado.status_code == 200

    # Ambas acciones quedaron en bitácora.
    audit = client.get(f"{API}/audit-logs?limit=10", headers=admin_headers).json()
    desactivar_entry = next(
        a for a in audit if a["action"] == "desactivar_usuario" and a["entity_id"] == str(objetivo.id)
    )
    activar_entry = next(a for a in audit if a["action"] == "activar_usuario" and a["entity_id"] == str(objetivo.id))
    assert desactivar_entry["user_id"] == admin.id
    assert activar_entry["user_id"] == admin.id


def test_admin_no_puede_desactivarse_a_si_mismo(client: TestClient) -> None:
    admin = _seed_user("smartgym.qa.admin.users6@gmail.com", "AdminPass123", "admin")
    admin_headers = _auth_headers(client, admin.email, "AdminPass123")

    response = client.patch(f"{API}/users/{admin.id}", json={"is_active": False}, headers=admin_headers)

    assert response.status_code == 400

    # Sigue activo -- el propio admin puede seguir iniciando sesión.
    login = client.post(f"{API}/auth/login", json={"email": admin.email, "password": "AdminPass123"})
    assert login.status_code == 200
