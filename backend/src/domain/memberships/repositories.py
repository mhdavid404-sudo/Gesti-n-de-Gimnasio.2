"""Puertos (interfaces) del repositorio de Memberships.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.memberships.entities import Membership, MembershipPlan


class MembershipPlanRepository(ABC):
    @abstractmethod
    def get_by_id(self, plan_id: int) -> MembershipPlan | None: ...

    @abstractmethod
    def list_all(self) -> list[MembershipPlan]: ...

    @abstractmethod
    def add(self, plan: MembershipPlan) -> MembershipPlan: ...

    @abstractmethod
    def update(self, plan: MembershipPlan) -> MembershipPlan: ...

    @abstractmethod
    def delete(self, plan_id: int) -> None: ...


class MembershipRepository(ABC):
    @abstractmethod
    def get_by_id(self, membership_id: int) -> Membership | None: ...

    @abstractmethod
    def list_by_client(self, client_id: int) -> list[Membership]: ...

    @abstractmethod
    def list_expiring_before(self, cutoff_date) -> list[Membership]:
        """Usado por RF006 (notificar membresias por vencer/vencidas)."""
        ...

    @abstractmethod
    def add(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def update(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def delete(self, membership_id: int) -> None: ...
