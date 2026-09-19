"""Puertos (interfaces) del repositorio de Routines.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.routines.entities import (
    Exercise,
    Routine,
    RoutineAssignment,
    RoutineExercise,
)


class ExerciseRepository(ABC):
    @abstractmethod
    def get_by_id(self, exercise_id: int) -> Exercise | None: ...

    @abstractmethod
    def list_all(self) -> list[Exercise]: ...

    @abstractmethod
    def add(self, exercise: Exercise) -> Exercise: ...

    @abstractmethod
    def update(self, exercise: Exercise) -> Exercise: ...

    @abstractmethod
    def delete(self, exercise_id: int) -> None: ...


class RoutineRepository(ABC):
    @abstractmethod
    def get_by_id(self, routine_id: int) -> Routine | None: ...

    @abstractmethod
    def list_all(self) -> list[Routine]: ...

    @abstractmethod
    def add(self, routine: Routine) -> Routine: ...

    @abstractmethod
    def update(self, routine: Routine) -> Routine: ...

    @abstractmethod
    def delete(self, routine_id: int) -> None: ...

    @abstractmethod
    def list_exercises(self, routine_id: int) -> list[RoutineExercise]: ...

    @abstractmethod
    def add_exercise(self, routine_exercise: RoutineExercise) -> RoutineExercise: ...

    @abstractmethod
    def remove_exercise(self, routine_exercise_id: int) -> None: ...


class RoutineAssignmentRepository(ABC):
    @abstractmethod
    def get_by_id(self, assignment_id: int) -> RoutineAssignment | None: ...

    @abstractmethod
    def list_by_client(self, client_id: int) -> list[RoutineAssignment]:
        """Usado por RF008 (historial) y RF013 (cliente ve lo propio)."""
        ...

    @abstractmethod
    def list_by_trainer(self, trainer_id: int) -> list[RoutineAssignment]:
        """Usado por RF012 (entrenador ve/actualiza asignados)."""
        ...

    @abstractmethod
    def add(self, assignment: RoutineAssignment) -> RoutineAssignment: ...

    @abstractmethod
    def update(self, assignment: RoutineAssignment) -> RoutineAssignment: ...

    @abstractmethod
    def delete(self, assignment_id: int) -> None: ...
