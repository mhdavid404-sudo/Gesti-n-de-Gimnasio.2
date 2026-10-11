"""Excepciones de dominio del modulo Notifications (RF006).

Mismo patron que `domain/memberships/exceptions.py` y
`domain/payments/exceptions.py`: el dominio no conoce HTTP ni FastAPI. La
traduccion a `HTTPException`/codigo de estado ocurre unicamente en
`api/v1/routers/notifications.py`.
"""

from __future__ import annotations


class InvalidNotificationTypeError(Exception):
    """`type` no esta en `TIPOS_NOTIFICACION_VALIDOS`."""

    def __init__(self, type_value: str) -> None:
        self.type_value = type_value
        super().__init__(f"El tipo de notificacion '{type_value}' no es valido")


class NotificationNotFoundError(Exception):
    """No existe una `Notification` con el id solicitado."""

    def __init__(self, notification_id: int) -> None:
        self.notification_id = notification_id
        super().__init__(f"La notificacion {notification_id} no existe")
