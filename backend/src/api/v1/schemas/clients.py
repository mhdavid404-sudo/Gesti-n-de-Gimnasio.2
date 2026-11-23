"""Schemas Pydantic (request/response) del modulo Clients."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ClientProfileCreate(BaseModel):
    """Alta de cliente (RF003): datos de `User` (role='cliente') +
    `ClientProfile` en un solo payload -- ver `RegisterClientUseCase`
    (DECISIONES.md, modulo Clientes). Deliberadamente SIN campo de
    password: el backend genera una temporal y la devuelve una sola vez en
    `ClientRegisterResponse`.
    """

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    trainer_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=30)


class ClientProfileUpdate(BaseModel):
    # full_name/email viven en `User` (dueño del perfil), no en
    # `ClientProfile` -- 2026-11-18, "Editar datos" se amplía para
    # tocar también la cuenta, ver `UpdateClientProfileUseCase`.
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    trainer_id: int | None = None
    phone: str | None = Field(default=None, max_length=30)
    birth_date: date | None = None
    address: str | None = Field(default=None, max_length=255)
    emergency_contact_name: str | None = Field(default=None, max_length=255)
    emergency_contact_phone: str | None = Field(default=None, max_length=30)


class ClientProfileRead(BaseModel):
    """Lectura de un cliente.

    DECISIONES.md (modulo Clientes, Entrega 2): se embeben `email`/
    `full_name` (del `User` duenio del perfil) y `trainer_name` (del
    `User` entrenador, si tiene uno asignado). El router las llena a mano
    (no vienen de `ClientProfileRepository`, que solo conoce la tabla
    `client_profiles`) -- el frontend (`ClientsListPage`) necesita mostrar
    nombre/correo/entrenador en la misma tabla que lista perfiles, y pedir
    2-3 llamadas extra a `GET /users/{id}` por fila para armar eso es peor
    que enriquecer la respuesta aqui, donde el router ya tiene ambos
    repositorios disponibles.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    trainer_id: int | None
    phone: str | None
    birth_date: date | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    created_at: datetime
    updated_at: datetime
    email: str
    full_name: str
    trainer_name: str | None = None


class ClientRegisterResponse(BaseModel):
    """Respuesta de `POST /clients`: el perfil creado + la password temporal.

    `temporary_password` solo se devuelve AQUI, una sola vez -- no existe
    otro endpoint que la vuelva a mostrar despues (ver DECISIONES.md).
    """

    client: ClientProfileRead
    temporary_password: str
