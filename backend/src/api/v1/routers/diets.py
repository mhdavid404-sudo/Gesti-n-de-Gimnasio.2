"""Router FastAPI del modulo Diets (RF009, RF012, RF013).

Autorizacion por endpoint (mismo criterio ya decidido en el modulo
Ejercicios y Rutinas, ver DECISIONES.md -- Diets replica exactamente ese
patron):

- `POST /diets/plans`: `admin` o `entrenador` -- la invariante REAL (rol
  del creador) la aplica `CreateDietPlanUseCase`, esto es solo el primer
  filtro.
- `GET /diets/plans`: cualquier rol autenticado -- un plan de dieta es
  una plantilla reutilizable, sin ownership de dato (a diferencia de
  `ClientProfile`/`Membership`/`Payment`); el cliente necesita poder ver
  el plan que tiene asignado.
- `POST /diets/assignments`: `admin` o `entrenador` -- si es `entrenador`,
  `AssignDietToClientUseCase` valida que el cliente sea suyo (traducido a
  403 si no).
- `GET /diets/assignments/clients/{client_id}`: ownership por dato igual
  que el resto del proyecto -- `admin` cualquiera; `entrenador` solo si
  el cliente es suyo; `cliente` solo el propio.
- `PATCH /diets/assignments/{assignment_id}` (NUEVO, no estaba en el
  esqueleto original -- mismo motivo que en Rutinas, pieza que completa
  RF012 para este modulo): `admin` cualquiera; `entrenador` solo si el
  cliente de esa asignacion es suyo; `cliente` NO puede (RF013 es de
  solo lectura).
- `DELETE /diets/assignments/{assignment_id}` (NUEVO, 2026-11-18,
  ampliacion de RF012 "quitar una asignacion sin perder la bitacora"):
  mismo criterio de ownership que el `PATCH` de arriba.
- `PATCH /diets/plans/{id}` y `DELETE /diets/plans/{id}` (NUEVOS,
  2026-11-18, ampliacion de RF009/RF012 "editar/eliminar dieta"): `admin`
  cualquiera; `entrenador` solo los planes que el mismo creo
  (`UnauthorizedDietEditError` si no); `cliente` NO puede. `DELETE`
  desactiva el plan en vez de borrarlo si tiene asignaciones existentes
  (conserva el historial) -- ver `DeleteOrDeactivateDietPlanUseCase`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.diets import (
    DietAssignmentCreate,
    DietAssignmentRead,
    DietAssignmentUpdate,
    DietPlanCreate,
    DietPlanDeleteResult,
    DietPlanRead,
    DietPlanUpdate,
)
from src.application.diets.use_cases import (
    AssignDietToClientUseCase,
    CreateDietPlanUseCase,
    DeleteDietAssignmentUseCase,
    DeleteOrDeactivateDietPlanUseCase,
    GetClientDietHistoryUseCase,
    UpdateDietAssignmentUseCase,
    UpdateDietPlanUseCase,
)
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.diets.entities import DietAssignment, DietPlan
from src.domain.diets.exceptions import (
    DietAssignmentNotFoundError,
    DietPlanNotFoundError,
    InvalidDietAssignmentStatusError,
    UnauthorizedDietAssignmentError,
    UnauthorizedDietEditError,
    UnauthorizedDietPlanCreatorError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.diets import (
    SqlAlchemyDietAssignmentRepository,
    SqlAlchemyDietPlanRepository,
)
from src.infrastructure.repositories.notifications import SqlAlchemyAuditLogRepository
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

router = APIRouter(prefix="/diets", tags=["diets"])

_PLAN_NO_ENCONTRADO = "El plan de dieta solicitado no existe."
_ASIGNACION_NO_ENCONTRADA = "La asignacion de dieta solicitada no existe."
_CLIENTE_NO_ENCONTRADO = "El cliente solicitado no existe."
_SIN_ACCESO_AL_HISTORIAL = "No tienes acceso al historial de este cliente."


@router.post(
    "/plans",
    response_model=DietPlanRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def create_diet_plan(
    payload: DietPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietPlanRead:
    """RF009: crear un plan de dieta. `created_by` NUNCA viene del body
    (ver correccion de seguridad en `api/v1/schemas/diets.py`) -- se
    rellena siempre con el `id` del usuario autenticado. La invariante
    real (rol entrenador/admin) la aplica `CreateDietPlanUseCase`."""
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    use_case = CreateDietPlanUseCase(
        diet_plan_repository=diet_plan_repository, user_repository=user_repository
    )

    try:
        created = use_case.execute(
            DietPlan(
                id=None,
                name=payload.name,
                created_by=current_user.id,  # type: ignore[arg-type]
                description=payload.description,
                calories_target=payload.calories_target,
            )
        )
    except UnauthorizedDietPlanCreatorError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return DietPlanRead.model_validate(created)


@router.get("/plans", response_model=list[DietPlanRead])
def list_diet_plans(db: Session = Depends(get_db)) -> list[DietPlanRead]:
    """Cualquier rol autenticado -- un plan de dieta es plantilla
    reutilizable, sin ownership de dato."""
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    return [DietPlanRead.model_validate(p) for p in diet_plan_repository.list_all()]


# IMPORTANTE: las rutas estaticas bajo "/assignments" deben declararse
# ANTES que cualquier ruta con un segmento dinamico equivalente, mismo
# motivo ya documentado en `routers/routines.py`.
@router.post(
    "/assignments",
    response_model=DietAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def assign_diet_to_client(
    payload: DietAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietAssignmentRead:
    """RF009: asignar un plan de dieta a un cliente. `assigned_by` NUNCA
    viene del body -- se rellena con el usuario autenticado. Si es
    `entrenador`, `AssignDietToClientUseCase` valida que el cliente sea
    suyo."""
    assignment_repository = SqlAlchemyDietAssignmentRepository(db)
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = AssignDietToClientUseCase(
        assignment_repository=assignment_repository,
        diet_plan_repository=diet_plan_repository,
        client_repository=client_repository,
    )

    try:
        created = use_case.execute(
            DietAssignment(
                id=None,
                diet_plan_id=payload.diet_plan_id,
                client_id=payload.client_id,
                assigned_by=current_user.id,  # type: ignore[arg-type]
                assigned_date=payload.assigned_date,
                status=payload.status,
                notes=payload.notes,
            ),
            assigner_role=current_user.role,
            assigner_id=current_user.id,  # type: ignore[arg-type]
        )
    except ClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente {exc.client_id} no existe.",
        ) from exc
    except DietPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidDietAssignmentStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnauthorizedDietAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return DietAssignmentRead.model_validate(created)


@router.get("/assignments/clients/{client_id}", response_model=list[DietAssignmentRead])
def get_client_diet_history(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DietAssignmentRead]:
    """RF012/RF013: historial de dietas de un cliente. Tambien cubre
    RF013 (cliente ve lo propio) y RF012 (entrenador ve lo asignado) --
    ownership por dato igual que el resto del proyecto: `admin`
    cualquiera; `entrenador` solo si el cliente es suyo; `cliente` solo
    el propio."""
    client_repository = SqlAlchemyClientProfileRepository(db)
    assignment_repository = SqlAlchemyDietAssignmentRepository(db)

    profile = client_repository.get_by_id(client_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO)

    if current_user.role == "entrenador" and profile.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)
    if current_user.role == "cliente" and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)

    use_case = GetClientDietHistoryUseCase(assignment_repository=assignment_repository)
    return [DietAssignmentRead.model_validate(a) for a in use_case.execute(client_id)]


@router.patch(
    "/assignments/{assignment_id}",
    response_model=DietAssignmentRead,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def update_diet_assignment(
    assignment_id: int,
    payload: DietAssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietAssignmentRead:
    """RF012 (NUEVO, ver DECISIONES.md): cambiar `status`/`notes` de una
    asignacion existente. 2026-11-18 (ampliacion de RF012, "corregir una
    asignacion, error de dedo"): tambien admite corregir
    `diet_plan_id`/`assigned_date`. `cliente` bloqueado de entrada (RF013
    es solo lectura). `entrenador` solo si el cliente de esa asignacion es
    suyo. Editar NUNCA elimina la asignacion, aunque ya este 'completada'
    -- eso es el `DELETE` de abajo, un endpoint aparte."""
    assignment_repository = SqlAlchemyDietAssignmentRepository(db)
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = UpdateDietAssignmentUseCase(
        assignment_repository=assignment_repository,
        diet_plan_repository=diet_plan_repository,
        client_repository=client_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        updated = use_case.execute(
            assignment_id,
            status_value=payload.status,
            notes=payload.notes,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
            diet_plan_id=payload.diet_plan_id,
            assigned_date=payload.assigned_date,
        )
    except DietAssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DietPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidDietAssignmentStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnauthorizedDietAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return DietAssignmentRead.model_validate(updated)


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def delete_diet_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """2026-11-18 (ampliacion de RF012, "quitar una asignacion sin perder
    la bitacora"): la fila se elimina, pero la eliminacion queda
    registrada en `AuditLog` ANTES de borrarla (ver
    `DeleteDietAssignmentUseCase`). `cliente` bloqueado de entrada;
    `entrenador` solo si el cliente de esa asignacion es suyo."""
    assignment_repository = SqlAlchemyDietAssignmentRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = DeleteDietAssignmentUseCase(
        assignment_repository=assignment_repository,
        client_repository=client_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        use_case.execute(
            assignment_id,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
        )
    except DietAssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedDietAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()


@router.patch(
    "/plans/{diet_plan_id}",
    response_model=DietPlanRead,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def update_diet_plan(
    diet_plan_id: int,
    payload: DietPlanUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietPlanRead:
    """2026-11-18 (ampliacion de RF009/RF012, "editar dieta"): cambiar
    nombre/descripcion/objetivo calorico de un plan del catalogo. `admin`
    puede editar cualquiera; `entrenador` solo los que el mismo creo;
    `cliente` bloqueado de entrada."""
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    use_case = UpdateDietPlanUseCase(
        diet_plan_repository=diet_plan_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        updated = use_case.execute(
            diet_plan_id,
            name=payload.name,
            description=payload.description,
            calories_target=payload.calories_target,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
        )
    except DietPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedDietEditError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return DietPlanRead.model_validate(updated)


@router.delete(
    "/plans/{diet_plan_id}",
    response_model=DietPlanDeleteResult,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def delete_diet_plan(
    diet_plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DietPlanDeleteResult:
    """2026-11-18 (ampliacion de RF009/RF012, "eliminar dieta"): elimina
    el plan si no tiene ninguna asignacion; si tiene, lo DESACTIVA en vez
    de borrarlo (conserva el historial) -- ver
    `DeleteOrDeactivateDietPlanUseCase`. Devuelve 200 (no 204) para que el
    frontend sepa cual de las dos paso. `admin` puede eliminar/desactivar
    cualquiera; `entrenador` solo los que el mismo creo."""
    diet_plan_repository = SqlAlchemyDietPlanRepository(db)
    assignment_repository = SqlAlchemyDietAssignmentRepository(db)
    use_case = DeleteOrDeactivateDietPlanUseCase(
        diet_plan_repository=diet_plan_repository,
        assignment_repository=assignment_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        deleted, plan = use_case.execute(
            diet_plan_id,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
        )
    except DietPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedDietEditError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    if deleted:
        return DietPlanDeleteResult(deleted=True, diet_plan=None, message="Plan de dieta eliminado.")
    return DietPlanDeleteResult(
        deleted=False,
        diet_plan=DietPlanRead.model_validate(plan),
        message="El plan tiene asignaciones existentes: se desactivo en vez de eliminarse.",
    )
