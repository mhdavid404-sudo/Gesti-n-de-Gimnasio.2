"""Router FastAPI del modulo Notifications (RF006, RF015).

Entrega 1: solo el esqueleto de la API. Ver nota en `routers/users.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.api.v1.schemas.notifications import AuditLogRead, NotificationRead

router = APIRouter(prefix="/notifications", tags=["notifications"])
audit_router = APIRouter(prefix="/audit-logs", tags=["notifications"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."


@router.get("/users/{user_id}", response_model=list[NotificationRead])
def list_user_notifications(user_id: int) -> list[NotificationRead]:
    """RF006: notificaciones de un usuario (ej. membresias por vencer/vencidas)."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_as_read(notification_id: int) -> NotificationRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)


@audit_router.get("", response_model=list[AuditLogRead])
def list_audit_logs(limit: int = 100) -> list[AuditLogRead]:
    """RF015: bitacora de eventos/errores relevantes del sistema."""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
