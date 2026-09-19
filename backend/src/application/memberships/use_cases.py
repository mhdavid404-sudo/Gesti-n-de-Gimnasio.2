"""Casos de uso del modulo Memberships. Entrega 1: solo el esqueleto."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.memberships.entities import Membership, MembershipPlan
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
)


@dataclass
class AssignMembershipUseCase:
    """RF004: asignar un plan de membresia a un cliente."""

    membership_repository: MembershipRepository
    plan_repository: MembershipPlanRepository

    def execute(self, membership: Membership) -> Membership:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class DetectExpiringMembershipsUseCase:
    """RF006: detectar membresias vencidas o proximas a vencer.

    Entrega 2 debe: correr sobre `list_expiring_before`, actualizar
    `status` a "vencida" cuando corresponda y disparar una `Notification`
    (modulo notifications) por cada caso.
    """

    membership_repository: MembershipRepository

    def execute(self, days_ahead: int = 7) -> list[Membership]:
        raise NotImplementedError("Entrega 2: logica pendiente")
