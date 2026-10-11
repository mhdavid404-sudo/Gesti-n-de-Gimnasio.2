"""Casos de uso del modulo Memberships (RF004, bases de RF006).

Entrega 2: `AssignMembershipUseCase` tiene logica real. RF006
(`DetectExpiringMembershipsUseCase`) pertenece al modulo
"Vencimientos/Notificaciones" (ver DECISIONES.md, orden fijo de modulos de
Entrega 2, que va DESPUES de Pagos) -- se deja intencionalmente sin
implementar en este modulo, no es un olvido.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.memberships.entities import ESTADOS_MEMBRESIA_VALIDOS, Membership
from src.domain.memberships.exceptions import (
    InvalidMembershipDateRangeError,
    InvalidMembershipStatusError,
    MembershipPlanNotFoundError,
)
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
)


@dataclass
class AssignMembershipUseCase:
    """RF004: asignar un plan de membresia a un cliente.

    Valida, en este orden:
    1. que `client_id` exista (`ClientProfileRepository.get_by_id`) --
       `ClientNotFoundError` (reusada de `domain.clients.exceptions`, ver
       nota en `domain/memberships/exceptions.py`).
    2. que `plan_id` exista (`MembershipPlanRepository.get_by_id`) --
       `MembershipPlanNotFoundError`.
    3. que `status` sea uno de `ESTADOS_MEMBRESIA_VALIDOS` --
       `InvalidMembershipStatusError`.
    4. que `end_date` sea estrictamente posterior a `start_date` --
       `InvalidMembershipDateRangeError`.

    Depende de `ClientProfileRepository` ademas de los dos repositorios de
    Memberships ya declarados en el esqueleto original -- mismo patron de
    orquestar varios repositorios de dominio desde un caso de uso de
    aplicacion que ya usa `RegisterClientUseCase` (modulo Clientes).
    """

    membership_repository: MembershipRepository
    plan_repository: MembershipPlanRepository
    client_repository: ClientProfileRepository

    def execute(self, membership: Membership) -> Membership:
        if self.client_repository.get_by_id(membership.client_id) is None:
            raise ClientNotFoundError(membership.client_id)

        if self.plan_repository.get_by_id(membership.plan_id) is None:
            raise MembershipPlanNotFoundError(membership.plan_id)

        if membership.status not in ESTADOS_MEMBRESIA_VALIDOS:
            raise InvalidMembershipStatusError(membership.status)

        if membership.end_date <= membership.start_date:
            raise InvalidMembershipDateRangeError()

        return self.membership_repository.add(membership)


@dataclass
class DetectExpiringMembershipsUseCase:
    """RF006: detectar membresias vencidas o proximas a vencer.

    FUERA DE ALCANCE del modulo Planes y Membresias (RF004). Pertenece al
    modulo "Vencimientos/Notificaciones" (ver DECISIONES.md) -- se deja sin
    implementar a proposito, junto con `GET /memberships/expiring` en el
    router, para no adelantar trabajo fuera del orden fijo de modulos.
    """

    membership_repository: MembershipRepository

    def execute(self, days_ahead: int = 7) -> list[Membership]:
        raise NotImplementedError("Entrega 2: modulo Vencimientos/Notificaciones, pendiente")
