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
- `PATCH /users/{id}` y `DELETE /users/{id}`: solo `admin`. `PATCH` con
  `is_active` es como se activa/desactiva una cuenta desde la pantalla
  "Usuarios" -- un admin no puede desactivarse a sí mismo (400). Alta
  (`POST /users`) y activar/desactivar quedan en `AuditLog`
  (`action="crear_usuario"`/`"activar_usuario"`/`"desactivar_usuario"`);
  antes de esta entrada, `RegisterUserUseCase` no registraba nada.
- `POST /users/{id}/reset-password`: solo `admin`. No existe self-service
  de cambio de contraseña ni "olvidé mi contraseña" en el sistema (ver
  DECISIONES.md, entrada "Restablecimiento de contraseña por Admin") -- la
  unica via para recuperar el acceso de una cuenta es que un admin la
  restablezca aqui; genera una temporal nueva (mismo mecanismo que
  `RegisterClientUseCase`), la devuelve en texto claro UNA SOLA VEZ y
  queda registrado en `AuditLog`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.users import PasswordResetResponse, UserCreate, UserRead, UserUpdate
from src.application.notifications.use_cases import RecordAuditEventUseCase
from src.application.users.use_cases import (
    ListUsersByRoleUseCase,
    RegisterUserUseCase,
    ResetUserPasswordUseCase,
)
from src.domain.notifications.entities import AuditLog
from src.domain.users.entities import User
from src.domain.users.exceptions import EmailAlreadyExistsError, InvalidRoleError
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.notifications import SqlAlchemyAuditLogRepository
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

router = APIRouter(prefix="/users", tags=["users"])

_USUARIO_NO_ENCONTRADO = "El usuario solicitado no existe."


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def register_user(
    payload: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    """RF001: registrar un usuario nuevo con un rol. Solo `admin`."""
    repository = SqlAlchemyUserRepository(db)
    use_case = RegisterUserUseCase(
        user_repository=repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

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
        created = use_case.execute(candidate, current_user.id)  # type: ignore[arg-type]
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
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    repository = SqlAlchemyUserRepository(db)
    existing = repository.get_by_id(user_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_USUARIO_NO_ENCONTRADO)

    # Un admin no puede desactivarse a si mismo -- si pudiera, y fuera el
    # unico admin activo, nadie quedaria con permiso para reactivar ninguna
    # cuenta (incluida la suya propia). Se compara contra el id del usuario
    # autenticado, no contra el rol, porque la regla es sobre la PROPIA
    # cuenta, no sobre "otro admin" (eso si esta permitido).
    if user_id == current_user.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrador no puede desactivarse a sí mismo.",
        )

    updated_data = User(
        id=existing.id,
        email=existing.email,
        password_hash=existing.password_hash,
        full_name=payload.full_name if payload.full_name is not None else existing.full_name,
        role=existing.role,
        is_active=payload.is_active if payload.is_active is not None else existing.is_active,
    )
    updated = repository.update(updated_data)

    # Activar/desactivar es una accion administrativa sobre la cuenta de
    # otra persona -- queda en Bitacora, igual que restablecer su
    # contraseña. Solo si `is_active` realmente cambio (una edicion de
    # `full_name` que no toca el estado no genera ruido en la bitacora).
    if payload.is_active is not None and payload.is_active != existing.is_active:
        RecordAuditEventUseCase(audit_log_repository=SqlAlchemyAuditLogRepository(db)).execute(
            AuditLog(
                id=None,
                user_id=current_user.id,  # type: ignore[arg-type]
                action="activar_usuario" if payload.is_active else "desactivar_usuario",
                entity_type="user",
                entity_id=str(user_id),
                details=f"Usuario '{existing.email}' {'activado' if payload.is_active else 'desactivado'}.",
            )
        )

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


@router.post(
    "/{user_id}/reset-password",
    response_model=PasswordResetResponse,
    dependencies=[Depends(require_role("admin"))],
)
def reset_user_password(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PasswordResetResponse:
    """Restablece la contraseña de cualquier usuario (admin), sin pedir la
    anterior. La temporal se devuelve en texto claro UNA SOLA VEZ -- mismo
    criterio que `POST /clients` (ver `ResetUserPasswordUseCase`)."""
    repository = SqlAlchemyUserRepository(db)
    existing = repository.get_by_id(user_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_USUARIO_NO_ENCONTRADO)

    use_case = ResetUserPasswordUseCase(
        user_repository=repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )
    temporary_password = use_case.execute(existing, current_user.id)  # type: ignore[arg-type]

    db.commit()
    return PasswordResetResponse(temporary_password=temporary_password)
