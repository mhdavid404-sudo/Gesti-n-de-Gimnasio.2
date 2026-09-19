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
    # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): campo unico de texto
    # libre, igual que `address` -- no separado en nombre/telefono.
    emergency_contact: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
