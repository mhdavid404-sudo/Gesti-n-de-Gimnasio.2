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

from src.domain.users.entities import ROLES_VALIDOS, User
from src.domain.users.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidRoleError,
)
from src.domain.users.repositories import UserRepository
from src.infrastructure.security.password import hash_password, verify_password


@dataclass
class RegisterUserUseCase:
    """RF001: registrar un usuario nuevo con un rol.

    Valida unicidad de email y que `role` sea uno de `ROLES_VALIDOS`,
    hashea el password en texto plano antes de persistir (nunca se guarda
    en claro) y delega la persistencia en el repositorio inyectado.
    """

    user_repository: UserRepository

    def execute(self, user: User) -> User:
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
        return self.user_repository.add(user_to_persist)


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
