"""Entidades de dominio del modulo Routines.

Dataclasses planas, sin imports de SQLAlchemy/FastAPI (DECISIONES.md,
correccion #2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

# Persistido como VARCHAR + CHECK (DECISIONES.md, correccion #1).
ESTADOS_ASIGNACION_VALIDOS = ("activa", "completada", "cancelada")


@dataclass
class Exercise:
    """Ejercicio de catalogo, reutilizable entre rutinas (RF007, RF008)."""

    id: int | None
    name: str
    muscle_group: str | None = None
    description: str | None = None
    created_at: datetime | None = None


@dataclass
class Routine:
    """Rutina de ejercicio (RF007).

    `created_by` apunta a un `User`.

    IMPORTANTE (DECISIONES.md, correccion #4): la base de datos NO garantiza
    que `created_by` sea un `User` con role="entrenador" o role="admin" --
    es una FK simple hacia `users.id`. Esa invariante de negocio es
    responsabilidad explicita de `application/routines` -- ver comentario en
    `application/routines/use_cases.py`.
    """

    id: int | None
    name: str
    created_by: int
    description: str | None = None
    created_at: datetime | None = None


@dataclass
class RoutineExercise:
    """Fila puente Routine <-> Exercise, con el detalle de series/repeticiones.

    Sin esta tabla, RF008 (historial estructurado de rutinas) queda roto
    (DECISIONES.md).
    """

    id: int | None
    routine_id: int
    exercise_id: int
    sets: int
    reps: int
    order_index: int
    rest_seconds: int | None = None
    notes: str | None = None


@dataclass
class RoutineAssignment:
    """Asignacion de una rutina a un cliente concreto (RF007, RF008, RF012)."""

    id: int | None
    routine_id: int
    client_id: int
    assigned_by: int  # User.id
    assigned_date: date
    status: str  # uno de ESTADOS_ASIGNACION_VALIDOS
