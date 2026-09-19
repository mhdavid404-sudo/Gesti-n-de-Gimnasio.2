"""Implementacion concreta (SQLAlchemy) de los puertos de Memberships."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.memberships.entities import Membership, MembershipPlan
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
)
from src.infrastructure.db.models.memberships import MembershipModel, MembershipPlanModel


def _plan_to_entity(model: MembershipPlanModel) -> MembershipPlan:
    return MembershipPlan(
        id=model.id,
        name=model.name,
        price=model.price,
        duration_days=model.duration_days,
        description=model.description,
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
