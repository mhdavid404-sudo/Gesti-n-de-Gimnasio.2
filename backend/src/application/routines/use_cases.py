"""Casos de uso del modulo Routines.

Entrega 1: solo el esqueleto. Ver DECISIONES.md, correccion #4.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.routines.entities import Routine, RoutineAssignment, RoutineExercise
from src.domain.routines.repositories import (
    ExerciseRepository,
    RoutineAssignmentRepository,
    RoutineRepository,
)
from src.domain.users.repositories import UserRepository


@dataclass
class CreateRoutineUseCase:
    """RF007: crear una rutina.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos:
        `Routine.created_by` debe ser un `User` con `role == "entrenador"`
        o `role == "admin"`.
    La FK `routines.created_by -> users.id` NO valida el rol. Entrega 2
    debe implementar aqui la verificacion explicita antes de persistir.
    """

    routine_repository: RoutineRepository
    user_repository: UserRepository

    def execute(self, routine: Routine) -> Routine:
        raise NotImplementedError("Entrega 2: logica + validacion de rol pendiente")


@dataclass
class AddExerciseToRoutineUseCase:
    """RF007: agregar un ejercicio de catalogo a una rutina."""

    routine_repository: RoutineRepository
    exercise_repository: ExerciseRepository

    def execute(self, routine_exercise: RoutineExercise) -> RoutineExercise:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class AssignRoutineToClientUseCase:
    """RF007: asignar una rutina existente a un cliente."""

    assignment_repository: RoutineAssignmentRepository

    def execute(self, assignment: RoutineAssignment) -> RoutineAssignment:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class GetClientRoutineHistoryUseCase:
    """RF008: consultar el historial de rutinas asignadas a un cliente.

    Tambien sirve para RF013 (el cliente ve lo propio) y RF012 (el
    entrenador ve lo que tiene asignado) -- la diferencia de alcance por
    rol es responsabilidad de esta capa, filtrando por `client_id` o por
    `trainer_id` segun quien pregunta.
    """

    assignment_repository: RoutineAssignmentRepository

    def execute(self, client_id: int) -> list[RoutineAssignment]:
        raise NotImplementedError("Entrega 2: logica pendiente")
