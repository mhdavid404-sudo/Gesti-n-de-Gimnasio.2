"""Excepciones de dominio del modulo Users.

Regla dura (DECISIONES.md, correccion #2/#3): el dominio no conoce HTTP ni
FastAPI. Estos casos de uso (`application/users/use_cases.py`) lanzan estas
excepciones; la traduccion a `HTTPException`/codigo de estado ocurre
unicamente en `api/v1/routers/users.py` y `api/v1/routers/auth.py`.
"""

from __future__ import annotations


class EmailAlreadyExistsError(Exception):
    """Se intento registrar un usuario con un email que ya existe."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Ya existe un usuario con el email '{email}'")


class InvalidRoleError(Exception):
    """El rol solicitado no es uno de `ROLES_VALIDOS`."""

    def __init__(self, role: str) -> None:
        self.role = role
        super().__init__(f"Rol invalido: '{role}'")


class InvalidCredentialsError(Exception):
    """Email no existe, password incorrecto, o la cuenta esta inactiva."""

    def __init__(self) -> None:
        super().__init__("Credenciales invalidas")


class UserNotFoundError(Exception):
    """No existe un usuario con el id solicitado."""

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(f"Usuario {user_id} no existe")
