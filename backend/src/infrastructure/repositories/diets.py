"""Implementacion concreta (SQLAlchemy) de los puertos de Diets."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.diets.entities import DietAssignment, DietPlan
from src.domain.diets.repositories import DietAssignmentRepository, DietPlanRepository
from src.infrastructure.db.models.clients import ClientProfileModel
from src.infrastructure.db.models.diets import DietAssignmentModel, DietPlanModel


def _plan_to_entity(model: DietPlanModel) -> DietPlan:
    return DietPlan(
        id=model.id,
        name=model.name,
        created_by=model.created_by,
        description=model.description,
        calories_target=model.calories_target,
        created_at=model.created_at,
    )


def _assignment_to_entity(model: DietAssignmentModel) -> DietAssignment:
    return DietAssignment(
        id=model.id,
        diet_plan_id=model.diet_plan_id,
        client_id=model.client_id,
        assigned_by=model.assigned_by,
        assigned_date=model.assigned_date,
        status=model.status,
    )


class SqlAlchemyDietPlanRepository(DietPlanRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, diet_plan_id: int) -> DietPlan | None:
        model = self._session.get(DietPlanModel, diet_plan_id)
        return _plan_to_entity(model) if model else None

    def list_all(self) -> list[DietPlan]:
        models = self._session.execute(select(DietPlanModel)).scalars()
        return [_plan_to_entity(m) for m in models]

    def add(self, diet_plan: DietPlan) -> DietPlan:
        model = DietPlanModel(
            name=diet_plan.name,
            created_by=diet_plan.created_by,
            description=diet_plan.description,
            calories_target=diet_plan.calories_target,
        )
        self._session.add(model)
        self._session.flush()
        return _plan_to_entity(model)

    def update(self, diet_plan: DietPlan) -> DietPlan:
        model = self._session.get(DietPlanModel, diet_plan.id)
        if model is None:
            raise ValueError(f"DietPlan {diet_plan.id} no existe")
        model.name = diet_plan.name
        model.description = diet_plan.description
        model.calories_target = diet_plan.calories_target
        self._session.flush()
        return _plan_to_entity(model)

    def delete(self, diet_plan_id: int) -> None:
        model = self._session.get(DietPlanModel, diet_plan_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyDietAssignmentRepository(DietAssignmentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, assignment_id: int) -> DietAssignment | None:
        model = self._session.get(DietAssignmentModel, assignment_id)
        return _assignment_to_entity(model) if model else None

    def list_by_client(self, client_id: int) -> list[DietAssignment]:
        models = self._session.execute(
            select(DietAssignmentModel).where(
                DietAssignmentModel.client_id == client_id
            )
        ).scalars()
        return [_assignment_to_entity(m) for m in models]

    def list_by_trainer(self, trainer_id: int) -> list[DietAssignment]:
        models = self._session.execute(
            select(DietAssignmentModel)
            .join(
                ClientProfileModel,
                ClientProfileModel.id == DietAssignmentModel.client_id,
            )
            .where(ClientProfileModel.trainer_id == trainer_id)
        ).scalars()
        return [_assignment_to_entity(m) for m in models]

    def add(self, assignment: DietAssignment) -> DietAssignment:
        model = DietAssignmentModel(
            diet_plan_id=assignment.diet_plan_id,
            client_id=assignment.client_id,
            assigned_by=assignment.assigned_by,
            assigned_date=assignment.assigned_date,
            status=assignment.status,
        )
        self._session.add(model)
        self._session.flush()
        return _assignment_to_entity(model)

    def update(self, assignment: DietAssignment) -> DietAssignment:
        model = self._session.get(DietAssignmentModel, assignment.id)
        if model is None:
            raise ValueError(f"DietAssignment {assignment.id} no existe")
        model.status = assignment.status
        self._session.flush()
        return _assignment_to_entity(model)

    def delete(self, assignment_id: int) -> None:
        model = self._session.get(DietAssignmentModel, assignment_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
