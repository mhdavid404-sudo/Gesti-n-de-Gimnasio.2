"""Hashing de password con bcrypt directo (sin passlib).

DECISIONES.md, 2026-10-10 (arranque de Entrega 2, punto 3): se eligio
`bcrypt` directo en vez de `passlib` porque `passlib` tiene historial de
friccion con versiones recientes de `bcrypt` (su wrapper de compatibilidad
quedo sin mantenimiento activo y rompe con bcrypt >= 4.1 en varios
entornos). La API de `bcrypt` puro es minima y no amerita esa capa extra.
"""

from __future__ import annotations

import secrets
import string

import bcrypt

# Factor de costo de bcrypt. 12 es el default de la libreria y un balance
# razonable entre seguridad y tiempo de respuesta para un sistema de staff
# de gimnasio (no un banco) -- documentado explicitamente para que nadie lo
# suba/baje sin medir el impacto en el login.
_BCRYPT_ROUNDS = 12

_TEMP_PASSWORD_LENGTH = 12
_TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits


def hash_password(plain: str) -> str:
    """Genera el hash bcrypt de una password en texto plano.

    Nunca se guarda `plain` en ningun lado -- el llamador (caso de uso de
    `application/users`) descarta la variable despues de esta llamada.
    """
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Compara una password en texto plano contra un hash bcrypt existente.

    Devuelve `False` (no lanza excepcion) si el hash esta corrupto o en un
    formato que bcrypt no reconoce -- un dato malformado en la base no debe
    tumbar el login, debe tratarse como credenciales invalidas.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def generate_temporary_password(length: int = _TEMP_PASSWORD_LENGTH) -> str:
    """Genera una password temporal aleatoria (letras + digitos, legible).

    DECISIONES.md (modulo Clientes, Entrega 2): el alta de cliente
    (`RegisterClientUseCase`) no pide password en el formulario -- se
    genera aqui con el modulo `secrets` (criptograficamente seguro, a
    diferencia de `random`), se hashea igual que cualquier otra password y
    se devuelve en texto claro UNA SOLA VEZ en la respuesta de `POST
    /clients` para que el staff la comparta con el cliente.
    """
    return "".join(secrets.choice(_TEMP_PASSWORD_ALPHABET) for _ in range(length))
