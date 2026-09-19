"""Casos de uso del modulo Users.

Entrega 1: solo el esqueleto (firmas + dependencias inyectadas). La logica
de negocio completa (incluido el hash real de password y el login JWT) es
alcance de Entrega 2 -- ver DECISIONES.md y SMARTGYM-V2-BRIEF.md.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.users.entities import User
from src.domain.users.repositories import UserRepository


@dataclass
class RegisterUserUseCase:
    """RF001: registrar un usuario nuevo con un rol.

    Entrega 2 debe: validar unicidad de email, hashear el password con un
    algoritmo seguro (ej. bcrypt via passlib) antes de persistir -- NUNCA
    guardar el password en texto plano -- y validar que `role` sea uno de
    `ROLES_VALIDOS`.
    """

    user_repository: UserRepository

    def execute(self, user: User) -> User:
        raise NotImplementedError("Entrega 2: logica de registro pendiente")


@dataclass
class AuthenticateUserUseCase:
    """RF001: autenticar usuario y emitir credenciales de sesion.

    Entrega 2 debe: verificar password contra `password_hash` y emitir un
    JWT. NO implementado en Entrega 1 (ver COORDINACION-ENTREGA1.md).
    """

    user_repository: UserRepository

    def execute(self, email: str, password: str) -> User:
        raise NotImplementedError("Entrega 2: login/JWT pendiente")


@dataclass
class ListUsersByRoleUseCase:
    """RF002: listar usuarios por rol (soporte para control de acceso)."""

    user_repository: UserRepository

    def execute(self, role: str) -> list[User]:
        raise NotImplementedError("Entrega 2: logica pendiente")
