"""Emision/decodificacion de JWT de sesion, via PyJWT.

DECISIONES.md, 2026-10-10 (arranque de Entrega 2, punto 3): `PyJWT` en vez
de `python-jose` -- mas simple para lo que necesita este proyecto (un solo
algoritmo simetrico, sin JWKS ni rotacion de llaves).

El secreto se lee de la variable de entorno `JWT_SECRET` (nunca
hardcodeado) -- ver `.env.example`/`.env` (raiz del repo) y
`docker-compose.yml`, servicio `backend`. Expiracion: 8 horas, razonable
para un sistema de staff de gimnasio que se usa en turnos de trabajo
(ver DECISIONES.md, entrada "2026-10-10 -- Resolucion del backlog... (B1)").
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def _get_secret() -> str:
    secret = os.environ.get("JWT_SECRET")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET no esta configurado -- ver .env.example (raiz del repo)."
        )
    return secret


def create_access_token(user_id: int, role: str) -> str:
    """Emite un JWT de sesion para `user_id` con su `role` embebido.

    El dominio NUNCA llama esto directamente -- es responsabilidad de la
    capa API (`api/v1/routers/auth.py`), que es la unica que sabe que la
    sesion se representa como un JWT.
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, _get_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un JWT de sesion.

    Deja que `jwt.ExpiredSignatureError`/`jwt.InvalidTokenError` se
    propaguen -- el llamador (`api/v1/dependencies.py`) los traduce a un
    401 HTTP, que es detalle de transporte ajeno a este modulo.
    """
    return jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
