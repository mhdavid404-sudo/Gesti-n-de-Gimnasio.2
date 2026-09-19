"""Schemas Pydantic (request/response) del modulo Routines."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AssignmentStatus = Literal["activa", "completada", "cancelada"]


class ExerciseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    muscle_group: str | None = Field(default=None, max_length=100)
    description: str | None = None


class ExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    muscle_group: str | None
    description: str | None
    created_at: datetime


class RoutineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    created_by: int
    description: str | None = None


class RoutineRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_by: int
    description: str | None
    created_at: datetime


class RoutineExerciseCreate(BaseModel):
    exercise_id: int
    sets: int = Field(gt=0)
    reps: int = Field(gt=0)
    order_index: int = Field(ge=0)
    rest_seconds: int | None = Field(default=None, ge=0)
    notes: str | None = None


class RoutineExerciseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    routine_id: int
    exercise_id: int
    sets: int
    reps: int
    order_index: int
    rest_seconds: int | None
    notes: str | None


class RoutineAssignmentCreate(BaseModel):
    routine_id: int
    client_id: int
    assigned_by: int
    assigned_date: date
    status: AssignmentStatus = "activa"


class RoutineAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    routine_id: int
    client_id: int
    assigned_by: int
    assigned_date: date
    status: AssignmentStatus
