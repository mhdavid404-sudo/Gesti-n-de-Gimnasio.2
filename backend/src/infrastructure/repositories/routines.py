"""Implementacion concreta (SQLAlchemy) de los puertos de Routines."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.routines.entities import (
    Exercise,
    Routine,
    RoutineAssignment,
    RoutineExercise,
)
from src.domain.routines.repositories import (
    ExerciseRepository,
    RoutineAssignmentRepository,
    RoutineRepository,
)
from src.infrastructure.db.models.clients import ClientProfileModel
from src.infrastructure.db.models.routines import (
    ExerciseModel,
    RoutineAssignmentModel,
    RoutineExerciseModel,
    RoutineModel,
)


def _exercise_to_entity(model: ExerciseModel) -> Exercise:
    return Exercise(
        id=model.id,
        name=model.name,
        muscle_group=model.muscle_group,
        description=model.description,
        created_at=model.created_at,
    )


def _routine_to_entity(model: RoutineModel) -> Routine:
    return Routine(
        id=model.id,
        name=model.name,
        created_by=model.created_by,
        description=model.description,
        created_at=model.created_at,
    )


def _routine_exercise_to_entity(model: RoutineExerciseModel) -> RoutineExercise:
    return RoutineExercise(
        id=model.id,
        routine_id=model.routine_id,
        exercise_id=model.exercise_id,
        sets=model.sets,
        reps=model.reps,
        order_index=model.order_index,
        rest_seconds=model.rest_seconds,
        notes=model.notes,
    )


def _assignment_to_entity(model: RoutineAssignmentModel) -> RoutineAssignment:
    return RoutineAssignment(
        id=model.id,
        routine_id=model.routine_id,
        client_id=model.client_id,
        assigned_by=model.assigned_by,
        assigned_date=model.assigned_date,
        status=model.status,
    )


class SqlAlchemyExerciseRepository(ExerciseRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, exercise_id: int) -> Exercise | None:
        model = self._session.get(ExerciseModel, exercise_id)
        return _exercise_to_entity(model) if model else None

    def list_all(self) -> list[Exercise]:
        models = self._session.execute(select(ExerciseModel)).scalars()
        return [_exercise_to_entity(m) for m in models]

    def add(self, exercise: Exercise) -> Exercise:
        model = ExerciseModel(
            name=exercise.name,
            muscle_group=exercise.muscle_group,
            description=exercise.description,
        )
        self._session.add(model)
        self._session.flush()
        return _exercise_to_entity(model)

    def update(self, exercise: Exercise) -> Exercise:
        model = self._session.get(ExerciseModel, exercise.id)
        if model is None:
            raise ValueError(f"Exercise {exercise.id} no existe")
        model.name = exercise.name
        model.muscle_group = exercise.muscle_group
        model.description = exercise.description
        self._session.flush()
        return _exercise_to_entity(model)

    def delete(self, exercise_id: int) -> None:
        model = self._session.get(ExerciseModel, exercise_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyRoutineRepository(RoutineRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, routine_id: int) -> Routine | None:
        model = self._session.get(RoutineModel, routine_id)
        return _routine_to_entity(model) if model else None

    def list_all(self) -> list[Routine]:
        models = self._session.execute(select(RoutineModel)).scalars()
        return [_routine_to_entity(m) for m in models]

    def add(self, routine: Routine) -> Routine:
        model = RoutineModel(
            name=routine.name,
            created_by=routine.created_by,
            description=routine.description,
        )
        self._session.add(model)
        self._session.flush()
        return _routine_to_entity(model)

    def update(self, routine: Routine) -> Routine:
        model = self._session.get(RoutineModel, routine.id)
        if model is None:
            raise ValueError(f"Routine {routine.id} no existe")
        model.name = routine.name
        model.description = routine.description
        self._session.flush()
        return _routine_to_entity(model)

    def delete(self, routine_id: int) -> None:
        model = self._session.get(RoutineModel, routine_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()

    def list_exercises(self, routine_id: int) -> list[RoutineExercise]:
        models = self._session.execute(
            select(RoutineExerciseModel)
            .where(RoutineExerciseModel.routine_id == routine_id)
            .order_by(RoutineExerciseModel.order_index)
        ).scalars()
        return [_routine_exercise_to_entity(m) for m in models]

    def add_exercise(self, routine_exercise: RoutineExercise) -> RoutineExercise:
        model = RoutineExerciseModel(
            routine_id=routine_exercise.routine_id,
            exercise_id=routine_exercise.exercise_id,
            sets=routine_exercise.sets,
            reps=routine_exercise.reps,
            order_index=routine_exercise.order_index,
            rest_seconds=routine_exercise.rest_seconds,
            notes=routine_exercise.notes,
        )
        self._session.add(model)
        self._session.flush()
        return _routine_exercise_to_entity(model)

    def remove_exercise(self, routine_exercise_id: int) -> None:
        model = self._session.get(RoutineExerciseModel, routine_exercise_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyRoutineAssignmentRepository(RoutineAssignmentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, assignment_id: int) -> RoutineAssignment | None:
        model = self._session.get(RoutineAssignmentModel, assignment_id)
        return _assignment_to_entity(model) if model else None

    def list_by_client(self, client_id: int) -> list[RoutineAssignment]:
        models = self._session.execute(
            select(RoutineAssignmentModel).where(
                RoutineAssignmentModel.client_id == client_id
            )
        ).scalars()
        return [_assignment_to_entity(m) for m in models]

    def list_by_trainer(self, trainer_id: int) -> list[RoutineAssignment]:
        models = self._session.execute(
            select(RoutineAssignmentModel)
            .join(
                ClientProfileModel,
                ClientProfileModel.id == RoutineAssignmentModel.client_id,
            )
            .where(ClientProfileModel.trainer_id == trainer_id)
        ).scalars()
        return [_assignment_to_entity(m) for m in models]

    def add(self, assignment: RoutineAssignment) -> RoutineAssignment:
        model = RoutineAssignmentModel(
            routine_id=assignment.routine_id,
            client_id=assignment.client_id,
            assigned_by=assignment.assigned_by,
            assigned_date=assignment.assigned_date,
            status=assignment.status,
        )
        self._session.add(model)
        self._session.flush()
        return _assignment_to_entity(model)

    def update(self, assignment: RoutineAssignment) -> RoutineAssignment:
        model = self._session.get(RoutineAssignmentModel, assignment.id)
        if model is None:
            raise ValueError(f"RoutineAssignment {assignment.id} no existe")
        model.status = assignment.status
        self._session.flush()
        return _assignment_to_entity(model)

    def delete(self, assignment_id: int) -> None:
        model = self._session.get(RoutineAssignmentModel, assignment_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
