"""Puertos (interfaces) del repositorio de Notifications.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.notifications.entities import AuditLog, Notification


class NotificationRepository(ABC):
    @abstractmethod
    def get_by_id(self, notification_id: int) -> Notification | None: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Notification]: ...

    @abstractmethod
    def add(self, notification: Notification) -> Notification: ...

    @abstractmethod
    def mark_as_read(self, notification_id: int) -> Notification: ...

    @abstractmethod
    def delete(self, notification_id: int) -> None: ...


class AuditLogRepository(ABC):
    @abstractmethod
    def add(self, entry: AuditLog) -> AuditLog: ...

    @abstractmethod
    def list_recent(self, limit: int = 100) -> list[AuditLog]: ...

    @abstractmethod
    def list_by_user(self, user_id: int) -> list[AuditLog]: ...
