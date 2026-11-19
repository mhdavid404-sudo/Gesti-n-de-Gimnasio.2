"""Excepciones de dominio del modulo Diets (RF009, RF012, RF013).

Mismo patron que `domain/routines/exceptions.py`: el dominio no conoce
HTTP ni FastAPI. Estos casos de uso (`application/diets/use_cases.py`)
lanzan estas excepciones; la traduccion a `HTTPException`/codigo de
estado ocurre unicamente en `api/v1/routers/diets.py`.

La falta de existencia del CLIENTE (`client_id`) se senaliza reusando
`domain.clients.exceptions.ClientNotFoundError` -- mismo criterio ya
aplicado por `application/routines/use_cases.py` (no se duplica un
segundo tipo de excepcion para el mismo caso real).
"""

from __future__ import annotations


class UnauthorizedDietPlanCreatorError(Exception):
    """`created_by` no es un `User` con role "entrenador" o "admin".

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4): la FK
    `diet_plans.created_by -> users.id` no garantiza el rol -- esta
    verificacion es responsabilidad explicita de `CreateDietPlanUseCase`.
    """

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(
            f"El usuario {user_id} no tiene permiso para crear planes de dieta "
            "(debe ser entrenador o admin)"
        )


class DietPlanNotFoundError(Exception):
    """No existe un `DietPlan` con el id solicitado."""

    def __init__(self, diet_plan_id: int) -> None:
        self.diet_plan_id = diet_plan_id
        super().__init__(f"El plan de dieta {diet_plan_id} no existe")


class InvalidDietAssignmentStatusError(Exception):
    """`status` no esta en `ESTADOS_ASIGNACION_VALIDOS`."""

    def __init__(self, status_value: str) -> None:
        self.status_value = status_value
        super().__init__(f"El estado '{status_value}' no es un estado de asignacion valido")


class DietAssignmentNotFoundError(Exception):
    """No existe una `DietAssignment` con el id solicitado."""

    def __init__(self, assignment_id: int) -> None:
        self.assignment_id = assignment_id
        super().__init__(f"La asignacion de dieta {assignment_id} no existe")


class UnauthorizedDietAssignmentError(Exception):
    """El entrenador que asigna/actualiza no es el dueno del cliente.

    Mismo patron de ownership por dato ya usado en
    `AssignRoutineToClientUseCase`/`UpdateRoutineAssignmentUseCase`: un
    entrenador solo puede asignar/actualizar dietas de SUS clientes
    asignados (RF012).
    """

    def __init__(self, client_id: int) -> None:
        self.client_id = client_id
        super().__init__(f"El cliente {client_id} no esta asignado a este entrenador")


class UnauthorizedDietEditError(Exception):
    """Un `entrenador` intento editar/eliminar un plan de dieta que NO creo el.

    Ampliacion de RF012 (2026-11-18, "editar/eliminar dieta"): mismo
    criterio que `UnauthorizedRoutineEditError` -- `admin` puede
    editar/eliminar cualquier plan; `entrenador` solo los que el mismo
    creo (`DietPlan.created_by`).
    """

    def __init__(self, diet_plan_id: int) -> None:
        self.diet_plan_id = diet_plan_id
        super().__init__(f"El plan de dieta {diet_plan_id} no fue creado por este entrenador")
