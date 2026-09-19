"""Casos de uso del modulo Clients.

Entrega 1: solo el esqueleto. Ver DECISIONES.md, correccion #4.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.clients.entities import ClientProfile
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.users.repositories import UserRepository


@dataclass
class RegisterClientUseCase:
    """RF003: registrar un cliente (crea/vincula su ClientProfile)."""

    client_repository: ClientProfileRepository
    user_repository: UserRepository

    def execute(self, client: ClientProfile) -> ClientProfile:
        raise NotImplementedError("Entrega 2: logica de registro pendiente")


@dataclass
class AssignTrainerToClientUseCase:
    """RF003: asignar/reasignar el entrenador de un cliente.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos:
        `trainer_id` debe apuntar a un `User` cuyo `role == "entrenador"`.
    La FK `client_profiles.trainer_id -> users.id` NO valida el rol; solo
    garantiza que el id exista. Entrega 2 debe implementar aqui la
    verificacion explicita (cargar el `User`, chequear `role`, rechazar si
    no corresponde) antes de persistir el cambio.
    """

    client_repository: ClientProfileRepository
    user_repository: UserRepository

    def execute(self, client_id: int, trainer_id: int) -> ClientProfile:
        raise NotImplementedError("Entrega 2: logica + validacion de rol pendiente")


@dataclass
class UpdateClientProfileUseCase:
    """RF003: editar datos de perfil de un cliente."""

    client_repository: ClientProfileRepository

    def execute(self, client: ClientProfile) -> ClientProfile:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class DeleteClientUseCase:
    """RF003: eliminar un cliente."""

    client_repository: ClientProfileRepository

    def execute(self, client_id: int) -> None:
        raise NotImplementedError("Entrega 2: logica pendiente")
