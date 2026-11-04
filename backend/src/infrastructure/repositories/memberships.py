"""Implementacion concreta (SQLAlchemy) de los puertos de Memberships."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.memberships.entities import (
    Membership,
    MembershipPlan,
    MembershipService,
    PlanService,
    Service,
)
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
    MembershipServiceRepository,
    PlanServiceRepository,
    ServiceRepository,
)
from src.infrastructure.db.models.memberships import (
    MembershipModel,
    MembershipPlanModel,
    MembershipServiceModel,
    PlanServiceModel,
    ServiceModel,
)


def _plan_to_entity(model: MembershipPlanModel) -> MembershipPlan:
    return MembershipPlan(
        id=model.id,
        name=model.name,
        price=model.price,
        duration_days=model.duration_days,
        description=model.description,
        benefits=list(model.benefits or []),
        is_active=model.is_active,
        created_at=model.created_at,
    )


def _service_to_entity(model: ServiceModel) -> Service:
    return Service(
        id=model.id,
        name=model.name,
        price=model.price,
        billing_period=model.billing_period,
        description=model.description,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def _plan_service_to_entity(model: PlanServiceModel) -> PlanService:
    return PlanService(plan_id=model.plan_id, service_id=model.service_id)


def _membership_service_to_entity(model: MembershipServiceModel) -> MembershipService:
    return MembershipService(
        id=model.id,
        membership_id=model.membership_id,
        service_id=model.service_id,
        price_at_purchase=model.price_at_purchase,
        start_date=model.start_date,
        end_date=model.end_date,
        status=model.status,
        created_at=model.created_at,
    )


def _membership_to_entity(model: MembershipModel) -> Membership:
    return Membership(
        id=model.id,
        client_id=model.client_id,
        plan_id=model.plan_id,
        start_date=model.start_date,
        end_date=model.end_date,
        status=model.status,
        created_at=model.created_at,
    )


class SqlAlchemyMembershipPlanRepository(MembershipPlanRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, plan_id: int) -> MembershipPlan | None:
        model = self._session.get(MembershipPlanModel, plan_id)
        return _plan_to_entity(model) if model else None

    def list_all(self) -> list[MembershipPlan]:
        models = self._session.execute(select(MembershipPlanModel)).scalars()
        return [_plan_to_entity(m) for m in models]

    def add(self, plan: MembershipPlan) -> MembershipPlan:
        model = MembershipPlanModel(
            name=plan.name,
            price=plan.price,
            duration_days=plan.duration_days,
            description=plan.description,
            benefits=list(plan.benefits),
            is_active=plan.is_active,
        )
        self._session.add(model)
        self._session.flush()
        return _plan_to_entity(model)

    def update(self, plan: MembershipPlan) -> MembershipPlan:
        model = self._session.get(MembershipPlanModel, plan.id)
        if model is None:
            raise ValueError(f"MembershipPlan {plan.id} no existe")
        model.name = plan.name
        model.price = plan.price
        model.duration_days = plan.duration_days
        model.description = plan.description
        model.benefits = list(plan.benefits)
        model.is_active = plan.is_active
        self._session.flush()
        return _plan_to_entity(model)

    def delete(self, plan_id: int) -> None:
        model = self._session.get(MembershipPlanModel, plan_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyMembershipRepository(MembershipRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, membership_id: int) -> Membership | None:
        model = self._session.get(MembershipModel, membership_id)
        return _membership_to_entity(model) if model else None

    def list_by_client(self, client_id: int) -> list[Membership]:
        models = self._session.execute(
            select(MembershipModel).where(MembershipModel.client_id == client_id)
        ).scalars()
        return [_membership_to_entity(m) for m in models]

    def list_expiring_before(self, cutoff_date: date) -> list[Membership]:
        models = self._session.execute(
            select(MembershipModel).where(MembershipModel.end_date <= cutoff_date)
        ).scalars()
        return [_membership_to_entity(m) for m in models]

    def has_memberships_for_plan(self, plan_id: int) -> bool:
        return (
            self._session.execute(
                select(MembershipModel.id).where(MembershipModel.plan_id == plan_id).limit(1)
            ).first()
            is not None
        )

    def add(self, membership: Membership) -> Membership:
        model = MembershipModel(
            client_id=membership.client_id,
            plan_id=membership.plan_id,
            start_date=membership.start_date,
            end_date=membership.end_date,
            status=membership.status,
        )
        self._session.add(model)
        self._session.flush()
        return _membership_to_entity(model)

    def update(self, membership: Membership) -> Membership:
        model = self._session.get(MembershipModel, membership.id)
        if model is None:
            raise ValueError(f"Membership {membership.id} no existe")
        model.plan_id = membership.plan_id
        model.start_date = membership.start_date
        model.end_date = membership.end_date
        model.status = membership.status
        self._session.flush()
        return _membership_to_entity(model)

    def delete(self, membership_id: int) -> None:
        model = self._session.get(MembershipModel, membership_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, service_id: int) -> Service | None:
        model = self._session.get(ServiceModel, service_id)
        return _service_to_entity(model) if model else None

    def list_all(self) -> list[Service]:
        models = self._session.execute(select(ServiceModel)).scalars()
        return [_service_to_entity(m) for m in models]

    def add(self, service: Service) -> Service:
        model = ServiceModel(
            name=service.name,
            price=service.price,
            billing_period=service.billing_period,
            description=service.description,
            is_active=service.is_active,
        )
        self._session.add(model)
        self._session.flush()
        return _service_to_entity(model)

    def update(self, service: Service) -> Service:
        model = self._session.get(ServiceModel, service.id)
        if model is None:
            raise ValueError(f"Service {service.id} no existe")
        model.name = service.name
        model.price = service.price
        model.billing_period = service.billing_period
        model.description = service.description
        model.is_active = service.is_active
        self._session.flush()
        return _service_to_entity(model)

    def delete(self, service_id: int) -> None:
        model = self._session.get(ServiceModel, service_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def has_contracts(self, service_id: int) -> bool:
        return (
            self._session.execute(
                select(MembershipServiceModel.id)
                .where(MembershipServiceModel.service_id == service_id)
                .limit(1)
            ).first()
            is not None
        )


class SqlAlchemyPlanServiceRepository(PlanServiceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_plan(self, plan_id: int) -> list[PlanService]:
        models = self._session.execute(
            select(PlanServiceModel).where(PlanServiceModel.plan_id == plan_id)
        ).scalars()
        return [_plan_service_to_entity(m) for m in models]

    def exists(self, plan_id: int, service_id: int) -> bool:
        return (
            self._session.get(PlanServiceModel, {"plan_id": plan_id, "service_id": service_id})
            is not None
        )

    def add(self, plan_service: PlanService) -> PlanService:
        model = PlanServiceModel(plan_id=plan_service.plan_id, service_id=plan_service.service_id)
        self._session.add(model)
        self._session.flush()
        return _plan_service_to_entity(model)

    def remove(self, plan_id: int, service_id: int) -> None:
        model = self._session.get(PlanServiceModel, {"plan_id": plan_id, "service_id": service_id})
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyMembershipServiceRepository(MembershipServiceRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, membership_service_id: int) -> MembershipService | None:
        model = self._session.get(MembershipServiceModel, membership_service_id)
        return _membership_service_to_entity(model) if model else None

    def list_by_membership(self, membership_id: int) -> list[MembershipService]:
        models = self._session.execute(
            select(MembershipServiceModel).where(
                MembershipServiceModel.membership_id == membership_id
            )
        ).scalars()
        return [_membership_service_to_entity(m) for m in models]

    def add(self, membership_service: MembershipService) -> MembershipService:
        model = MembershipServiceModel(
            membership_id=membership_service.membership_id,
            service_id=membership_service.service_id,
            price_at_purchase=membership_service.price_at_purchase,
            start_date=membership_service.start_date,
            end_date=membership_service.end_date,
            status=membership_service.status,
        )
        self._session.add(model)
        self._session.flush()
        return _membership_service_to_entity(model)

    def update(self, membership_service: MembershipService) -> MembershipService:
        model = self._session.get(MembershipServiceModel, membership_service.id)
        if model is None:
            raise ValueError(f"MembershipService {membership_service.id} no existe")
        model.status = membership_service.status
        model.end_date = membership_service.end_date
        self._session.flush()
        return _membership_service_to_entity(model)
