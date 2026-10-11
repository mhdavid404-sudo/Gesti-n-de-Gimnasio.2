"""Router FastAPI del modulo Memberships (RF004, RF006).

Autorizacion por endpoint (criterio decidido en esta entrada de Entrega 2
del modulo Planes y Membresias, ver DECISIONES.md):

- `POST /membership-plans` (alta de plan): solo `admin` -- son datos de
  catalogo/precio, decision administrativa/financiera, igual que el alta de
  perfil de cliente en el modulo Clientes.
- `GET /membership-plans` (listado de catalogo): cualquier rol autenticado
  -- es catalogo no sensible (nombre/precio/duracion/beneficios), no datos
  personales; un entrenador o cliente tambien necesita poder leerlo (ej.
  para mostrar opciones al asignar/consultar una membresia).
- `POST /memberships` (asignar): solo `admin` -- asignar/cobrar una
  membresia es una decision administrativa/financiera, no una accion del
  propio entrenador o del cliente.
- `GET /memberships` (listado, filtro opcional `client_id`): los 3 roles
  pueden llegar aqui -- el filtro real es POR DATO (ownership), mismo
  principio que `GET /clients/{id}` (ver `routers/clients.py`):
    - `admin`: ve todas, o solo las de `client_id` si lo manda en query.
    - `entrenador`: solo las de SUS clientes asignados (resueltos via
      `ClientProfileRepository.list_by_trainer`); un `client_id` de query
      que no sea uno de los suyos se ignora (nunca ve membresias ajenas).
    - `cliente`: solo la(s) suya(s) propia(s) (resuelve su `client_id` via
      `ClientProfileRepository.get_by_user_id`); el `client_id` de query se
      ignora -- nunca ve membresias de otro cliente.
  `MembershipRepository` (ya implementado, sin tocar) no expone un
  `list_all` -- "ver todo" para `admin` se resuelve agregando
  `list_by_client` sobre todos los `client_id` reales
  (`ClientProfileRepository.list_all`), igual de valido que una consulta
  directa para el alcance de este proyecto.
- `GET /memberships/{id}`: mismo criterio de ownership por dato que
  `GET /clients/{id}` -- los 3 roles pueden llegar, el filtro se aplica
  sobre el `ClientProfile` dueno de la membresia (`trainer_id`/`user_id`).
- `PATCH /memberships/{id}` (cambiar status): solo `admin` -- hoy
  (RF006/deteccion automatica todavia no existe) cualquier cambio de
  estado es una decision manual, igual de administrativa/financiera que el
  resto de las decisiones de este tipo ya resueltas en el modulo Clientes.
- `POST /memberships/detect-expiring` (RF006, modulo
  "Vencimientos/Notificaciones"): solo `admin` -- corre
  `DetectExpiringMembershipsUseCase` (ver docstring de la clase en
  `application/memberships/use_cases.py`), que transiciona a "vencida" las
  membresias ya vencidas y genera las notificaciones correspondientes. Es
  una accion administrativa que muta datos (cambia `status`, crea
  `Notification`), por eso queda detras de `admin` igual que
  `PATCH /memberships/{id}` -- ningun rol lo dispara "en su propio
  nombre".
- `GET /memberships/expiring` (RF006): a diferencia del POST anterior, es
  de SOLO LECTURA -- calcula al vuelo (sin mutar nada) que membresias
  estan vencidas (status `"vencida"` ya persistido) o por vencer (status
  `"activa"` con `end_date` dentro de la ventana `days_ahead`), mismo
  criterio que `frontend/src/utils/membership.ts`
  (`isMembershipExpiringSoon`/`getMembershipDisplayStatus`). No depende de
  que el POST se haya ejecutado antes. Ownership por dato: mismo patron
  que `list_memberships` -- `admin` ve todas, `entrenador` solo las de sus
  clientes asignados. Se decide permitir tambien a `cliente` (ve solo
  la(s) suya(s)): aunque en la practica un cliente solo tiene una
  membresia activa, ya puede ver el detalle completo via
  `GET /memberships/{id}` y `GET /memberships` -- restringir
  especificamente este endpoint a admin/entrenador seria una
  inconsistencia arbitraria frente a esos dos.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.memberships import (
    MembershipCreate,
    MembershipPlanCreate,
    MembershipPlanRead,
    MembershipRead,
    MembershipUpdate,
)
from src.application.memberships.use_cases import (
    AssignMembershipUseCase,
    DetectExpiringMembershipsUseCase,
)
from src.application.notifications.use_cases import NotifyUserUseCase
from src.domain.clients.entities import ClientProfile
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.memberships.entities import Membership, MembershipPlan
from src.domain.memberships.exceptions import (
    InvalidMembershipDateRangeError,
    InvalidMembershipStatusError,
    MembershipPlanNotFoundError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.memberships import (
    SqlAlchemyMembershipPlanRepository,
    SqlAlchemyMembershipRepository,
)
from src.infrastructure.repositories.notifications import SqlAlchemyNotificationRepository

router = APIRouter(prefix="/memberships", tags=["memberships"])
plans_router = APIRouter(prefix="/membership-plans", tags=["memberships"])

_PLAN_NO_ENCONTRADO = "El plan de membresia solicitado no existe."
_MEMBRESIA_NO_ENCONTRADA = "La membresia solicitada no existe."
_SIN_ACCESO_A_MEMBRESIA = "No tienes acceso a esta membresia."
_VENTANA_POR_VENCER_DIAS = 7


def _ensure_access_to_membership(current_user: User, profile: ClientProfile) -> None:
    """Mismo filtro por dato que `_enrich`/los checks de `routers/clients.py`:
    `admin` sin restriccion; `entrenador` solo si es su cliente asignado;
    `cliente` solo si es su propio perfil."""
    if current_user.role == "entrenador" and profile.trainer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_MEMBRESIA)
    if current_user.role == "cliente" and profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_SIN_ACCESO_A_MEMBRESIA)


# --- Plan CRUD -------------------------------------------------------------
# Sin caso de uso dedicado a proposito: crear/listar un plan del catalogo no
# tiene ninguna invariante de negocio propia (a diferencia de asignar una
# membresia, que si valida existencia de cliente/plan, status y rango de
# fechas) -- usar el repositorio directo desde el router evita una capa de
# indireccion vacia. Si en una entrega futura aparece una regla real (ej.
# "no se puede borrar un plan con membresias activas"), ahi si amerita un
# caso de uso propio en `application/memberships/use_cases.py`.


@plans_router.post(
    "",
    response_model=MembershipPlanRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_membership_plan(payload: MembershipPlanCreate, db: Session = Depends(get_db)) -> MembershipPlanRead:
    """RF004: alta de un plan de membresia (Basica/VIP/Premium, etc). Solo `admin`."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    created = plan_repository.add(
        MembershipPlan(
            id=None,
            name=payload.name,
            price=payload.price,
            duration_days=payload.duration_days,
            description=payload.description,
            benefits=payload.benefits,
        )
    )
    db.commit()
    return MembershipPlanRead.model_validate(created)


