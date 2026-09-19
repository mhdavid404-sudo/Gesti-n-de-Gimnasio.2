"""Implementacion concreta (SQLAlchemy) del puerto `BodyProgressRepository`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.progress.entities import BodyProgress
from src.domain.progress.repositories import BodyProgressRepository
from src.infrastructure.db.models.progress import BodyProgressModel


def _to_entity(model: BodyProgressModel) -> BodyProgress:
    return BodyProgress(
        id=model.id,
        client_id=model.client_id,
        record_date=model.record_date,
        weight_kg=model.weight_kg,
        height_cm=model.height_cm,
        body_fat_pct=model.body_fat_pct,
        muscle_mass_kg=model.muscle_mass_kg,
        chest_cm=model.chest_cm,
        waist_cm=model.waist_cm,
        hip_cm=model.hip_cm,
        arm_cm=model.arm_cm,
        notes=model.notes,
    )


class SqlAlchemyBodyProgressRepository(BodyProgressRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, record_id: int) -> BodyProgress | None:
        model = self._session.get(BodyProgressModel, record_id)
        return _to_entity(model) if model else None

    def list_by_client(self, client_id: int) -> list[BodyProgress]:
        models = self._session.execute(
            select(BodyProgressModel)
            .where(BodyProgressModel.client_id == client_id)
            .order_by(BodyProgressModel.record_date)
        ).scalars()
        return [_to_entity(m) for m in models]

    def add(self, record: BodyProgress) -> BodyProgress:
        model = BodyProgressModel(
            client_id=record.client_id,
            record_date=record.record_date,
            weight_kg=record.weight_kg,
            height_cm=record.height_cm,
            body_fat_pct=record.body_fat_pct,
            muscle_mass_kg=record.muscle_mass_kg,
            chest_cm=record.chest_cm,
            waist_cm=record.waist_cm,
            hip_cm=record.hip_cm,
            arm_cm=record.arm_cm,
            notes=record.notes,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, record: BodyProgress) -> BodyProgress:
        model = self._session.get(BodyProgressModel, record.id)
        if model is None:
            raise ValueError(f"BodyProgress {record.id} no existe")
        model.record_date = record.record_date
        model.weight_kg = record.weight_kg
        model.height_cm = record.height_cm
        model.body_fat_pct = record.body_fat_pct
        model.muscle_mass_kg = record.muscle_mass_kg
        model.chest_cm = record.chest_cm
        model.waist_cm = record.waist_cm
        model.hip_cm = record.hip_cm
        model.arm_cm = record.arm_cm
        model.notes = record.notes
        self._session.flush()
        return _to_entity(model)

    def delete(self, record_id: int) -> None:
        model = self._session.get(BodyProgressModel, record_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
