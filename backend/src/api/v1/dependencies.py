"""Dependencias FastAPI reusables: usuario autenticado y control de rol.

Vive en `api/`, no en `domain/` ni `application/`, porque hablar de un
header `Authorization: Bearer ...` y de codigos HTTP (401/403) es detalle
de transporte -- igual que los schemas Pydantic (ver nota en
`api/v1/schemas/users.py`).
"""

from __future__ import annotations

from collections.abc import Callable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.users import SqlAlchemyUserRepository
from src.infrastructure.security.jwt import decode_access_token

_bearer_scheme = HTTPBearer(auto_error=False)

_CREDENCIALES_INVALIDAS = "No se pudo validar la credencial."


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodifica el JWT del header `Authorization: Bearer <token>`.

    401 si falta el header, el token es invalido/expiro, o el usuario ya
    no existe o esta inactivo (una cuenta desactivada despues de emitido
    el token no debe seguir teniendo acceso).
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_CREDENCIALES_INVALIDAS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_CREDENCIALES_INVALIDAS,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    repository = SqlAlchemyUserRepository(db)
    user = repository.get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_CREDENCIALES_INVALIDAS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*roles: str) -> Callable[[User], None]:
    """Factory de dependencia: 403 si el rol del usuario actual no esta en `roles`.

    Base de RF012 (entrenador limitado a sus clientes asignados) y RF013
    (cliente solo lectura de lo propio) -- esos dos RF necesitan ademas
    filtrar POR DATO (no solo por rol: un entrenador puede ver a SU
    cliente, no a cualquiera), lo que se aplica caso por caso dentro de
    cada caso de uso cuando se conecten los modulos Clientes/Rutinas/
    Dietas/Progreso en esta misma entrega. Esta dependencia solo cubre el
    primer filtro (control de acceso por rol).
    """

    def dependency(current_user: User = Depends(get_current_user)) -> None:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta accion.",
            )

    return dependency
