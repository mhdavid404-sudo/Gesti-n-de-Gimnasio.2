"""Puertos (interfaces) del repositorio de Memberships.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.memberships.entities import (
    Membership,
    MembershipPlan,
    MembershipRenewal,
    MembershipService,
    PlanService,
    Service,
)


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
    def has_memberships_for_plan(self, plan_id: int) -> bool:
        """True si existe al menos una `Membership` sobre este plan --
        usado por `DeleteOrDeactivateMembershipPlanUseCase` (Entrega 3)."""
        ...

    @abstractmethod
    def add(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def update(self, membership: Membership) -> Membership: ...

    @abstractmethod
    def delete(self, membership_id: int) -> None: ...


class ServiceRepository(ABC):
    @abstractmethod
    def get_by_id(self, service_id: int) -> Service | None: ...

    @abstractmethod
    def list_all(self) -> list[Service]: ...

    @abstractmethod
    def add(self, service: Service) -> Service: ...

    @abstractmethod
    def update(self, service: Service) -> Service: ...

    @abstractmethod
    def delete(self, service_id: int) -> None: ...

    @abstractmethod
    def has_contracts(self, service_id: int) -> bool:
        """True si existe al menos un `MembershipService` que referencia
        este servicio -- usado para decidir desactivar vs. eliminar."""
        ...


class PlanServiceRepository(ABC):
    """Puerto de la tabla puente `plan_services` (que `Service` incluye
    cada `MembershipPlan`)."""

    @abstractmethod
    def list_for_plan(self, plan_id: int) -> list[PlanService]: ...

    @abstractmethod
    def exists(self, plan_id: int, service_id: int) -> bool: ...

    @abstractmethod
    def add(self, plan_service: PlanService) -> PlanService: ...

    @abstractmethod
    def remove(self, plan_id: int, service_id: int) -> None: ...


class MembershipServiceRepository(ABC):
    """Puerto de `membership_services` -- servicios extra CONTRATADOS por
    un cliente sobre una membresia (distinto de `PlanServiceRepository`,
    que solo modela "que incluye el plan")."""

    @abstractmethod
    def get_by_id(self, membership_service_id: int) -> MembershipService | None: ...

    @abstractmethod
    def list_by_membership(self, membership_id: int) -> list[MembershipService]: ...

    @abstractmethod
    def add(self, membership_service: MembershipService) -> MembershipService: ...

    @abstractmethod
    def update(self, membership_service: MembershipService) -> MembershipService: ...


class MembershipRenewalRepository(ABC):
    """Puerto de `membership_renewals` -- historial de renovaciones,
    usado para "deshacer la ultima renovacion" (BUG-12)."""

    @abstractmethod
    def get_by_id(self, renewal_id: int) -> MembershipRenewal | None: ...

    @abstractmethod
    def list_by_membership(self, membership_id: int) -> list[MembershipRenewal]:
        """Orden mas reciente primero -- el llamador toma el primero como
        "la ultima renovacion" cuando lo necesita."""
        ...

    @abstractmethod
    def get_latest_for_membership(self, membership_id: int) -> MembershipRenewal | None: ...

    @abstractmethod
    def add(self, renewal: MembershipRenewal) -> MembershipRenewal: ...

    @abstractmethod
    def update(self, renewal: MembershipRenewal) -> MembershipRenewal: ...
