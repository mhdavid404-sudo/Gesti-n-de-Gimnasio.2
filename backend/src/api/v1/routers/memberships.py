"""Router FastAPI del modulo Memberships (RF004, RF006).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.memberships import (
    MembershipCreate,
    MembershipPlanCreate,
    MembershipPlanRead,
    MembershipRead,
    MembershipUpdate,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])
plans_router = APIRouter(prefix="/membership-plans", tags=["memberships"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@plans_router.post("", response_model=MembershipPlanRead, status_code=status.HTTP_201_CREATED)
def create_membership_plan(payload: MembershipPlanCreate) -> MembershipPlanRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@plans_router.get("", response_model=list[MembershipPlanRead])
def list_membership_plans() -> list[MembershipPlanRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.post("", response_model=MembershipRead, status_code=status.HTTP_201_CREATED)
def assign_membership(payload: MembershipCreate) -> MembershipRead:
    """RF004: asignar un plan de membresia a un cliente."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("", response_model=list[MembershipRead])
def list_memberships(client_id: int | None = None) -> list[MembershipRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


# IMPORTANTE: esta ruta estatica debe declararse ANTES que
# "/{membership_id}" -- FastAPI/Starlette resuelve las rutas en el orden en
# que se registran, y "/expiring" calzaria con el patron "/{membership_id}"
# (fallando la validacion de tipo `int`) si quedara despues.
@router.get("/expiring", response_model=list[MembershipRead])
def list_expiring_memberships(days_ahead: int = 7) -> list[MembershipRead]:
    """RF006: detectar membresias vencidas o proximas a vencer."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{membership_id}", response_model=MembershipRead)
def get_membership(membership_id: int) -> MembershipRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.patch("/{membership_id}", response_model=MembershipRead)
def update_membership_status(membership_id: int, payload: MembershipUpdate) -> MembershipRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
