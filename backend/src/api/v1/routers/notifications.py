"""Router FastAPI del modulo Notifications (RF006, RF015).

Este archivo agrupa dos modulos distintos por decision de organizacion ya
documentada en DECISIONES.md (`domain/notifications/entities.py`:
`Notification` y `AuditLog` son ambas "eventos del sistema dirigidos a
alguien que los consulta"):

- `router` (RF006, modulo "Vencimientos/Notificaciones"): implementado en
  esta entrega -- `GET /notifications/users/{user_id}`,
  `POST /notifications/{notification_id}/read`.
- `audit_router` (RF015, modulo "Bitacora (AuditLog)"): FUERA DE ALCANCE de
  este encargo -- el modulo Bitacora es el ULTIMO en el orden fijo de
  modulos de Entrega 2 (ver DECISIONES.md), despues de Progreso. Se deja
  intencionalmente en 501, no es un olvido.

Autorizacion de cada endpoint de `router`:

- `GET /notifications/users/{user_id}`: el propio usuario puede ver sus
  notificaciones (`user_id == current_user.id`); `admin` puede ver las de
  cualquier usuario (util para soporte); cualquier otro caso -> 403.
- `POST /notifications/{notification_id}/read`: solo el dueno de la
  notificacion (`Notification.user_id == current_user.id`) o `admin`
  puede marcarla como leida -- 403 si no corresponde, 404 si no existe.

Sin caso de uso dedicado para "marcar como leida" a proposito: no hay
ninguna invariante de negocio propia (es un toggle simple de
`is_read`), mismo criterio ya aplicado al CRUD de `MembershipPlan` en
`routers/memberships.py` -- usar el repositorio directo desde el router
evita una capa de indireccion vacia.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user
from src.api.v1.schemas.notifications import AuditLogRead, NotificationRead
from src.application.notifications.use_cases import ListUserNotificationsUseCase
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.notifications import SqlAlchemyNotificationRepository

router = APIRouter(prefix="/notifications", tags=["notifications"])
audit_router = APIRouter(prefix="/audit-logs", tags=["notifications"])

_NOT_IMPLEMENTED = "Pendiente de implementacion completa en Entrega 2 (ver DECISIONES.md)."
_NOTIFICACION_NO_ENCONTRADA = "La notificacion solicitada no existe."
_SIN_ACCESO_A_NOTIFICACIONES = "No tienes acceso a las notificaciones de este usuario."
_SIN_ACCESO_A_NOTIFICACION = "No tienes acceso a esta notificacion."


@router.get("/users/{user_id}", response_model=list[NotificationRead])
def list_user_notifications(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[NotificationRead]:
    """RF006: notificaciones de un usuario (ej. membresias por vencer/vencidas).

    El propio usuario puede ver las suyas; `admin` puede ver las de
    cualquiera (soporte); cualquier otro caso -> 403.
    """
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_NOTIFICACIONES)

    notification_repository = SqlAlchemyNotificationRepository(db)
    use_case = ListUserNotificationsUseCase(notification_repository=notification_repository)
    notifications = use_case.execute(user_id)
    return [NotificationRead.model_validate(n) for n in notifications]


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationRead:
    """Solo el dueno de la notificacion o `admin` puede marcarla como leida."""
    notification_repository = SqlAlchemyNotificationRepository(db)

    existing = notification_repository.get_by_id(notification_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOTIFICACION_NO_ENCONTRADA)

    if current_user.role != "admin" and existing.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_NOTIFICACION)

    updated = notification_repository.mark_as_read(notification_id)
    db.commit()
    return NotificationRead.model_validate(updated)


@audit_router.get("", response_model=list[AuditLogRead])
def list_audit_logs(limit: int = 100) -> list[AuditLogRead]:
    """RF015: bitacora de eventos/errores relevantes del sistema.

    FUERA DE ALCANCE de este encargo (modulo Vencimientos/Notificaciones)
    -- pertenece al modulo "Bitacora (AuditLog)", el ultimo en el orden
    fijo de modulos de Entrega 2 (ver DECISIONES.md). Se deja
    intencionalmente en 501.
    """
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=_NOT_IMPLEMENTED)
