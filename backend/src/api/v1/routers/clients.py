"""Router FastAPI del modulo Clients (RF003).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.clients import (
    ClientProfileCreate,
    ClientProfileRead,
    ClientProfileUpdate,
)

router = APIRouter(prefix="/clients", tags=["clients"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.post("", response_model=ClientProfileRead, status_code=status.HTTP_201_CREATED)
def register_client(payload: ClientProfileCreate) -> ClientProfileRead:
    """RF003: registrar un cliente (crea/vincula su ClientProfile)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{client_id}", response_model=ClientProfileRead)
def get_client(client_id: int) -> ClientProfileRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("", response_model=list[ClientProfileRead])
def list_clients(trainer_id: int | None = None) -> list[ClientProfileRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.patch("/{client_id}", response_model=ClientProfileRead)
def update_client(client_id: int, payload: ClientProfileUpdate) -> ClientProfileRead:
    """Incluye reasignar `trainer_id`.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4): en Entrega 2 este
    endpoint debe delegar en `AssignTrainerToClientUseCase`, que valida que
    `trainer_id` sea un `User` con `role == "entrenador"` -- la FK no lo
    garantiza.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_client(client_id: int) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
