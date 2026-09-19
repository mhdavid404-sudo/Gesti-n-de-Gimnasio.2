"""Router FastAPI del modulo Users (RF001, RF002).

Entrega 1: solo el esqueleto de la API (rutas, schemas, codigos de
respuesta documentados en OpenAPI). Los cuerpos de los endpoints devuelven
501 porque los casos de uso en `application/users/use_cases.py` son stubs
-- ver DECISIONES.md y COORDINACION-ENTREGA1.md. NO hay login/JWT
funcional en esta entrega.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.users import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate) -> UserRead:
    """RF001: registrar un usuario nuevo con un rol."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int) -> UserRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("", response_model=list[UserRead])
def list_users(role: str | None = None) -> list[UserRead]:
    """RF002: listar usuarios, opcionalmente filtrados por rol."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate) -> UserRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def delete_user(user_id: int) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
