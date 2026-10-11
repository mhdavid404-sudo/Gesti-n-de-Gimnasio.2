"""Router FastAPI del modulo Clients (RF003, bases de RF012/RF013).

Autorizacion por endpoint (DECISIONES.md, entrada "Modulo Clientes (RF003)"
de Entrega 2):

- `POST /clients` (alta): solo `admin` -- el personal de recepcion da de
  alta clientes, no el propio cliente ni el entrenador.
- `GET /clients` (listado): `admin` ve todos; `entrenador` ve SOLO los que
  tiene asignados (se fuerza `trainer_id == current_user.id`, un
  `trainer_id` de query distinto al propio se IGNORA -- no se usa para ver
  la cartera de otro entrenador); `cliente` no tiene acceso (403, el rol no
  esta en `require_role`).
- `GET /clients/me`: endpoint de conveniencia SOLO para `cliente`, agregado
  a proposito -- el rol cliente no tiene por que conocer su propio
  `client_id` para consultar su perfil (RF013). Debe declararse ANTES de
  `GET /clients/{client_id}` en este archivo: FastAPI/Starlette resuelve
  rutas en orden de declaracion, y `{client_id}` (sin convertidor de tipo
  explicito) matchea el string "me" antes de que FastAPI intente convertirlo
  a `int` -- si esta ruta se declarara despues, `/clients/me` devolveria 422
  en vez de el perfil propio.
- `GET /clients/{client_id}`: `admin` cualquiera; `entrenador` solo si
  `trainer_id == current_user.id` (403 si no); `cliente` solo si es su
  propio perfil (403 si no). Los 3 roles pueden llegar a esta ruta (no hay
  rol bloqueado de entrada) -- el filtro real es POR DATO, no por rol.
- `PATCH /clients/{client_id}`: RF012 le da al entrenador acceso a
  actualizar RUTINAS/DIETAS de sus clientes asignados (modulos separados),
  NO el perfil del cliente -- por eso el PATCH de perfil completo (incluida
  la reasignacion de `trainer_id`, que usa `AssignTrainerToClientUseCase`)
  queda reservado a `admin`.
- `DELETE /clients/{client_id}`: solo `admin`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.clients import (
    ClientProfileCreate,
    ClientProfileRead,
    ClientProfileUpdate,
    ClientRegisterResponse,
)
from src.application.clients.use_cases import (
    AssignTrainerToClientUseCase,
    DeleteClientUseCase,
    RegisterClientUseCase,
    UpdateClientProfileUseCase,
)
from src.domain.clients.entities import ClientProfile
from src.domain.clients.exceptions import ClientNotFoundError, InvalidTrainerAssignmentError
from src.domain.users.entities import User
from src.domain.users.exceptions import EmailAlreadyExistsError
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

router = APIRouter(prefix="/clients", tags=["clients"])

_CLIENTE_NO_ENCONTRADO = "El cliente solicitado no existe."
_SIN_ACCESO_A_CLIENTE = "No tienes acceso a este cliente."


def _enrich(
    user_repository: SqlAlchemyUserRepository, profile: ClientProfile
) -> ClientProfileRead:
    """Completa `email`/`full_name`/`trainer_name` a partir de `User` (ver
    docstring de `ClientProfileRead`)."""
    owner = user_repository.get_by_id(profile.user_id)
    trainer = user_repository.get_by_id(profile.trainer_id) if profile.trainer_id else None
    return ClientProfileRead(
        id=profile.id,  # type: ignore[arg-type]
        user_id=profile.user_id,
        trainer_id=profile.trainer_id,
        phone=profile.phone,
        birth_date=profile.birth_date,
        address=profile.address,
        emergency_contact=profile.emergency_contact,
        created_at=profile.created_at,  # type: ignore[arg-type]
        updated_at=profile.updated_at,  # type: ignore[arg-type]
        email=owner.email if owner else "",
        full_name=owner.full_name if owner else "",
        trainer_name=trainer.full_name if trainer else None,
    )


@router.post(
    "",
    response_model=ClientRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def register_client(payload: ClientProfileCreate, db: Session = Depends(get_db)) -> ClientRegisterResponse:
    """RF003: registrar un cliente (crea `User` + `ClientProfile`). Solo `admin`."""
    client_repository = SqlAlchemyClientProfileRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    use_case = RegisterClientUseCase(client_repository=client_repository, user_repository=user_repository)

    try:
        result = use_case.execute(
            email=payload.email,
            full_name=payload.full_name,
            trainer_id=payload.trainer_id,
            phone=payload.phone,
            birth_date=payload.birth_date,
            address=payload.address,
            emergency_contact=payload.emergency_contact,
        )
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario registrado con el email '{exc.email}'.",
        ) from exc
    except InvalidTrainerAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return ClientRegisterResponse(
        client=_enrich(user_repository, result.client_profile),
        temporary_password=result.temporary_password,
    )


@router.get("/me", response_model=ClientProfileRead, dependencies=[Depends(require_role("cliente"))])
def get_my_client_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientProfileRead:
    """RF013: conveniencia para que el rol `cliente` consulte su propio
    perfil sin necesitar conocer su `client_id` (ver docstring del modulo).
    """
    client_repository = SqlAlchemyClientProfileRepository(db)
    user_repository = SqlAlchemyUserRepository(db)

    profile = client_repository.get_by_user_id(current_user.id)  # type: ignore[arg-type]
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO)

    return _enrich(user_repository, profile)


@router.get("/{client_id}", response_model=ClientProfileRead)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClientProfileRead:
    """Los 3 roles pueden llegar aqui -- el filtro es por dato, no por rol
    (ver docstring del modulo): `admin` sin restriccion, `entrenador` solo
    si es su cliente asignado, `cliente` solo su propio perfil.
    """
    client_repository = SqlAlchemyClientProfileRepository(db)
    user_repository = SqlAlchemyUserRepository(db)

    profile = client_repository.get_by_id(client_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO)

    if current_user.role == "entrenador" and profile.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_CLIENTE)
    if current_user.role == "cliente" and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_CLIENTE)

    return _enrich(user_repository, profile)


@router.get(
    "",
    response_model=list[ClientProfileRead],
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def list_clients(
    trainer_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ClientProfileRead]:
    """`cliente` no tiene acceso (403, bloqueado por `require_role`).
    `entrenador` ve SOLO sus clientes asignados -- cualquier `trainer_id` de
    query se ignora y se fuerza al propio id (ver docstring del modulo).
    `admin` ve todos, opcionalmente filtrado por el `trainer_id` de query.
    """
    client_repository = SqlAlchemyClientProfileRepository(db)
    user_repository = SqlAlchemyUserRepository(db)

    if current_user.role == "entrenador":
        profiles = client_repository.list_by_trainer(current_user.id)  # type: ignore[arg-type]
    elif trainer_id is not None:
        profiles = client_repository.list_by_trainer(trainer_id)
    else:
        profiles = client_repository.list_all()

    return [_enrich(user_repository, profile) for profile in profiles]


@router.patch(
    "/{client_id}",
    response_model=ClientProfileRead,
    dependencies=[Depends(require_role("admin"))],
)
def update_client(client_id: int, payload: ClientProfileUpdate, db: Session = Depends(get_db)) -> ClientProfileRead:
    """Incluye reasignar `trainer_id` -- delega en `AssignTrainerToClientUseCase`
    (ver docstring del modulo: solo `admin`, RF012 es de Rutinas/Dietas, no
    de este perfil).
    """
    client_repository = SqlAlchemyClientProfileRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    use_case = UpdateClientProfileUseCase(client_repository=client_repository, user_repository=user_repository)

    updates = ClientProfile(
        id=None,
        user_id=0,
        trainer_id=payload.trainer_id,
        phone=payload.phone,
        birth_date=payload.birth_date,
        address=payload.address,
        emergency_contact=payload.emergency_contact,
    )

    try:
        updated = use_case.execute(client_id, updates)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO) from exc
    except InvalidTrainerAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return _enrich(user_repository, updated)


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin"))],
)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = DeleteClientUseCase(client_repository=client_repository)

    try:
        use_case.execute(client_id)
    except ClientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO) from exc

    db.commit()
