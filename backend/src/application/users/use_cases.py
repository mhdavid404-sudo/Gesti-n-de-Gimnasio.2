"""Casos de uso del modulo Users.

Entrega 2: logica real de registro/autenticacion (RF001, RF002). El JWT en
si NO se genera aqui -- `AuthenticateUserUseCase` solo verifica
credenciales y devuelve el `User` autenticado; emitir el token es
responsabilidad de la capa API (`api/v1/routers/auth.py`), que es la unica
que sabe que la sesion se representa como un JWT (el dominio no debe saber
que eso existe).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.notifications.entities import AuditLog
from src.domain.notifications.repositories import AuditLogRepository
from src.domain.users.entities import ROLES_VALIDOS, User
from src.domain.users.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRoleError,
)
from src.domain.users.repositories import UserRepository
from src.infrastructure.security.password import generate_temporary_password, hash_password, verify_password


@dataclass
class RegisterUserUseCase:
    """RF001: registrar un usuario nuevo con un rol.

    Valida unicidad de email y que `role` sea uno de `ROLES_VALIDOS`,
    hashea el password en texto plano antes de persistir (nunca se guarda
    en claro) y delega la persistencia en el repositorio inyectado.

    Queda registrado en `AuditLog` (mismo patrón que `ResetUserPasswordUseCase`)
    porque dar de alta una cuenta de admin/entrenador es una acción
    administrativa que debe quedar trazada: quién la creó, con qué rol y
    cuándo. `performed_by_user_id` es opcional (en vez de requerido como en
    `ResetUserPasswordUseCase`) solo para no romper un eventual llamador sin
    un admin autenticado detrás -- hoy el único llamador real (`POST
    /users`) siempre lo tiene, por venir detrás de `require_role("admin")`.
    """

    user_repository: UserRepository
    audit_log_repository: AuditLogRepository

    def execute(self, user: User, performed_by_user_id: int | None = None) -> User:
        if user.role not in ROLES_VALIDOS:
            raise InvalidRoleError(user.role)

        if self.user_repository.get_by_email(user.email) is not None:
            raise EmailAlreadyExistsError(user.email)

        user_to_persist = User(
            id=None,
            email=user.email,
            password_hash=hash_password(user.password_hash),
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )
        created = self.user_repository.add(user_to_persist)

        self.audit_log_repository.add(
            AuditLog(
                id=None,
                user_id=performed_by_user_id,
                action="crear_usuario",
                entity_type="user",
                entity_id=str(created.id),
                details=f"Usuario '{created.email}' creado con rol '{created.role}'.",
            )
        )

        return created


@dataclass
class AuthenticateUserUseCase:
    """RF001: autenticar un usuario por email/password.

    NO emite JWT -- devuelve el `User` autenticado si las credenciales son
    correctas y la cuenta esta activa, o lanza `InvalidCredentialsError`.
    Emitir el token es responsabilidad explicita de la capa API.
    """

    user_repository: UserRepository

    def execute(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InvalidCredentialsError()

        return user


@dataclass
class ListUsersByRoleUseCase:
    """RF002: listar usuarios por rol (soporte para control de acceso)."""

    user_repository: UserRepository

    def execute(self, role: str) -> list[User]:
        return self.user_repository.list_by_role(role)


@dataclass
class ResetUserPasswordUseCase:
    """Restablecer la contraseña de cualquier usuario (admin), sin pedir la
    anterior -- mismo criterio que `RegisterClientUseCase`: se genera una
    temporal nueva con `generate_temporary_password()`, se hashea y se
    persiste; el valor en texto plano se devuelve UNA SOLA VEZ al llamador
    (la capa API lo envuelve en `PasswordResetResponse`) y nunca se vuelve a
    mostrar. El router ya resolvió que `user` existe antes de llamar esto
    (mismo patron que `update_user`), por eso esta clase no lanza su propia
    excepcion de "no encontrado".

    Queda registrado en `AuditLog` (mismo patron que `ChangeMembershipPlanUseCase`)
    porque restablecer la contraseña de otra cuenta es una accion
    administrativa sensible que debe quedar trazada: quien la hizo, a quien
    se la restablecio y cuando.
    """

    user_repository: UserRepository
    audit_log_repository: AuditLogRepository

    def execute(self, user: User, performed_by_user_id: int) -> str:
        temporary_password = generate_temporary_password()

        updated = User(
            id=user.id,
            email=user.email,
            password_hash=hash_password(temporary_password),
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )
        self.user_repository.update(updated)

        self.audit_log_repository.add(
            AuditLog(
                id=None,
                user_id=performed_by_user_id,
                action="restablecer_password",
                entity_type="user",
                entity_id=str(user.id),
                details=f"Contraseña restablecida para '{user.email}' (role={user.role}).",
            )
        )

        return temporary_password
