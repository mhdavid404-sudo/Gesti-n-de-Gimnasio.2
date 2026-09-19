"""Schemas Pydantic (request/response) del modulo Diets."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssignmentStatus = Literal["activa", "completada", "cancelada"]


class DietPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    created_by: int
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


class DietAssignmentCreate(BaseModel):
    diet_plan_id: int
    client_id: int
    assigned_by: int
    assigned_date: date
    status: AssignmentStatus = "activa"


class DietAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    diet_plan_id: int
    client_id: int
    assigned_by: int
    assigned_date: date
    status: AssignmentStatus
