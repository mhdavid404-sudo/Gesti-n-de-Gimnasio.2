"""Schemas Pydantic (request/response) del modulo Progress."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BodyProgressCreate(BaseModel):
    client_id: int
    record_date: date
    weight_kg: Decimal = Field(gt=0)
    height_cm: Decimal | None = Field(default=None, gt=0)
    body_fat_pct: Decimal | None = Field(default=None, ge=0, le=100)
    muscle_mass_kg: Decimal | None = Field(default=None, gt=0)
    chest_cm: Decimal | None = Field(default=None, gt=0)
    waist_cm: Decimal | None = Field(default=None, gt=0)
    hip_cm: Decimal | None = Field(default=None, gt=0)
    arm_cm: Decimal | None = Field(default=None, gt=0)
    notes: str | None = None


class BodyProgressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    record_date: date
    weight_kg: Decimal
    height_cm: Decimal | None
    body_fat_pct: Decimal | None
    muscle_mass_kg: Decimal | None
    chest_cm: Decimal | None
    waist_cm: Decimal | None
    hip_cm: Decimal | None
    arm_cm: Decimal | None
    notes: str | None
