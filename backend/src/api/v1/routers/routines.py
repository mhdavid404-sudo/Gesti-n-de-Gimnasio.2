"""Router FastAPI del modulo Routines (RF007, RF008, RF012, RF013).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.routines import (
    ExerciseCreate,
    ExerciseRead,
    RoutineAssignmentCreate,
    RoutineAssignmentRead,
    RoutineCreate,
    RoutineExerciseCreate,
    RoutineExerciseRead,
    RoutineRead,
)

exercises_router = APIRouter(prefix="/exercises", tags=["routines"])
router = APIRouter(prefix="/routines", tags=["routines"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@exercises_router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise(payload: ExerciseCreate) -> ExerciseRead:
    """Catalogo de ejercicios reutilizable (soporte de RF007/RF008)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@exercises_router.get("", response_model=list[ExerciseRead])
def list_exercises() -> list[ExerciseRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.post("", response_model=RoutineRead, status_code=status.HTTP_201_CREATED)
def create_routine(payload: RoutineCreate) -> RoutineRead:
    """RF007: crear una rutina.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4): en Entrega 2 debe
    delegar en `CreateRoutineUseCase`, que valida que `created_by` sea
    entrenador o admin -- la FK no lo garantiza.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("", response_model=list[RoutineRead])
def list_routines() -> list[RoutineRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


# IMPORTANTE: las rutas estaticas bajo "/assignments" deben declararse
# ANTES que "/{routine_id}" -- FastAPI/Starlette resuelve las rutas en el
# orden de registro, y "assignments" calzaria como valor de `routine_id`
# (fallando la validacion de tipo `int`) si quedara despues.
@router.post(
    "/assignments", response_model=RoutineAssignmentRead, status_code=status.HTTP_201_CREATED
)
def assign_routine_to_client(payload: RoutineAssignmentCreate) -> RoutineAssignmentRead:
    """RF007: asignar una rutina a un cliente."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/assignments/clients/{client_id}", response_model=list[RoutineAssignmentRead])
def get_client_routine_history(client_id: int) -> list[RoutineAssignmentRead]:
    """RF008: historial de rutinas de un cliente.

    Tambien cubre RF013 (cliente ve lo propio) y RF012 (entrenador ve/
    actualiza lo asignado) -- el filtrado por rol de quien consulta es
    responsabilidad de `application/routines` en Entrega 2.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{routine_id}", response_model=RoutineRead)
def get_routine(routine_id: int) -> RoutineRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.post(
    "/{routine_id}/exercises",
    response_model=RoutineExerciseRead,
    status_code=status.HTTP_201_CREATED,
)
def add_exercise_to_routine(routine_id: int, payload: RoutineExerciseCreate) -> RoutineExerciseRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{routine_id}/exercises", response_model=list[RoutineExerciseRead])
def list_routine_exercises(routine_id: int) -> list[RoutineExerciseRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
