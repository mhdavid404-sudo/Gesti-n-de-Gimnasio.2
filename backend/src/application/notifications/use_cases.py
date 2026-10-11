"""Casos de uso del modulo Notifications (RF006, bases de RF015).

Entrega 2: `NotifyUserUseCase`/`ListUserNotificationsUseCase` tienen logica
real (modulo "Vencimientos/Notificaciones", ver DECISIONES.md).
`RecordAuditEventUseCase` (RF015, modulo "Bitacora (AuditLog)") sigue sin
implementar A PROPOSITO -- ese modulo es el ULTIMO en el orden fijo de
modulos de Entrega 2, despues de Progreso. No es un olvido.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.notifications.entities import (
    TIPOS_NOTIFICACION_VALIDOS,
    AuditLog,
    Notification,
)
from src.domain.notifications.exceptions import InvalidNotificationTypeError
from src.domain.notifications.repositories import (
    AuditLogRepository,
    NotificationRepository,
)


@dataclass
class NotifyUserUseCase:
    """RF006: crear una notificacion para un usuario.

    Valida que `type` sea uno de `TIPOS_NOTIFICACION_VALIDOS` -- el schema
    Pydantic (`api/v1/schemas/notifications.py`) ya tipa `type` como
    `Literal` en la capa de transporte, pero el dominio no confia
    ciegamente en esa capa (mismo criterio ya aplicado por
    `AssignMembershipUseCase`/`RegisterPaymentUseCase` sobre sus propios
    enums-por-CHECK).

    Usado directamente por `DetectExpiringMembershipsUseCase` (modulo
    Memberships, RF006) para generar las notificaciones de
    `membresia_vencida`/`membresia_por_vencer` -- no existe todavia un
    endpoint HTTP que llame a este caso de uso de forma directa (no se
    pidio un `POST /notifications` generico en esta entrega).
    """

    notification_repository: NotificationRepository

    def execute(self, notification: Notification) -> Notification:
        if notification.type not in TIPOS_NOTIFICACION_VALIDOS:
            raise InvalidNotificationTypeError(notification.type)
        return self.notification_repository.add(notification)


@dataclass
class ListUserNotificationsUseCase:
    """RF006: listar las notificaciones de un usuario (mas recientes
    primero -- ver `SqlAlchemyNotificationRepository.list_by_user`)."""

    notification_repository: NotificationRepository

    def execute(self, user_id: int) -> list[Notification]:
        return self.notification_repository.list_by_user(user_id)


@dataclass
class RecordAuditEventUseCase:
    """RF015: registrar un evento/error relevante en la bitacora.

    FUERA DE ALCANCE del modulo Vencimientos/Notificaciones. Pertenece al
    modulo "Bitacora (AuditLog)" (ver DECISIONES.md, orden fijo de
    modulos) -- se deja intencionalmente sin implementar, no es un olvido.
    """

    audit_log_repository: AuditLogRepository

    def execute(self, entry: AuditLog) -> AuditLog:
        raise NotImplementedError("Entrega 2: modulo Bitacora (AuditLog), pendiente")
