"""Router FastAPI del modulo Payments (RF005).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.payments import PaymentCreate, PaymentRead

router = APIRouter(prefix="/payments", tags=["payments"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.post("", response_model=PaymentRead, status_code=status.HTTP_201_CREATED)
def register_payment(payload: PaymentCreate) -> PaymentRead:
    """RF005: registrar un pago asociado a la membresia de un cliente."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int) -> PaymentRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.get("", response_model=list[PaymentRead])
def list_payments(membership_id: int | None = None) -> list[PaymentRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
