"""Casos de uso del modulo Routines (RF007, RF008, RF012, RF013).

Entrega 2: logica real, antes `NotImplementedError` (ver DECISIONES.md).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.routines.entities import (
    ESTADOS_ASIGNACION_VALIDOS,
    Routine,
    RoutineAssignment,
    RoutineExercise,
)
from src.domain.routines.exceptions import (
    ExerciseNotFoundError,
    InvalidAssignmentStatusError,
    RoutineAssignmentNotFoundError,
    RoutineNotFoundError,
    UnauthorizedRoutineAssignmentError,
    UnauthorizedRoutineCreatorError,
)
from src.domain.routines.repositories import (
    ExerciseRepository,
    RoutineAssignmentRepository,
    RoutineRepository,
)
from src.domain.users.repositories import UserRepository

_ROLES_CREADORES_DE_RUTINA = ("entrenador", "admin")


@dataclass
class CreateRoutineUseCase:
    """RF007: crear una rutina.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos:
        `Routine.created_by` debe ser un `User` con `role == "entrenador"`
        o `role == "admin"`.
    La FK `routines.created_by -> users.id` NO valida el rol.

    Esta validacion de rol existe tanto aqui como en `require_role` del
    router (defensa en profundidad): el caso de uso no debe confiar en que
    SIEMPRE lo invoque un router protegido -- si en el futuro otro
    llamador invoca este caso de uso sin pasar por la API HTTP (ej. un
    script interno), la regla de negocio sigue protegida igual. Mismo
    criterio ya documentado en `RegisterPaymentUseCase` sobre
    `METODOS_PAGO_VALIDOS`/`ESTADOS_PAGO_VALIDOS`.
    """

    routine_repository: RoutineRepository
    user_repository: UserRepository

    def execute(self, routine: Routine) -> Routine:
        creator = self.user_repository.get_by_id(routine.created_by)
        if creator is None or creator.role not in _ROLES_CREADORES_DE_RUTINA:
            raise UnauthorizedRoutineCreatorError(routine.created_by)

        return self.routine_repository.add(routine)


@dataclass
class AddExerciseToRoutineUseCase:
    """RF007: agregar un ejercicio de catalogo a una rutina.

    Valida que la rutina y el ejercicio existan antes de crear el vinculo.
    """

    routine_repository: RoutineRepository
    exercise_repository: ExerciseRepository

    def execute(self, routine_exercise: RoutineExercise) -> RoutineExercise:
        if self.routine_repository.get_by_id(routine_exercise.routine_id) is None:
            raise RoutineNotFoundError(routine_exercise.routine_id)

        if self.exercise_repository.get_by_id(routine_exercise.exercise_id) is None:
            raise ExerciseNotFoundError(routine_exercise.exercise_id)

        return self.routine_repository.add_exercise(routine_exercise)


@dataclass
class AssignRoutineToClientUseCase:
    """RF007: asignar una rutina existente a un cliente.

    Valida, en este orden:
    1. que el cliente exista (`ClientNotFoundError`, reusada de
       `domain.clients.exceptions` -- mismo criterio ya aplicado por
       `AssignMembershipUseCase`).
    2. que la rutina exista (`RoutineNotFoundError`).
    3. que `status` sea uno de `ESTADOS_ASIGNACION_VALIDOS`
       (`InvalidAssignmentStatusError`).
    4. si quien asigna es `entrenador`, que el cliente este asignado a EL
       (mismo patron de ownership ya usado en `AssignMembershipUseCase`/
       `clients.py` -- `UnauthorizedRoutineAssignmentError` si no).

    `assigner_role`/`assigner_id` representan a quien asigna (ya resuelto
    server-side via `current_user`, nunca desde el body -- ver correccion
    de seguridad de `assigned_by` en `api/v1/schemas/routines.py`).
    """

    assignment_repository: RoutineAssignmentRepository
    routine_repository: RoutineRepository
    client_repository: ClientProfileRepository

    def execute(
        self,
        assignment: RoutineAssignment,
        assigner_role: str,
        assigner_id: int,
    ) -> RoutineAssignment:
        client = self.client_repository.get_by_id(assignment.client_id)
        if client is None:
            raise ClientNotFoundError(assignment.client_id)

        if self.routine_repository.get_by_id(assignment.routine_id) is None:
            raise RoutineNotFoundError(assignment.routine_id)

        if assignment.status not in ESTADOS_ASIGNACION_VALIDOS:
            raise InvalidAssignmentStatusError(assignment.status)

        if assigner_role == "entrenador" and client.trainer_id != assigner_id:
            raise UnauthorizedRoutineAssignmentError(assignment.client_id)

        return self.assignment_repository.add(assignment)


@dataclass
class UpdateRoutineAssignmentUseCase:
    """RF012: el entrenador actualiza (status/notes) las rutinas asignadas
    a SUS clientes. Pieza nueva, no prevista en el esqueleto original --
    ver DECISIONES.md ("pieza que completa RF012 para este modulo").

    Valida, en este orden:
    1. que la asignacion exista (`RoutineAssignmentNotFoundError`).
    2. que `status`, si viene, sea uno de `ESTADOS_ASIGNACION_VALIDOS`
       (`InvalidAssignmentStatusError`).
    3. si quien actualiza es `entrenador`, que el cliente de esa
       asignacion este asignado a EL (`UnauthorizedRoutineAssignmentError`
       si no) -- mismo patron de ownership que `AssignRoutineToClientUseCase`.

    `cliente` nunca llega a ejecutar esto -- RF013 es de solo lectura, el
    bloqueo real ocurre en el router via `require_role`.
    """

    assignment_repository: RoutineAssignmentRepository
    client_repository: ClientProfileRepository

    def execute(
        self,
        assignment_id: int,
        status_value: str | None,
        notes: str | None,
        updater_role: str,
        updater_id: int,
    ) -> RoutineAssignment:
        existing = self.assignment_repository.get_by_id(assignment_id)
        if existing is None:
            raise RoutineAssignmentNotFoundError(assignment_id)

        if status_value is not None and status_value not in ESTADOS_ASIGNACION_VALIDOS:
            raise InvalidAssignmentStatusError(status_value)

        if updater_role == "entrenador":
            client = self.client_repository.get_by_id(existing.client_id)
            if client is None or client.trainer_id != updater_id:
                raise UnauthorizedRoutineAssignmentError(existing.client_id)

        existing.status = status_value if status_value is not None else existing.status
        existing.notes = notes if notes is not None else existing.notes

        return self.assignment_repository.update(existing)


@dataclass
class GetClientRoutineHistoryUseCase:
    """RF008: consultar el historial de rutinas asignadas a un cliente.

    Tambien sirve para RF013 (el cliente ve lo propio) y RF012 (el
    entrenador ve lo que tiene asignado) -- la diferencia de alcance por
    rol es responsabilidad del ROUTER (ownership por dato, igual que
    `clients.py`/`payments.py`), no de este caso de uso, que es un paso
    trivial sobre el repositorio.
    """

    assignment_repository: RoutineAssignmentRepository

    def execute(self, client_id: int) -> list[RoutineAssignment]:
        return self.assignment_repository.list_by_client(client_id)
