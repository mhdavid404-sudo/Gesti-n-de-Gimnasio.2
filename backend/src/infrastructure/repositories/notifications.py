"""Implementacion concreta (SQLAlchemy) de los puertos de Notifications."""

from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.domain.notifications.entities import AuditLog, Notification
from src.domain.notifications.repositories import (
    AuditLogRepository,
    NotificationRepository,
)
from src.infrastructure.db.models.notifications import AuditLogModel, NotificationModel


def _notification_to_entity(model: NotificationModel) -> Notification:
    return Notification(
        id=model.id,
        user_id=model.user_id,
        type=model.type,
        title=model.title,
        message=model.message,
        is_read=model.is_read,
        created_at=model.created_at,
    )


def _audit_log_to_entity(model: AuditLogModel) -> AuditLog:
    return AuditLog(
        id=model.id,
        user_id=model.user_id,
        action=model.action,
        entity_type=model.entity_type,
        entity_id=model.entity_id,
        details=model.details,
        created_at=model.created_at,
    )


class SqlAlchemyNotificationRepository(NotificationRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, notification_id: int) -> Notification | None:
        model = self._session.get(NotificationModel, notification_id)
        return _notification_to_entity(model) if model else None

    def list_by_user(self, user_id: int) -> list[Notification]:
        models = self._session.execute(
            select(NotificationModel)
            .where(NotificationModel.user_id == user_id)
            .order_by(desc(NotificationModel.created_at))
        ).scalars()
        return [_notification_to_entity(m) for m in models]

    def add(self, notification: Notification) -> Notification:
        model = NotificationModel(
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            is_read=notification.is_read,
        )
        self._session.add(model)
        self._session.flush()
        return _notification_to_entity(model)

    def mark_as_read(self, notification_id: int) -> Notification:
        model = self._session.get(NotificationModel, notification_id)
        if model is None:
            raise ValueError(f"Notification {notification_id} no existe")
        model.is_read = True
        self._session.flush()
        return _notification_to_entity(model)

    def delete(self, notification_id: int) -> None:
        model = self._session.get(NotificationModel, notification_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


class SqlAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entry: AuditLog) -> AuditLog:
        model = AuditLogModel(
            user_id=entry.user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            details=entry.details,
        )
        self._session.add(model)
        self._session.flush()
        return _audit_log_to_entity(model)

    def list_recent(self, limit: int = 100) -> list[AuditLog]:
        models = self._session.execute(
            select(AuditLogModel).order_by(desc(AuditLogModel.created_at)).limit(limit)
        ).scalars()
        return [_audit_log_to_entity(m) for m in models]

    def list_by_user(self, user_id: int) -> list[AuditLog]:
        models = self._session.execute(
            select(AuditLogModel).where(AuditLogModel.user_id == user_id)
        ).scalars()
        return [_audit_log_to_entity(m) for m in models]
