"""Casos de uso del modulo Diets (RF009, RF012, RF013).

Entrega 2: logica real, antes `NotImplementedError` (ver DECISIONES.md).
Mismo patron que `application/routines/use_cases.py` -- Diets es casi
identico en estructura a Routines, solo que mas simple: un `DietPlan` no
tiene una tabla puente de sub-items equivalente a
`Exercise`/`RoutineExercise` (es un plan plano con `calories_target`).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.diets.entities import ESTADOS_ASIGNACION_VALIDOS, DietAssignment, DietPlan
from src.domain.diets.exceptions import (
    DietAssignmentNotFoundError,
    DietPlanNotFoundError,
    InvalidDietAssignmentStatusError,
    UnauthorizedDietAssignmentError,
    UnauthorizedDietPlanCreatorError,
)
from src.domain.diets.repositories import DietAssignmentRepository, DietPlanRepository
from src.domain.users.repositories import UserRepository

_ROLES_CREADORES_DE_DIETA = ("entrenador", "admin")


@dataclass
class CreateDietPlanUseCase:
    """RF009: crear un plan de dieta.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos:
        `DietPlan.created_by` debe ser un `User` con `role == "entrenador"`
        o `role == "admin"`.
    La FK `diet_plans.created_by -> users.id` NO valida el rol.

    Mismo criterio de defensa en profundidad ya documentado en
    `CreateRoutineUseCase`: esta validacion existe aqui ademas del
    `require_role` del router.
    """

    diet_plan_repository: DietPlanRepository
    user_repository: UserRepository

    def execute(self, diet_plan: DietPlan) -> DietPlan:
        creator = self.user_repository.get_by_id(diet_plan.created_by)
        if creator is None or creator.role not in _ROLES_CREADORES_DE_DIETA:
            raise UnauthorizedDietPlanCreatorError(diet_plan.created_by)

        return self.diet_plan_repository.add(diet_plan)


@dataclass
class AssignDietToClientUseCase:
    """RF009: asignar un plan de dieta existente a un cliente.

    Valida, en este orden:
    1. que el cliente exista (`ClientNotFoundError`, reusada de
       `domain.clients.exceptions` -- mismo criterio ya aplicado por
       `AssignRoutineToClientUseCase`).
    2. que el plan de dieta exista (`DietPlanNotFoundError`).
    3. que `status` sea uno de `ESTADOS_ASIGNACION_VALIDOS`
       (`InvalidDietAssignmentStatusError`).
    4. si quien asigna es `entrenador`, que el cliente este asignado a EL
       (mismo patron de ownership que `AssignRoutineToClientUseCase` --
       `UnauthorizedDietAssignmentError` si no).

    `assigner_role`/`assigner_id` representan a quien asigna (ya resuelto
    server-side via `current_user`, nunca desde el body -- ver correccion
    de seguridad de `assigned_by` en `api/v1/schemas/diets.py`).
    """

    assignment_repository: DietAssignmentRepository
    diet_plan_repository: DietPlanRepository
    client_repository: ClientProfileRepository

    def execute(
        self,
        assignment: DietAssignment,
        assigner_role: str,
        assigner_id: int,
    ) -> DietAssignment:
        client = self.client_repository.get_by_id(assignment.client_id)
        if client is None:
            raise ClientNotFoundError(assignment.client_id)

        if self.diet_plan_repository.get_by_id(assignment.diet_plan_id) is None:
            raise DietPlanNotFoundError(assignment.diet_plan_id)

        if assignment.status not in ESTADOS_ASIGNACION_VALIDOS:
            raise InvalidDietAssignmentStatusError(assignment.status)

        if assigner_role == "entrenador" and client.trainer_id != assigner_id:
            raise UnauthorizedDietAssignmentError(assignment.client_id)

        return self.assignment_repository.add(assignment)


@dataclass
class UpdateDietAssignmentUseCase:
    """RF012: el entrenador actualiza (status/notes) las dietas asignadas
    a SUS clientes. Pieza nueva, no prevista en el esqueleto original --
    mismo criterio que `UpdateRoutineAssignmentUseCase` en Rutinas.

    Valida, en este orden:
    1. que la asignacion exista (`DietAssignmentNotFoundError`).
    2. que `status`, si viene, sea uno de `ESTADOS_ASIGNACION_VALIDOS`
       (`InvalidDietAssignmentStatusError`).
    3. si quien actualiza es `entrenador`, que el cliente de esa
       asignacion este asignado a EL (`UnauthorizedDietAssignmentError`
       si no) -- mismo patron de ownership que `AssignDietToClientUseCase`.

    `cliente` nunca llega a ejecutar esto -- RF013 es de solo lectura, el
    bloqueo real ocurre en el router via `require_role`.
    """

    assignment_repository: DietAssignmentRepository
    client_repository: ClientProfileRepository

    def execute(
        self,
        assignment_id: int,
        status_value: str | None,
        notes: str | None,
        updater_role: str,
        updater_id: int,
    ) -> DietAssignment:
        existing = self.assignment_repository.get_by_id(assignment_id)
        if existing is None:
            raise DietAssignmentNotFoundError(assignment_id)

        if status_value is not None and status_value not in ESTADOS_ASIGNACION_VALIDOS:
            raise InvalidDietAssignmentStatusError(status_value)

        if updater_role == "entrenador":
            client = self.client_repository.get_by_id(existing.client_id)
            if client is None or client.trainer_id != updater_id:
                raise UnauthorizedDietAssignmentError(existing.client_id)

        existing.status = status_value if status_value is not None else existing.status
        existing.notes = notes if notes is not None else existing.notes

        return self.assignment_repository.update(existing)


@dataclass
class GetClientDietHistoryUseCase:
    """RF012/RF013: consultar el historial de dietas asignadas a un
    cliente.

    Tambien sirve para RF013 (el cliente ve lo propio) y RF012 (el
    entrenador ve lo que tiene asignado) -- la diferencia de alcance por
    rol es responsabilidad del ROUTER (ownership por dato, igual que
    `GetClientRoutineHistoryUseCase`), no de este caso de uso, que es un
    paso trivial sobre el repositorio.
    """

    assignment_repository: DietAssignmentRepository

    def execute(self, client_id: int) -> list[DietAssignment]:
        return self.assignment_repository.list_by_client(client_id)
