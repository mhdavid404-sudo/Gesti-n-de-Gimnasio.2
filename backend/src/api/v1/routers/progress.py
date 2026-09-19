"""Router FastAPI del modulo Progress (RF010, RF011).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.progress import BodyProgressCreate, BodyProgressRead

router = APIRouter(prefix="/progress", tags=["progress"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.post("", response_model=BodyProgressRead, status_code=status.HTTP_201_CREATED)
def register_body_progress(payload: BodyProgressCreate) -> BodyProgressRead:
    """RF010: registrar progreso corporal (peso, medidas, fecha)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/clients/{client_id}", response_model=list[BodyProgressRead])
def get_client_progress_timeline(client_id: int) -> list[BodyProgressRead]:
    """RF011: evolucion del progreso corporal en el tiempo (para el dashboard)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
