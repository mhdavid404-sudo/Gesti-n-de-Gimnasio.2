"""Excepciones de dominio del modulo Routines (RF007, RF008, RF012, RF013).

Mismo patron que `domain/clients/exceptions.py` y `domain/memberships/
exceptions.py`: el dominio no conoce HTTP ni FastAPI. Estos casos de uso
(`application/routines/use_cases.py`) lanzan estas excepciones; la
traduccion a `HTTPException`/codigo de estado ocurre unicamente en
`api/v1/routers/routines.py`.

La falta de existencia del CLIENTE (`client_id`) se senaliza reusando
`domain.clients.exceptions.ClientNotFoundError` -- mismo criterio ya
aplicado por `application/memberships/use_cases.py` (no se duplica un
segundo tipo de excepcion para el mismo caso real).
"""

from __future__ import annotations


class UnauthorizedRoutineCreatorError(Exception):
    """`created_by` no es un `User` con role "entrenador" o "admin".

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4): la FK
    `routines.created_by -> users.id` no garantiza el rol -- esta
    verificacion es responsabilidad explicita de `CreateRoutineUseCase`.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(
            f"El usuario {user_id} no tiene permiso para crear rutinas "
            "(debe ser entrenador o admin)"
        )


class RoutineNotFoundError(Exception):
    """No existe una `Routine` con el id solicitado."""

    def __init__(self, routine_id: int) -> None:
        self.routine_id = routine_id
        super().__init__(f"La rutina {routine_id} no existe")


class ExerciseNotFoundError(Exception):
    """No existe un `Exercise` con el id solicitado."""

    def __init__(self, exercise_id: int) -> None:
        self.exercise_id = exercise_id
        super().__init__(f"El ejercicio {exercise_id} no existe")


class InvalidAssignmentStatusError(Exception):
    """`status` no esta en `ESTADOS_ASIGNACION_VALIDOS`."""

    def __init__(self, status_value: str) -> None:
        self.status_value = status_value
        super().__init__(f"El estado '{status_value}' no es un estado de asignacion valido")


class RoutineAssignmentNotFoundError(Exception):
    """No existe una `RoutineAssignment` con el id solicitado."""

    def __init__(self, assignment_id: int) -> None:
        self.assignment_id = assignment_id
        super().__init__(f"La asignacion de rutina {assignment_id} no existe")


class UnauthorizedRoutineAssignmentError(Exception):
    """El entrenador que asigna/actualiza no es el dueno del cliente.

    Mismo patron de ownership por dato ya usado en `AssignMembershipUseCase`/
    `clients.py`: un entrenador solo puede asignar/actualizar rutinas de
    SUS clientes asignados (RF012).
    """

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(f"El cliente {client_id} no esta asignado a este entrenador")


class UnauthorizedRoutineEditError(Exception):
    """Un `entrenador` intento editar/eliminar una rutina que NO creo el.

    Ampliacion de RF012 (2026-11-18, "editar/eliminar rutina"): `admin`
    puede editar/eliminar cualquier rutina del catalogo; `entrenador` solo
    las que el mismo creo (`Routine.created_by`).
    """

    def __init__(self, routine_id: int) -> None:
        self.routine_id = routine_id
        super().__init__(f"La rutina {routine_id} no fue creada por este entrenador")
