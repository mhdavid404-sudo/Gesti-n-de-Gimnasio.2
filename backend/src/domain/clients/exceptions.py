"""Excepciones de dominio del modulo Clients.

Mismo principio que `domain/users/exceptions.py` (DECISIONES.md, correccion
#2/#3): el dominio no conoce HTTP ni FastAPI. Estos casos de uso
(`application/clients/use_cases.py`) lanzan estas excepciones; la
traduccion a `HTTPException`/codigo de estado ocurre unicamente en
`api/v1/routers/clients.py`.
"""

from __future__ import annotations


class ClientNotFoundError(Exception):
    """No existe un `ClientProfile` con el id solicitado."""

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(f"Cliente {client_id} no existe")


class InvalidTrainerAssignmentError(Exception):
    """`trainer_id` no corresponde a un `User` con `role == 'entrenador'`.

    DECISIONES.md, correccion #4 (Entrega 1) y entrada del modulo Clientes
    (Entrega 2): la FK `client_profiles.trainer_id -> users.id` NO garantiza
    el rol del usuario referenciado -- esta invariante es responsabilidad
    explicita de `application/clients/use_cases.py`.
    """

    def __init__(self, trainer_id: int) -> None:
        self.trainer_id = trainer_id
        super().__init__(
            f"El usuario {trainer_id} no existe o no tiene rol 'entrenador'"
        )
