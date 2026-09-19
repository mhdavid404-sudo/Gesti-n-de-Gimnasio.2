"""Implementacion concreta (SQLAlchemy) del puerto `ClientProfileRepository`.

Traduce `ClientProfile` (dominio) <-> `ClientProfileModel` (SQLAlchemy).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.clients.entities import ClientProfile
from src.domain.clients.repositories import ClientProfileRepository
from src.infrastructure.db.models.clients import ClientProfileModel


def _to_entity(model: ClientProfileModel) -> ClientProfile:
    return ClientProfile(
        id=model.id,
        user_id=model.user_id,
        trainer_id=model.trainer_id,
        phone=model.phone,
        birth_date=model.birth_date,
        address=model.address,
        emergency_contact=model.emergency_contact,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SqlAlchemyClientProfileRepository(ClientProfileRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, client_id: int) -> ClientProfile | None:
        model = self._session.get(ClientProfileModel, client_id)
        return _to_entity(model) if model else None

    def get_by_user_id(self, user_id: int) -> ClientProfile | None:
        model = self._session.execute(
            select(ClientProfileModel).where(ClientProfileModel.user_id == user_id)
        ).scalar_one_or_none()
        return _to_entity(model) if model else None

    def list_by_trainer(self, trainer_id: int) -> list[ClientProfile]:
        models = self._session.execute(
            select(ClientProfileModel).where(
                ClientProfileModel.trainer_id == trainer_id
            )
        ).scalars()
        return [_to_entity(m) for m in models]

    def list_all(self) -> list[ClientProfile]:
        models = self._session.execute(select(ClientProfileModel)).scalars()
        return [_to_entity(m) for m in models]

    def add(self, client: ClientProfile) -> ClientProfile:
        model = ClientProfileModel(
            user_id=client.user_id,
            trainer_id=client.trainer_id,
            phone=client.phone,
            birth_date=client.birth_date,
            address=client.address,
            emergency_contact=client.emergency_contact,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, client: ClientProfile) -> ClientProfile:
        model = self._session.get(ClientProfileModel, client.id)
        if model is None:
            raise ValueError(f"ClientProfile {client.id} no existe")
        model.trainer_id = client.trainer_id
        model.phone = client.phone
        model.birth_date = client.birth_date
        model.address = client.address
        model.emergency_contact = client.emergency_contact
        self._session.flush()
        return _to_entity(model)

    def delete(self, client_id: int) -> None:
        model = self._session.get(ClientProfileModel, client_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
