"""Router FastAPI del modulo Diets (RF009, RF012, RF013).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.diets import (
    DietAssignmentCreate,
    DietAssignmentRead,
    DietPlanCreate,
    DietPlanRead,
)

router = APIRouter(prefix="/diets", tags=["diets"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.post("/plans", response_model=DietPlanRead, status_code=status.HTTP_201_CREATED)
def create_diet_plan(payload: DietPlanCreate) -> DietPlanRead:
    """RF009: crear un plan de dieta.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4): en Entrega 2 debe
    delegar en `CreateDietPlanUseCase`, que valida que `created_by` sea
    entrenador o admin -- la FK no lo garantiza.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/plans", response_model=list[DietPlanRead])
def list_diet_plans() -> list[DietPlanRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.post(
    "/assignments", response_model=DietAssignmentRead, status_code=status.HTTP_201_CREATED
)
def assign_diet_to_client(payload: DietAssignmentCreate) -> DietAssignmentRead:
    """RF009: asignar un plan de dieta a un cliente."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/assignments/clients/{client_id}", response_model=list[DietAssignmentRead])
def get_client_diet_history(client_id: int) -> list[DietAssignmentRead]:
    """RF012/RF013: dietas asignadas a un cliente, segun el rol de quien consulta."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
