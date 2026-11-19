"""Schemas Pydantic (request/response) del modulo Diets."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssignmentStatus = Literal["activa", "completada", "cancelada"]


class DietPlanCreate(BaseModel):
    """Defecto de seguridad corregido (DECISIONES.md, mismo criterio que
    `PaymentCreate.registered_by`/`RoutineCreate.created_by`): `created_by`
    NO viene del body -- el router lo rellena siempre con
    `current_user.id`. Dejar que el cliente HTTP decida quien "creo" el
    plan permitiria falsificar la autoria.
    """

    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    calories_target: int | None = Field(default=None, gt=0)


class DietPlanUpdate(BaseModel):
    """2026-11-18 (ampliacion de RF012, "editar dieta"): `None` en
    cualquiera de los campos significa "no cambiarlo" (mismo criterio que
    `DietAssignmentUpdate`/`RoutineUpdate`)."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    calories_target: int | None = Field(default=None, gt=0)


class DietPlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: int
    description: str | None
    calories_target: int | None
    created_at: datetime
    is_active: bool


class DietPlanDeleteResult(BaseModel):
    """2026-11-18 (ampliacion de RF012, "eliminar dieta"): mismo patron
    que `RoutineDeleteResult`."""

    deleted: bool
    diet_plan: DietPlanRead | None
    message: str


class DietAssignmentCreate(BaseModel):
    """Defecto de seguridad corregido (DECISIONES.md, mismo criterio que
    `RoutineAssignmentCreate.assigned_by`): `assigned_by` NO viene del
    body -- el router lo rellena siempre con `current_user.id`.
    """

    diet_plan_id: int
    client_id: int
    assigned_date: date
    status: AssignmentStatus = "activa"
    notes: str | None = None


class DietAssignmentUpdate(BaseModel):
    """RF012 (nuevo, ver DECISIONES.md): el entrenador/admin puede cambiar
    `status`/`notes` de una asignacion existente. Todos opcionales -- solo
    se actualiza lo que venga distinto de `None`.

    2026-11-18 (ampliacion de RF012, "corregir una asignacion, error de
    dedo"): se agregan `diet_plan_id`/`assigned_date`, antes solo se podia
    cambiar `status`/`notes`."""

    diet_plan_id: int | None = None
    assigned_date: date | None = None
    status: AssignmentStatus | None = None
    notes: str | None = None


class DietAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    diet_plan_id: int
    client_id: int
    assigned_by: int
    assigned_date: date
    status: AssignmentStatus
    notes: str | None
