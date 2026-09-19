"""Casos de uso del modulo Notifications. Entrega 1: solo el esqueleto."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.notifications.entities import AuditLog, Notification
from src.domain.notifications.repositories import (
    AuditLogRepository,
    NotificationRepository,
)


@dataclass
class NotifyUserUseCase:
    """RF006: crear una notificacion para un usuario."""

    notification_repository: NotificationRepository

    def execute(self, notification: Notification) -> Notification:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class ListUserNotificationsUseCase:
    """RF006: listar notificaciones de un usuario."""

    notification_repository: NotificationRepository

    def execute(self, user_id: int) -> list[Notification]:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class RecordAuditEventUseCase:
    """RF015: registrar un evento/error relevante en la bitacora."""

    audit_log_repository: AuditLogRepository

    def execute(self, entry: AuditLog) -> AuditLog:
        raise NotImplementedError("Entrega 2: logica pendiente")
