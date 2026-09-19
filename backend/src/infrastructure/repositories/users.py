"""Implementacion concreta (SQLAlchemy) del puerto `UserRepository`.

Esta es la UNICA capa donde se traduce `User` (dominio) <-> `UserModel`
(SQLAlchemy) -- DECISIONES.md, correccion #2. La `Session` vive aqui, nunca
en la interfaz de dominio (correccion #3).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.users.entities import User
from src.domain.users.repositories import UserRepository
from src.infrastructure.db.models.users import UserModel


def _to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        full_name=model.full_name,
        role=model.role,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _apply_to_model(entity: User, model: UserModel) -> None:
    model.email = entity.email
    model.password_hash = entity.password_hash
    model.full_name = entity.full_name
    model.role = entity.role
    model.is_active = entity.is_active


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        model = self._session.get(UserModel, user_id)
        return _to_entity(model) if model else None

    def get_by_email(self, email: str) -> User | None:
        model = self._session.execute(
            select(UserModel).where(UserModel.email == email)
        ).scalar_one_or_none()
        return _to_entity(model) if model else None

    def list_by_role(self, role: str) -> list[User]:
        models = self._session.execute(
            select(UserModel).where(UserModel.role == role)
        ).scalars()
        return [_to_entity(m) for m in models]

    def add(self, user: User) -> User:
        model = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, user: User) -> User:
        model = self._session.get(UserModel, user.id)
        if model is None:
            raise ValueError(f"User {user.id} no existe")
        _apply_to_model(user, model)
        self._session.flush()
        return _to_entity(model)

    def delete(self, user_id: int) -> None:
        model = self._session.get(UserModel, user_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()
