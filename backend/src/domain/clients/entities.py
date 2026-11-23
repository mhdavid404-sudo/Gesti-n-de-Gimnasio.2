"""Entidades de dominio del modulo Clients.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class ClientProfile:
    """Perfil extendido de un cliente (RF003).

    `user_id` apunta al `User` (role="cliente") dueno de este perfil.
    `trainer_id` apunta al `User` (role="entrenador") que lo atiende.

    IMPORTANTE (DECISIONES.md, correccion #4): la base de datos NO garantiza
    que `trainer_id` sea un `User` con role="entrenador" (es una FK simple
    hacia `users.id`, sin CHECK cross-tabla posible en un CHECK constraint
    plano). Esa invariante de negocio es responsabilidad explicita de
    `application/clients` -- ver comentario en
    `application/clients/use_cases.py`.
    """

    id: int | None
    user_id: int
    trainer_id: int | None
    phone: str | None
    birth_date: date | None
    address: str | None
    # Reversion del arbitraje de 2026-09-12 (DECISIONES.md, entrada
    # "Separacion de contacto de emergencia en nombre/telefono"): vuelve a
    # dividirse en dos campos -- el cliente real pidio poder filtrar/llamar
    # por telefono sin tener que parsear texto libre.
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
