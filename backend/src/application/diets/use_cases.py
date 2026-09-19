"""Casos de uso del modulo Diets.

Entrega 1: solo el esqueleto. Ver DECISIONES.md, correccion #4.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.diets.entities import DietAssignment, DietPlan
from src.domain.diets.repositories import DietAssignmentRepository, DietPlanRepository
from src.domain.users.repositories import UserRepository


@dataclass
class CreateDietPlanUseCase:
    """RF009: crear un plan de dieta.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos: `DietPlan.created_by` debe ser un
    `User` con `role == "entrenador"` o `role == "admin"`, igual que
    `Routine.created_by`. La FK no lo garantiza.
    """

    diet_plan_repository: DietPlanRepository
    user_repository: UserRepository

    def execute(self, diet_plan: DietPlan) -> DietPlan:
        raise NotImplementedError("Entrega 2: logica + validacion de rol pendiente")


@dataclass
class AssignDietToClientUseCase:
    """RF009: asignar un plan de dieta a un cliente."""

    assignment_repository: DietAssignmentRepository

    def execute(self, assignment: DietAssignment) -> DietAssignment:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class GetClientDietHistoryUseCase:
    """RF012/RF013: consultar dietas asignadas a un cliente (segun rol)."""

    assignment_repository: DietAssignmentRepository

    def execute(self, client_id: int) -> list[DietAssignment]:
        raise NotImplementedError("Entrega 2: logica pendiente")
