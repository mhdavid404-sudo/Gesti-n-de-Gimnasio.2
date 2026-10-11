"""Router FastAPI del modulo Users (RF001, RF002).

Autorizacion (DECISIONES.md, 2026-10-10, resolucion del backlog B1):
- `POST /users` (alta de usuario): solo `admin`. No existe alta publica de
  cuentas en un sistema de staff de gimnasio -- las cuentas de
  entrenador/cliente las crea el staff administrativo, nunca el propio
  interesado via un formulario abierto.
- `GET /users/{id}` y `GET /users`: `admin` o `entrenador` (un entrenador
  necesita poder consultar informacion basica de otros usuarios, ej. para
  verificar a quien le asigna una rutina). RF012/RF013 (acceso acotado a
  SUS clientes) se aplican en los modulos Clientes/Rutinas/Dietas/
  Progreso, no en este listado general de cuentas.
- `PATCH /users/{id}` y `DELETE /users/{id}`: solo `admin`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import require_role
from src.api.v1.schemas.users import UserCreate, UserRead, UserUpdate
from src.application.users.use_cases import ListUsersByRoleUseCase, RegisterUserUseCase
from src.domain.users.entities import User
from src.domain.users.exceptions import EmailAlreadyExistsError, InvalidRoleError
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

router = APIRouter(prefix="/users", tags=["users"])

_USUARIO_NO_ENCONTRADO = "El usuario solicitado no existe."


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    """RF001: registrar un usuario nuevo con un rol. Solo `admin`."""
    repository = SqlAlchemyUserRepository(db)
    use_case = RegisterUserUseCase(user_repository=repository)

    # `password_hash` se usa aqui como el campo que transporta la password
    # EN TEXTO PLANO del request hasta el caso de uso -- el caso de uso es
    # quien la hashea antes de persistir (ver `RegisterUserUseCase.execute`).
    candidate = User(
        id=None,
        email=payload.email,
        password_hash=payload.password,
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )

    try:
        created = use_case.execute(candidate)
    except EmailAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un usuario registrado con el email '{exc.email}'.",
        ) from exc
    except InvalidRoleError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rol invalido: '{exc.role}'.",
        ) from exc

    db.commit()
    return UserRead.model_validate(created)


@router.get(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    repository = SqlAlchemyUserRepository(db)
    user = repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_USUARIO_NO_ENCONTRADO)
    return UserRead.model_validate(user)


@router.get(
    "",
    response_model=list[UserRead],
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def list_users(role: str | None = None, db: Session = Depends(get_db)) -> list[UserRead]:
    """RF002: listar usuarios, opcionalmente filtrados por rol."""
    repository = SqlAlchemyUserRepository(db)
    if role is not None:
        use_case = ListUsersByRoleUseCase(user_repository=repository)
        users = use_case.execute(role)
    else:
        users = [*repository.list_by_role("admin"), *repository.list_by_role("entrenador"), *repository.list_by_role("cliente")]
    return [UserRead.model_validate(u) for u in users]


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    dependencies=[Depends(require_role("admin"))],
)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> UserRead:
    repository = SqlAlchemyUserRepository(db)
    existing = repository.get_by_id(user_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_USUARIO_NO_ENCONTRADO)

    updated_data = User(
        id=existing.id,
        email=existing.email,
        password_hash=existing.password_hash,
        full_name=payload.full_name if payload.full_name is not None else existing.full_name,
        role=existing.role,
        is_active=payload.is_active if payload.is_active is not None else existing.is_active,
    )
    updated = repository.update(updated_data)
    db.commit()
    return UserRead.model_validate(updated)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin"))],
)
def delete_user(user_id: int, db: Session = Depends(get_db)) -> None:
    repository = SqlAlchemyUserRepository(db)
    existing = repository.get_by_id(user_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_USUARIO_NO_ENCONTRADO)
    repository.delete(user_id)
    db.commit()
