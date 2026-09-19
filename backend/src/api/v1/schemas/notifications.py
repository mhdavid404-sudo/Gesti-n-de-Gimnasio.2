"""Schemas Pydantic (request/response) del modulo Notifications."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NotificationType = Literal[
    "membresia_vencida",
    "membresia_por_vencer",
    "pago_registrado",
    "rutina_asignada",
    "dieta_asignada",
    "sistema",
]


class NotificationCreate(BaseModel):
    user_id: int
    type: NotificationType
    title: str = Field(min_length=1, max_length=150)
    message: str = Field(min_length=1)


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: NotificationType
    title: str
    message: str
    is_read: bool
    created_at: datetime


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: str | None
    created_at: datetime
