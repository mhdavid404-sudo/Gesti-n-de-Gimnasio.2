"""Casos de uso del modulo Clients.

Entrega 2: logica real de los 4 casos de uso (RF003), mas las bases de
RF012/RF013 aplicadas sobre este modulo (ver router). Detalle de cada
decision de ambiguedad en DECISIONES.md, entrada "Modulo Clientes (RF003)".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.domain.clients.entities import ClientProfile
from src.domain.clients.exceptions import ClientNotFoundError, InvalidTrainerAssignmentError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.users.entities import User
from src.domain.users.exceptions import EmailAlreadyExistsError
from src.domain.users.repositories import UserRepository
from src.infrastructure.security.password import generate_temporary_password, hash_password


def _ensure_trainer_role(user_repository: UserRepository, trainer_id: int) -> None:
    """Valida la invariante de negocio (DECISIONES.md, correccion #4):
    `trainer_id` debe apuntar a un `User` existente con `role == 'entrenador'`.
    La FK `client_profiles.trainer_id -> users.id` no lo garantiza -- esta
    funcion es la unica responsable de esa verificacion, reusada por
    `RegisterClientUseCase` y `AssignTrainerToClientUseCase` para no
    duplicar la regla.
    """
    trainer = user_repository.get_by_id(trainer_id)
    if trainer is None or trainer.role != "entrenador":
        raise InvalidTrainerAssignmentError(trainer_id)


@dataclass
class RegisterClientResult:
    """Resultado de `RegisterClientUseCase`: perfil creado + password temporal.

    DECISIONES.md: la password temporal se devuelve en texto claro UNA SOLA
    VEZ, en esta respuesta -- nunca se vuelve a mostrar despues (solo el
    hash queda persistido).
    """

    client_profile: ClientProfile
    temporary_password: str


@dataclass
class RegisterClientUseCase:
    """RF003: registrar un cliente -- orquesta la creacion de `User`
    (role='cliente') + `ClientProfile` en una sola operacion.

    DECISIONES.md (modulo Clientes, Entrega 2): el formulario de alta no
    pide password (el frontend actual solo pedia nombre/correo/telefono/
    direccion) -- se genera una temporal aqui, se hashea igual que
    `RegisterUserUseCase`, y se devuelve en claro una sola vez via
    `RegisterClientResult` para que el staff la comparta con el cliente.

    Depende de `ClientProfileRepository` y `UserRepository` a la vez:
    orquestar varios repositorios desde un caso de uso de aplicacion es
    correcto en este patron (ninguno de los dos es infraestructura, ambos
    son puertos de dominio).
    """

    client_repository: ClientProfileRepository
    user_repository: UserRepository

    def execute(
        self,
        *,
        email: str,
        full_name: str,
        trainer_id: int | None,
        phone: str | None,
        birth_date: date | None,
        address: str | None,
        emergency_contact: str | None,
    ) -> RegisterClientResult:
        if self.user_repository.get_by_email(email) is not None:
            raise EmailAlreadyExistsError(email)

        if trainer_id is not None:
            _ensure_trainer_role(self.user_repository, trainer_id)

        temporary_password = generate_temporary_password()

        new_user = self.user_repository.add(
            User(
                id=None,
                email=email,
                password_hash=hash_password(temporary_password),
                full_name=full_name,
                role="cliente",
                is_active=True,
            )
        )

        new_profile = self.client_repository.add(
            ClientProfile(
                id=None,
                user_id=new_user.id,  # type: ignore[arg-type]
                trainer_id=trainer_id,
                phone=phone,
                birth_date=birth_date,
                address=address,
                emergency_contact=emergency_contact,
            )
        )

        return RegisterClientResult(client_profile=new_profile, temporary_password=temporary_password)


@dataclass
class AssignTrainerToClientUseCase:
    """RF003: asignar/reasignar el entrenador de un cliente.

    INVARIANTE DE NEGOCIO (DECISIONES.md, correccion #4) -- responsabilidad
    de esta capa, NO de la base de datos: `trainer_id` debe apuntar a un
    `User` cuyo `role == "entrenador"`.
    """

    client_repository: ClientProfileRepository
    user_repository: UserRepository

    def execute(self, client_id: int, trainer_id: int) -> ClientProfile:
        client = self.client_repository.get_by_id(client_id)
        if client is None:
            raise ClientNotFoundError(client_id)

        _ensure_trainer_role(self.user_repository, trainer_id)

        client.trainer_id = trainer_id
        return self.client_repository.update(client)


@dataclass
class UpdateClientProfileUseCase:
    """RF003: editar datos de perfil de un cliente (incluye reasignar
    `trainer_id`, cuando el payload lo trae).

    Autorizacion (quien puede llamar esto) es responsabilidad del router
    (`api/v1/routers/clients.py`) -- esta clase solo aplica la logica de
    dominio: un campo en `None` dentro de `updates` significa "no cambiar
    ese campo" (mismo criterio que `UserUpdate` en
    `application/users/use_cases.py`), excepto `trainer_id`, cuyo cambio se
    delega integramente en `AssignTrainerToClientUseCase` para no duplicar
    la validacion de rol.
    """

    client_repository: ClientProfileRepository
    user_repository: UserRepository

    def execute(self, client_id: int, updates: ClientProfile) -> ClientProfile:
        existing = self.client_repository.get_by_id(client_id)
        if existing is None:
            raise ClientNotFoundError(client_id)

        if updates.trainer_id is not None and updates.trainer_id != existing.trainer_id:
            assign_use_case = AssignTrainerToClientUseCase(
                client_repository=self.client_repository,
                user_repository=self.user_repository,
            )
            existing = assign_use_case.execute(client_id, updates.trainer_id)

        merged = ClientProfile(
            id=existing.id,
            user_id=existing.user_id,
            trainer_id=existing.trainer_id,
            phone=updates.phone if updates.phone is not None else existing.phone,
            birth_date=updates.birth_date if updates.birth_date is not None else existing.birth_date,
            address=updates.address if updates.address is not None else existing.address,
            emergency_contact=(
                updates.emergency_contact
                if updates.emergency_contact is not None
                else existing.emergency_contact
            ),
        )
        return self.client_repository.update(merged)


@dataclass
class DeleteClientUseCase:
    """RF003: eliminar el perfil de un cliente.

    DECISIONES.md: solo elimina el `ClientProfile` -- la cuenta `User`
    (role='cliente') asociada NO se borra aqui (la FK es `ondelete=CASCADE`
    en el sentido User->ClientProfile, no al reves). Desactivar/eliminar la
    cuenta de acceso es una operacion distinta (`DELETE /users/{id}`, modulo
    Users), fuera del alcance de este caso de uso -- mantiene la
    responsabilidad de esta clase acotada a una sola tabla, igual que en el
    esqueleto original.
    """

    client_repository: ClientProfileRepository

    def execute(self, client_id: int) -> None:
        existing = self.client_repository.get_by_id(client_id)
        if existing is None:
            raise ClientNotFoundError(client_id)
        self.client_repository.delete(client_id)
