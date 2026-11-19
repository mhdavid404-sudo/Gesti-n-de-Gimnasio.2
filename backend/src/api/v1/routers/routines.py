"""Router FastAPI del modulo Routines (RF007, RF008, RF012, RF013).

Autorizacion por endpoint (criterio decidido en esta entrada de Entrega 2
del modulo Ejercicios y Rutinas, ver DECISIONES.md):

- `POST /exercises` (catalogo): `admin` o `entrenador` -- ambos construyen
  rutinas y necesitan poder ampliar el catalogo de ejercicios; sin caso de
  uso dedicado porque no hay ninguna invariante de negocio propia (mismo
  criterio ya aplicado al CRUD de `MembershipPlan`).
- `GET /exercises`: cualquier rol autenticado -- catalogo no sensible.
- `POST /routines`: `admin` o `entrenador` -- la invariante REAL (rol del
  creador) la aplica `CreateRoutineUseCase`, esto es solo el primer filtro.
- `GET /routines` y `GET /routines/{id}`: cualquier rol autenticado -- una
  rutina es una plantilla reutilizable, sin ownership de dato (a diferencia
  de `ClientProfile`/`Membership`/`Payment`); el cliente necesita poder ver
  el detalle de una rutina que tiene asignada.
- `POST /routines/{id}/exercises`: `admin` o `entrenador`.
- `GET /routines/{id}/exercises`: cualquier rol autenticado.
- `POST /routines/assignments`: `admin` o `entrenador` -- si es
  `entrenador`, `AssignRoutineToClientUseCase` valida que el cliente sea
  suyo (traducido a 403 si no).
- `GET /routines/assignments/clients/{client_id}`: ownership por dato igual
  que el resto del proyecto -- `admin` cualquiera; `entrenador` solo si el
  cliente es suyo; `cliente` solo el propio.
- `PATCH /routines/assignments/{assignment_id}` (NUEVO, no estaba en el
  esqueleto original -- ver DECISIONES.md, pieza que completa RF012 para
  este modulo): `admin` cualquiera; `entrenador` solo si el cliente de esa
  asignacion es suyo; `cliente` NO puede (RF013 es de solo lectura).
- `DELETE /routines/assignments/{assignment_id}` (NUEVO, 2026-11-18,
  ampliacion de RF012 "quitar una asignacion sin perder la bitacora"):
  mismo criterio de ownership que el `PATCH` de arriba.
- `PATCH /routines/{id}` y `DELETE /routines/{id}` (NUEVOS, 2026-11-18,
  ampliacion de RF007/RF012 "editar/eliminar rutina"): `admin` cualquiera;
  `entrenador` solo las rutinas que el mismo creo (`UnauthorizedRoutineEditError`
  si no); `cliente` NO puede. `DELETE` desactiva la rutina en vez de
  borrarla si tiene asignaciones existentes (conserva el historial) -- ver
  `DeleteOrDeactivateRoutineUseCase`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.routines import (
    ExerciseCreate,
    ExerciseRead,
    RoutineAssignmentCreate,
    RoutineAssignmentRead,
    RoutineAssignmentUpdate,
    RoutineCreate,
    RoutineDeleteResult,
    RoutineExerciseCreate,
    RoutineExerciseRead,
    RoutineRead,
    RoutineUpdate,
)
from src.application.routines.use_cases import (
    AddExerciseToRoutineUseCase,
    AssignRoutineToClientUseCase,
    CreateRoutineUseCase,
    DeleteOrDeactivateRoutineUseCase,
    DeleteRoutineAssignmentUseCase,
    GetClientRoutineHistoryUseCase,
    UpdateRoutineAssignmentUseCase,
    UpdateRoutineUseCase,
)
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.routines.entities import Exercise, Routine, RoutineAssignment, RoutineExercise
from src.domain.routines.exceptions import (
    ExerciseNotFoundError,
    InvalidAssignmentStatusError,
    RoutineAssignmentNotFoundError,
    RoutineNotFoundError,
    UnauthorizedRoutineAssignmentError,
    UnauthorizedRoutineCreatorError,
    UnauthorizedRoutineEditError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.notifications import SqlAlchemyAuditLogRepository
from src.infrastructure.repositories.routines import (
    SqlAlchemyExerciseRepository,
    SqlAlchemyRoutineAssignmentRepository,
    SqlAlchemyRoutineRepository,
)
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

exercises_router = APIRouter(prefix="/exercises", tags=["routines"])
router = APIRouter(prefix="/routines", tags=["routines"])

_RUTINA_NO_ENCONTRADA = "La rutina solicitada no existe."
_EJERCICIO_NO_ENCONTRADO = "El ejercicio solicitado no existe."
_ASIGNACION_NO_ENCONTRADA = "La asignacion de rutina solicitada no existe."
_CLIENTE_NO_ENCONTRADO = "El cliente solicitado no existe."
_SIN_ACCESO_AL_HISTORIAL = "No tienes acceso al historial de este cliente."


@exercises_router.post(
    "",
    response_model=ExerciseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def create_exercise(payload: ExerciseCreate, db: Session = Depends(get_db)) -> ExerciseRead:
    """Catalogo de ejercicios reutilizable (soporte de RF007/RF008). Sin
    caso de uso dedicado -- no hay invariante de negocio propia (mismo
    criterio ya aplicado al CRUD de `MembershipPlan`)."""
    exercise_repository = SqlAlchemyExerciseRepository(db)
    created = exercise_repository.add(
        Exercise(
            id=None,
            name=payload.name,
            muscle_group=payload.muscle_group,
            description=payload.description,
            equipment=payload.equipment,
        )
    )
    db.commit()
    return ExerciseRead.model_validate(created)


@exercises_router.get("", response_model=list[ExerciseRead])
def list_exercises(db: Session = Depends(get_db)) -> list[ExerciseRead]:
    """Cualquier rol autenticado -- catalogo no sensible."""
    exercise_repository = SqlAlchemyExerciseRepository(db)
    return [ExerciseRead.model_validate(e) for e in exercise_repository.list_all()]


@router.post(
    "",
    response_model=RoutineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def create_routine(
    payload: RoutineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineRead:
    """RF007: crear una rutina. `created_by` NUNCA viene del body (ver
    correccion de seguridad en `api/v1/schemas/routines.py`) -- se rellena
    siempre con el `id` del usuario autenticado. La invariante real (rol
    entrenador/admin) la aplica `CreateRoutineUseCase`."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    use_case = CreateRoutineUseCase(
        routine_repository=routine_repository, user_repository=user_repository
    )

    try:
        created = use_case.execute(
            Routine(
                id=None,
                name=payload.name,
                created_by=current_user.id,  # type: ignore[arg-type]
                description=payload.description,
            )
        )
    except UnauthorizedRoutineCreatorError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return RoutineRead.model_validate(created)