@plans_router.get("", response_model=list[MembershipPlanRead])
def list_membership_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipPlanRead]:
    """Catalogo no sensible: cualquier rol autenticado puede listar planes."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    return [MembershipPlanRead.model_validate(plan) for plan in plan_repository.list_all()]


# --- Membership -------------------------------------------------------------


@router.post(
    "",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def assign_membership(payload: MembershipCreate, db: Session = Depends(get_db)) -> MembershipRead:
    """RF004: asignar un plan de membresia a un cliente. Solo `admin`."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    use_case = AssignMembershipUseCase(
        membership_repository=membership_repository,
        plan_repository=plan_repository,
        client_repository=client_repository,
    )

    try:
        created = use_case.execute(
            Membership(
                id=None,
                client_id=payload.client_id,
                plan_id=payload.plan_id,
                start_date=payload.start_date,
                end_date=payload.end_date,
                status=payload.status,
            )
        )
    except ClientNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El cliente {exc.client_id} no existe.",
        ) from exc
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except (InvalidMembershipDateRangeError, InvalidMembershipStatusError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return MembershipRead.model_validate(created)


def _resolve_memberships_for_user(
    current_user: User,
    membership_repository: SqlAlchemyMembershipRepository,
    client_repository: SqlAlchemyClientProfileRepository,
    client_id: int | None,
) -> list[Membership]:
    """Ownership por rol, factorizado de `list_memberships` para
    reutilizarse tambien en `GET /memberships/expiring` -- ver docstring
    del modulo arriba."""
    if current_user.role == "entrenador":
        own_client_ids = [
            profile.id for profile in client_repository.list_by_trainer(current_user.id)  # type: ignore[arg-type]
        ]
        if client_id is not None and client_id in own_client_ids:
            own_client_ids = [client_id]
        return [
            m for cid in own_client_ids for m in membership_repository.list_by_client(cid)  # type: ignore[arg-type]
        ]
    if current_user.role == "cliente":
        own_profile = client_repository.get_by_user_id(current_user.id)  # type: ignore[arg-type]
        return (
            membership_repository.list_by_client(own_profile.id)  # type: ignore[arg-type]
            if own_profile is not None
            else []
        )
    # admin
    if client_id is not None:
        return membership_repository.list_by_client(client_id)
    all_client_ids = [profile.id for profile in client_repository.list_all()]
    return [
        m for cid in all_client_ids for m in membership_repository.list_by_client(cid)  # type: ignore[arg-type]
    ]


@router.get("", response_model=list[MembershipRead])
def list_memberships(
    client_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipRead]:
    """Ownership por rol -- ver docstring del modulo arriba."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)

    memberships = _resolve_memberships_for_user(
        current_user, membership_repository, client_repository, client_id
    )
    return [MembershipRead.model_validate(m) for m in memberships]


# IMPORTANTE: estas dos rutas estaticas ("/expiring" y "/detect-expiring")
# deben declararse ANTES que "/{membership_id}" -- FastAPI/Starlette
# resuelve las rutas en el orden en que se registran, y calzarian con el
# patron "/{membership_id}" (fallando la validacion de tipo `int`) si
# quedaran despues.
@router.get("/expiring", response_model=list[MembershipRead])
def list_expiring_memberships(
    days_ahead: int = _VENTANA_POR_VENCER_DIAS,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipRead]:
    """RF006: membresias vencidas o por vencer, calculado al vuelo (SOLO
    LECTURA, no muta nada) -- ver docstring del modulo arriba para el
    criterio completo de calculo y de ownership."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)

    memberships = _resolve_memberships_for_user(
        current_user, membership_repository, client_repository, None
    )

    today = date.today()

    def _is_expired_or_expiring(membership: Membership) -> bool:
        if membership.status == "vencida":
            return True
        if membership.status != "activa":
            return False
        days_left = (membership.end_date - today).days
        return 0 <= days_left <= days_ahead

    filtered = [m for m in memberships if _is_expired_or_expiring(m)]
    return [MembershipRead.model_validate(m) for m in filtered]


@router.post(
    "/detect-expiring",
    response_model=list[MembershipRead],
    dependencies=[Depends(require_role("admin"))],
)
def detect_expiring_memberships(
    days_ahead: int = _VENTANA_POR_VENCER_DIAS,
    db: Session = Depends(get_db),
) -> list[MembershipRead]:
    """RF006: dispara `DetectExpiringMembershipsUseCase`. Solo `admin` --
    ver docstring del modulo arriba.

    Simplificacion documentada en DECISIONES.md: no existe
    cron/scheduler en este proyecto; en un despliegue real esto correria
    como un job diario, aqui es una accion manual."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    notification_repository = SqlAlchemyNotificationRepository(db)
    notify_use_case = NotifyUserUseCase(notification_repository=notification_repository)

    use_case = DetectExpiringMembershipsUseCase(
        membership_repository=membership_repository,
        client_repository=client_repository,
        notify_use_case=notify_use_case,
    )
    affected = use_case.execute(days_ahead=days_ahead)

    db.commit()
    return [MembershipRead.model_validate(m) for m in affected]


@router.get("/{membership_id}", response_model=MembershipRead)
def get_membership(
    membership_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MembershipRead:
    """Mismo criterio de ownership por dato que `GET /clients/{id}`: los 3
    roles pueden llegar, el filtro real se aplica sobre el `ClientProfile`
    dueno de la membresia (no hay rol bloqueado de entrada)."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)

    membership = membership_repository.get_by_id(membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_MEMBRESIA_NO_ENCONTRADA)

    profile = client_repository.get_by_id(membership.client_id)
    if profile is not None:
        _ensure_access_to_membership(current_user, profile)

    return MembershipRead.model_validate(membership)


@router.patch(
    "/{membership_id}",
    response_model=MembershipRead,
    dependencies=[Depends(require_role("admin"))],
)
def update_membership_status(
    membership_id: int, payload: MembershipUpdate, db: Session = Depends(get_db)
) -> MembershipRead:
    """Cambiar el `status` de una membresia es, hoy, una decision manual
    exclusiva de `admin` -- ver docstring del modulo arriba (RF006 todavia
    no existe para automatizarlo)."""
    membership_repository = SqlAlchemyMembershipRepository(db)

    existing = membership_repository.get_by_id(membership_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_MEMBRESIA_NO_ENCONTRADA)

    existing.status = payload.status
    updated = membership_repository.update(existing)

    db.commit()
    return MembershipRead.model_validate(updated)
