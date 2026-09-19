"""Entidades de dominio del modulo Notifications.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).

Nota de organizacion: `DECISIONES.md` lista 8 modulos de referencia (users,
clients, memberships, payments, routines, diets, progress, notifications)
pero el modelo aprobado tiene 14 entidades, no 13 como dice el titulo del
acta (incluye `AuditLog`, que no tiene modulo propio en esa lista). Se
decidio ubicar `AuditLog` dentro de `notifications` porque ambas entidades
son "eventos del sistema dirigidos a alguien que los consulta" -- ver
tambien `backend/MODELO-DATOS.md`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# Persistido como VARCHAR + CHECK (DECISIONES.md, correccion #1).
TIPOS_NOTIFICACION_VALIDOS = (
    "membresia_vencida",
    "membresia_por_vencer",
    "pago_registrado",
    "rutina_asignada",
    "dieta_asignada",
    "sistema",
)


@dataclass
class Notification:
    """Notificacion dirigida a un usuario (RF006)."""

    id: int | None
    user_id: int
    type: str  # uno de TIPOS_NOTIFICACION_VALIDOS
    title: str
    message: str
    is_read: bool = False
    created_at: datetime | None = None


@dataclass
class AuditLog:
    """Entrada de bitacora de eventos/errores del sistema (RF015).

    `user_id` es opcional: un evento de sistema (ej. un job que detecta
    membresias vencidas) puede no estar atado a un usuario que ejecuta la
    accion interactivamente.
    """

    id: int | None
    action: str
    user_id: int | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    details: str | None = None
    created_at: datetime | None = None