@router.get("", response_model=list[RoutineRead])
def list_routines(db: Session = Depends(get_db)) -> list[RoutineRead]:
    """Cualquier rol autenticado -- una rutina es plantilla reutilizable,
    sin ownership de dato."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    return [RoutineRead.model_validate(r) for r in routine_repository.list_all()]


# IMPORTANTE: las rutas estaticas bajo "/assignments" deben declararse
# ANTES que "/{routine_id}" -- FastAPI/Starlette resuelve las rutas en el
# orden de registro, y "assignments" calzaria como valor de `routine_id`
# (fallando la validacion de tipo `int`) si quedara despues.
@router.post(
    "/assignments",
    response_model=RoutineAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def assign_routine_to_client(
    payload: RoutineAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineAssignmentRead:
    """RF007: asignar una rutina a un cliente. `assigned_by` NUNCA viene
    del body -- se rellena con el usuario autenticado. Si es `entrenador`,
    `AssignRoutineToClientUseCase` valida que el cliente sea suyo."""
    assignment_repository = SqlAlchemyRoutineAssignmentRepository(db)
    routine_repository = SqlAlchemyRoutineRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = AssignRoutineToClientUseCase(
        assignment_repository=assignment_repository,
        routine_repository=routine_repository,
        client_repository=client_repository,
    )

    try:
        created = use_case.execute(
            RoutineAssignment(
                id=None,
                routine_id=payload.routine_id,
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
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAssignmentStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnauthorizedRoutineAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return RoutineAssignmentRead.model_validate(created)


@router.get("/assignments/clients/{client_id}", response_model=list[RoutineAssignmentRead])
def get_client_routine_history(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RoutineAssignmentRead]:
    """RF008: historial de rutinas de un cliente. Tambien cubre RF013
    (cliente ve lo propio) y RF012 (entrenador ve lo asignado) -- ownership
    por dato igual que el resto del proyecto: `admin` cualquiera;
    `entrenador` solo si el cliente es suyo; `cliente` solo el propio."""
    client_repository = SqlAlchemyClientProfileRepository(db)
    assignment_repository = SqlAlchemyRoutineAssignmentRepository(db)

    profile = client_repository.get_by_id(client_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_CLIENTE_NO_ENCONTRADO)

    if current_user.role == "entrenador" and profile.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)
    if current_user.role == "cliente" and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_AL_HISTORIAL)

    use_case = GetClientRoutineHistoryUseCase(assignment_repository=assignment_repository)
    return [RoutineAssignmentRead.model_validate(a) for a in use_case.execute(client_id)]


@router.patch(
    "/assignments/{assignment_id}",
    response_model=RoutineAssignmentRead,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def update_routine_assignment(
    assignment_id: int,
    payload: RoutineAssignmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineAssignmentRead:
    """RF012 (NUEVO, ver DECISIONES.md): cambiar `status`/`notes` de una
    asignacion existente. 2026-11-18 (ampliacion de RF012, "corregir una
    asignacion, error de dedo"): tambien admite corregir
    `routine_id`/`assigned_date`. `cliente` bloqueado de entrada (RF013 es
    solo lectura). `entrenador` solo si el cliente de esa asignacion es
    suyo. Editar NUNCA elimina la asignacion, aunque ya este 'completada'
    -- eso es el `DELETE` de abajo, un endpoint aparte."""
    assignment_repository = SqlAlchemyRoutineAssignmentRepository(db)
    routine_repository = SqlAlchemyRoutineRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = UpdateRoutineAssignmentUseCase(
        assignment_repository=assignment_repository,
        routine_repository=routine_repository,
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
            routine_id=payload.routine_id,
            assigned_date=payload.assigned_date,
        )
    except RoutineAssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidAssignmentStatusError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except UnauthorizedRoutineAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return RoutineAssignmentRead.model_validate(updated)


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def delete_routine_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """2026-11-18 (ampliacion de RF012, "quitar una asignacion sin perder
    la bitacora"): la fila se elimina, pero la eliminacion queda
    registrada en `AuditLog` ANTES de borrarla -- el registro sobrevive a
    la fila (ver `DeleteRoutineAssignmentUseCase`). `cliente` bloqueado de
    entrada; `entrenador` solo si el cliente de esa asignacion es suyo."""
    assignment_repository = SqlAlchemyRoutineAssignmentRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = DeleteRoutineAssignmentUseCase(
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
    except RoutineAssignmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedRoutineAssignmentError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()


@router.patch(
    "/{routine_id}",
    response_model=RoutineRead,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def update_routine(
    routine_id: int,
    payload: RoutineUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineRead:
    """2026-11-18 (ampliacion de RF007/RF012, "editar rutina"): cambiar
    nombre/descripcion de una rutina del catalogo. `admin` puede editar
    cualquiera; `entrenador` solo las que el mismo creo; `cliente`
    bloqueado de entrada."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    use_case = UpdateRoutineUseCase(
        routine_repository=routine_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        updated = use_case.execute(
            routine_id,
            name=payload.name,
            description=payload.description,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
        )
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedRoutineEditError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    return RoutineRead.model_validate(updated)


@router.delete(
    "/{routine_id}",
    response_model=RoutineDeleteResult,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def delete_routine(
    routine_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RoutineDeleteResult:
    """2026-11-18 (ampliacion de RF007/RF012, "eliminar rutina"): elimina
    la rutina si no tiene ninguna asignacion; si tiene, la DESACTIVA en
    vez de borrarla (conserva el historial) -- ver
    `DeleteOrDeactivateRoutineUseCase`. Devuelve 200 (no 204) para que el
    frontend sepa cual de las dos paso. `admin` puede eliminar/desactivar
    cualquiera; `entrenador` solo las que el mismo creo."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    assignment_repository = SqlAlchemyRoutineAssignmentRepository(db)
    use_case = DeleteOrDeactivateRoutineUseCase(
        routine_repository=routine_repository,
        assignment_repository=assignment_repository,
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
    )

    try:
        deleted, routine = use_case.execute(
            routine_id,
            updater_role=current_user.role,
            updater_id=current_user.id,  # type: ignore[arg-type]
        )
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedRoutineEditError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    db.commit()
    if deleted:
        return RoutineDeleteResult(deleted=True, routine=None, message="Rutina eliminada.")
    return RoutineDeleteResult(
        deleted=False,
        routine=RoutineRead.model_validate(routine),
        message="La rutina tiene asignaciones existentes: se desactivo en vez de eliminarse.",
    )


@router.get("/{routine_id}", response_model=RoutineRead)
def get_routine(routine_id: int, db: Session = Depends(get_db)) -> RoutineRead:
    """Cualquier rol autenticado -- el cliente necesita ver el detalle de
    una rutina que tiene asignada."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    routine = routine_repository.get_by_id(routine_id)
    if routine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_RUTINA_NO_ENCONTRADA)
    return RoutineRead.model_validate(routine)


@router.post(
    "/{routine_id}/exercises",
    response_model=RoutineExerciseRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "entrenador"))],
)
def add_exercise_to_routine(
    routine_id: int, payload: RoutineExerciseCreate, db: Session = Depends(get_db)
) -> RoutineExerciseRead:
    """RF007: agregar un ejercicio de catalogo a una rutina. Valida que la
    rutina y el ejercicio existan."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    exercise_repository = SqlAlchemyExerciseRepository(db)
    use_case = AddExerciseToRoutineUseCase(
        routine_repository=routine_repository, exercise_repository=exercise_repository
    )

    try:
        created = use_case.execute(
            RoutineExercise(
                id=None,
                routine_id=routine_id,
                exercise_id=payload.exercise_id,
                sets=payload.sets,
                reps=payload.reps,
                order_index=payload.order_index,
                rest_seconds=payload.rest_seconds,
                notes=payload.notes,
            )
        )
    except RoutineNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ExerciseNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    db.commit()
    return RoutineExerciseRead.model_validate(created)


@router.get("/{routine_id}/exercises", response_model=list[RoutineExerciseRead])
def list_routine_exercises(routine_id: int, db: Session = Depends(get_db)) -> list[RoutineExerciseRead]:
    """Cualquier rol autenticado."""
    routine_repository = SqlAlchemyRoutineRepository(db)
    if routine_repository.get_by_id(routine_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_RUTINA_NO_ENCONTRADA)
    return [
        RoutineExerciseRead.model_validate(re) for re in routine_repository.list_exercises(routine_id)
    ]
