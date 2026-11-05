"""Router FastAPI del modulo Memberships (RF004, RF006).

Autorizacion por endpoint (criterio decidido en esta entrada de Entrega 2
del modulo Planes y Membresias, ver DECISIONES.md):

- `POST /membership-plans` (alta de plan): solo `admin` -- son datos de
  catalogo/precio, decision administrativa/financiera, igual que el alta de
  perfil de cliente en el modulo Clientes.
- `GET /membership-plans` (listado de catalogo): PUBLICO, sin autenticacion
  (Entrega 3) -- es catalogo no sensible (nombre/precio/duracion/beneficios),
  no datos personales, y la landing publica (`/`) lo necesita para mostrar
  los planes reales sin pedir login. Antes exigia sesion (cualquier rol
  autenticado); se relaja a publico porque ningun dato de este endpoint deja
  de ser apropiado para un visitante anonimo -- ver DECISIONES.md.
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

Entrega 3, Fase 2 (Planes y servicios extra, amplia RF004/RF005) -- ver
DECISIONES.md:

- `PATCH`/`DELETE /membership-plans/{id}`: solo `admin`. `DELETE` no borra
  sin mas -- usa `DeleteOrDeactivateMembershipPlanUseCase` (desactiva si
  el plan tiene membresias contratadas, elimina de verdad si no).
- `services_router` (`/services`): mismo criterio que `/membership-plans`
  -- catalogo no sensible, `GET` publico, `POST`/`PATCH`/`DELETE` solo
  `admin`. `DELETE` usa `DeleteOrDeactivateServiceUseCase` (mismo patron
  desactivar-si-tiene-contrataciones).
- `GET`/`POST`/`DELETE /membership-plans/{plan_id}/services`: que
  servicios incluye un plan. Requiere sesion (cualquier rol) para `GET`;
  `POST`/`DELETE` solo `admin`.
- `POST /memberships/{membership_id}/services`: CONTRATAR un extra sobre
  la membresia de un cliente. Solo `admin` -- es una decision
  administrativa/financiera (el cliente paga), mismo criterio que
  `POST /payments`; la regla de negocio "cualquier cliente puede
  contratar cualquier extra no incluido en su plan" describe que NO hay
  restriccion de elegibilidad por cliente, no que el cliente lo haga el
  mismo desde la pantalla -- en todo el resto del sistema las acciones que
  mueven dinero las ejecuta `admin` (recepcion), nunca el propio cliente.
- `GET /memberships/{membership_id}/services`: ownership por dato
  encadenado (mismo patron que `GET /payments`) + un recorte de columnas
  por rol en vez de rechazar: `admin`/`cliente` ven el precio
  (`MembershipServiceRead`), `entrenador` ve la misma lista sin precio
  (`MembershipServiceReadLimited`) -- regla explicita del encargo
  ("Entrenador ve los extras de sus clientes asignados (no precios ni
  pagos)").

Entrega 3, ajuste de UX de la pantalla "Membresias" (ver DECISIONES.md) --
la pantalla deja de mostrar el catalogo de planes (eso vive solo en
"Planes y servicios") y pasa a ser un tablero operativo de membresias
ACTIVAS:

- `GET /memberships/board`: indicadores (total de activas, cuantas vencen
  en los proximos 7 dias, ingresos del mes) + la tabla (cliente, plan,
  extras activos, fechas, dias restantes), con filtros opcionales
  `plan_id`/`q` (nombre de cliente). Solo `admin`/`entrenador` -- `cliente`
  NUNCA llega a este tablero (403), consulta su propia membresia en
  `GET /memberships` (ya ownership-filtrado). `entrenador` ve solo sus
  clientes asignados (mismo `_resolve_memberships_for_user` que el resto
  del modulo) y `monthly_revenue` siempre `None` (regla explicita: "sin
  ingresos"). Los indicadores reflejan el total SIN filtrar (`plan_id`/`q`
  solo acotan `items`, la tabla) -- un admin buscando a un cliente no
  pierde de vista el total real mientras busca.
- `POST /memberships/{membership_id}/renew`: accion "Renovar" del
  tablero -- solo `admin`, mismo criterio que el resto de acciones que
  comprometen dinero/contrato en este modulo (asignar membresia, registrar
  pago). Ver `RenewMembershipUseCase` para la regla de extension de
  `end_date`. Deliberadamente NO registra un pago -- "Cobrar" es una
  accion distinta en la UI (navega al formulario de pago de la ficha del
  cliente), para no asumir metodo ni monto.

Cambio de plan (amplia RF004/RF005 de nuevo, ver DECISIONES.md):

- `POST /memberships/{membership_id}/change-plan/preview` y
  `POST /memberships/{membership_id}/change-plan`: mismo body
  (`PlanChangeRequest`) y el MISMO calculo
  (`PreviewChangeMembershipPlanUseCase`) -- preview no escribe nada en la
  base, confirm reusa ese calculo y lo persiste dentro de
  `ChangeMembershipPlanUseCase` (ver su docstring para la regla completa
  de cancelacion de extras y la nota de atomicidad). Solo `admin` --
  cambiar el plan de un cliente es una decision administrativa/financiera,
  mismo criterio que el resto de acciones de este tipo en el modulo.
- `GET /memberships/{membership_id}/services` para `entrenador` ahora
  filtra a extras con `status == "activa"` -- un extra cancelado por un
  cambio de plan (o por cualquier otro motivo) deja de aparecerle,
  regla explicita del encargo ("el entrenador asignado al extra cancelado
  debe dejar de ver ese extra"). `admin`/`cliente` siguen viendo el
  historial completo (incluidos los cancelados, con su status) -- "el
  historial se conserva" es una regla para los datos, no para que
  desaparezcan de la vista de quien necesita auditarlos.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.v1.dependencies import get_current_user, require_role
from src.api.v1.schemas.memberships import (
    ActiveMembershipRow,
    ActiveMembershipsBoard,
    ActiveMembershipsIndicators,
    MembershipCreate,
    MembershipPlanCreate,
    MembershipPlanRead,
    MembershipPlanUpdate,
    MembershipRead,
    MembershipServiceCreate,
    MembershipServiceRead,
    MembershipServiceReadLimited,
    MembershipUpdate,
    PlanChangeContractableRow,
    PlanChangeExtraRow,
    PlanChangePreview,
    PlanChangeRequest,
    PlanServiceAdd,
    ServiceCreate,
    ServiceRead,
    ServiceUpdate,
)
from src.application.memberships.use_cases import (
    AddServiceToPlanUseCase,
    AssignMembershipUseCase,
    ChangeMembershipPlanUseCase,
    ContractMembershipServiceUseCase,
    DeleteOrDeactivateMembershipPlanUseCase,
    DeleteOrDeactivateServiceUseCase,
    DetectExpiringMembershipsUseCase,
    PlanChangeImpact,
    PreviewChangeMembershipPlanUseCase,
    RenewMembershipUseCase,
)
from src.application.notifications.use_cases import NotifyUserUseCase
from src.domain.clients.entities import ClientProfile
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.memberships.entities import Membership, MembershipPlan, Service
from src.domain.memberships.exceptions import (
    InactiveMembershipPlanError,
    InactiveServiceError,
    InvalidMembershipDateRangeError,
    InvalidMembershipStatusError,
    MembershipNotFoundError,
    MembershipPlanNotFoundError,
    SamePlanChangeError,
    ServiceAlreadyIncludedInPlanError,
    ServiceIncludedInPlanError,
    ServiceNotFoundError,
)
from src.domain.users.entities import User
from src.infrastructure.db.session import get_db
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.memberships import (
    SqlAlchemyMembershipPlanRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyMembershipServiceRepository,
    SqlAlchemyPlanServiceRepository,
    SqlAlchemyServiceRepository,
)
from src.infrastructure.repositories.notifications import (
    SqlAlchemyAuditLogRepository,
    SqlAlchemyNotificationRepository,
)
from src.infrastructure.repositories.payments import SqlAlchemyPaymentRepository
from src.infrastructure.repositories.users import SqlAlchemyUserRepository

router = APIRouter(prefix="/memberships", tags=["memberships"])
plans_router = APIRouter(prefix="/membership-plans", tags=["memberships"])
services_router = APIRouter(prefix="/services", tags=["memberships"])

_PLAN_NO_ENCONTRADO = "El plan de membresia solicitado no existe."
_SERVICIO_NO_ENCONTRADO = "El servicio solicitado no existe."
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
def list_membership_plans(db: Session = Depends(get_db)) -> list[MembershipPlanRead]:
    """Catalogo no sensible: publico, sin autenticacion (ver docstring del modulo)."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    return [MembershipPlanRead.model_validate(plan) for plan in plan_repository.list_all()]


@plans_router.patch(
    "/{plan_id}",
    response_model=MembershipPlanRead,
    dependencies=[Depends(require_role("admin"))],
)
def update_membership_plan(
    plan_id: int, payload: MembershipPlanUpdate, db: Session = Depends(get_db)
) -> MembershipPlanRead:
    """Editar nombre/precio/duracion/descripcion/beneficios. Solo `admin`.

    No toca `is_active` -- eso solo cambia via `DELETE` (desactivar si
    tiene contrataciones). Un cambio de precio aqui aplica unicamente a
    contrataciones NUEVAS (ver `price_at_purchase` en
    `MembershipService`); las ya existentes no se tocan."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)

    existing = plan_repository.get_by_id(plan_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PLAN_NO_ENCONTRADO)

    existing.name = payload.name
    existing.price = payload.price
    existing.duration_days = payload.duration_days
    existing.description = payload.description
    existing.benefits = payload.benefits
    updated = plan_repository.update(existing)

    db.commit()
    return MembershipPlanRead.model_validate(updated)


@plans_router.delete(
    "/{plan_id}",
    response_model=MembershipPlanRead,
    dependencies=[Depends(require_role("admin"))],
)
def delete_or_deactivate_membership_plan(plan_id: int, db: Session = Depends(get_db)) -> MembershipPlanRead:
    """Solo `admin`. Desactiva el plan si tiene membresias contratadas;
    lo elimina de verdad si no tiene ninguna -- ver
    `DeleteOrDeactivateMembershipPlanUseCase`. Devuelve 200 (no 204) con
    el estado resultante para que el frontend sepa cual de las dos paso."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    membership_repository = SqlAlchemyMembershipRepository(db)
    use_case = DeleteOrDeactivateMembershipPlanUseCase(
        plan_repository=plan_repository, membership_repository=membership_repository
    )

    try:
        result = use_case.execute(plan_id)
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    db.commit()
    return MembershipPlanRead.model_validate(result)


# --- Servicios incluidos en un plan (plan_services) -------------------------


@plans_router.get("/{plan_id}/services", response_model=list[ServiceRead])
def list_plan_services(
    plan_id: int,
    current_user: User = Depends(get_current_user),  # noqa: ARG001 -- requiere sesion, cualquier rol
    db: Session = Depends(get_db),
) -> list[ServiceRead]:
    """Que servicios incluye este plan. Requiere sesion (cualquier rol)."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    service_repository = SqlAlchemyServiceRepository(db)
    plan_service_repository = SqlAlchemyPlanServiceRepository(db)

    if plan_repository.get_by_id(plan_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_PLAN_NO_ENCONTRADO)

    included = plan_service_repository.list_for_plan(plan_id)
    services = [service_repository.get_by_id(ps.service_id) for ps in included]
    return [ServiceRead.model_validate(s) for s in services if s is not None]


@plans_router.post(
    "/{plan_id}/services",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def add_service_to_plan(
    plan_id: int, payload: PlanServiceAdd, db: Session = Depends(get_db)
) -> ServiceRead:
    """Marca un servicio como incluido en este plan. Solo `admin`."""
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    service_repository = SqlAlchemyServiceRepository(db)
    plan_service_repository = SqlAlchemyPlanServiceRepository(db)
    use_case = AddServiceToPlanUseCase(
        plan_repository=plan_repository,
        service_repository=service_repository,
        plan_service_repository=plan_service_repository,
    )

    try:
        use_case.execute(plan_id, payload.service_id)
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ServiceAlreadyIncludedInPlanError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    db.commit()
    service = service_repository.get_by_id(payload.service_id)
    return ServiceRead.model_validate(service)


@plans_router.delete(
    "/{plan_id}/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin"))],
)
def remove_service_from_plan(plan_id: int, service_id: int, db: Session = Depends(get_db)) -> None:
    """Quita un servicio de los incluidos del plan (sigue existiendo en el
    catalogo). Solo `admin`."""
    plan_service_repository = SqlAlchemyPlanServiceRepository(db)
    if not plan_service_repository.exists(plan_id, service_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ese servicio no esta incluido en este plan.",
        )
    plan_service_repository.remove(plan_id, service_id)
    db.commit()


# --- Services CRUD (catalogo) ------------------------------------------------


@services_router.post(
    "",
    response_model=ServiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_service(payload: ServiceCreate, db: Session = Depends(get_db)) -> ServiceRead:
    """RF005 (Fase 2): alta de un servicio extra del catalogo. Solo `admin`."""
    service_repository = SqlAlchemyServiceRepository(db)
    created = service_repository.add(
        Service(
            id=None,
            name=payload.name,
            price=payload.price,
            billing_period=payload.billing_period,
            description=payload.description,
        )
    )
    db.commit()
    return ServiceRead.model_validate(created)


@services_router.get("", response_model=list[ServiceRead])
def list_services(db: Session = Depends(get_db)) -> list[ServiceRead]:
    """Catalogo no sensible: publico, sin autenticacion (mismo criterio
    que `GET /membership-plans`)."""
    service_repository = SqlAlchemyServiceRepository(db)
    return [ServiceRead.model_validate(s) for s in service_repository.list_all()]


@services_router.patch(
    "/{service_id}",
    response_model=ServiceRead,
    dependencies=[Depends(require_role("admin"))],
)
def update_service(service_id: int, payload: ServiceUpdate, db: Session = Depends(get_db)) -> ServiceRead:
    """Editar un servicio del catalogo. Solo `admin`. No toca `is_active`
    -- mismo criterio que `update_membership_plan`."""
    service_repository = SqlAlchemyServiceRepository(db)

    existing = service_repository.get_by_id(service_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_SERVICIO_NO_ENCONTRADO)

    existing.name = payload.name
    existing.price = payload.price
    existing.billing_period = payload.billing_period
    existing.description = payload.description
    updated = service_repository.update(existing)

    db.commit()
    return ServiceRead.model_validate(updated)


@services_router.delete(
    "/{service_id}",
    response_model=ServiceRead,
    dependencies=[Depends(require_role("admin"))],
)
def delete_or_deactivate_service(service_id: int, db: Session = Depends(get_db)) -> ServiceRead:
    """Solo `admin`. Desactiva el servicio si tiene contrataciones
    (`MembershipService`); lo elimina de verdad si no tiene ninguna."""
    service_repository = SqlAlchemyServiceRepository(db)
    use_case = DeleteOrDeactivateServiceUseCase(service_repository=service_repository)

    try:
        result = use_case.execute(service_id)
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    db.commit()
    return ServiceRead.model_validate(result)


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


_VENTANA_TABLERO_DIAS = 7


@router.get("/board", response_model=ActiveMembershipsBoard, dependencies=[Depends(require_role("admin", "entrenador"))])
def get_active_memberships_board(
    plan_id: int | None = None,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActiveMembershipsBoard:
    """Tablero de membresias ACTIVAS -- ver docstring del modulo arriba.
    Las vencidas no aparecen aqui (se consultan en `GET /memberships/
    expiring` o en la ficha del cliente)."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    user_repository = SqlAlchemyUserRepository(db)
    membership_service_repository = SqlAlchemyMembershipServiceRepository(db)
    service_repository = SqlAlchemyServiceRepository(db)
    payment_repository = SqlAlchemyPaymentRepository(db)

    memberships = _resolve_memberships_for_user(current_user, membership_repository, client_repository, None)
    active = [m for m in memberships if m.status == "activa"]

    today = date.today()
    all_rows: list[ActiveMembershipRow] = []
    for m in active:
        profile = client_repository.get_by_id(m.client_id)
        owner = user_repository.get_by_id(profile.user_id) if profile is not None else None
        plan = plan_repository.get_by_id(m.plan_id)
        extras = [
            service.name
            for ms in membership_service_repository.list_by_membership(m.id)  # type: ignore[arg-type]
            if ms.status == "activa"
            for service in [service_repository.get_by_id(ms.service_id)]
            if service is not None
        ]
        days_remaining = (m.end_date - today).days
        all_rows.append(
            ActiveMembershipRow(
                membership_id=m.id,  # type: ignore[arg-type]
                client_id=m.client_id,
                client_name=owner.full_name if owner else "Cliente no disponible",
                plan_id=m.plan_id,
                plan_name=plan.name if plan else "Plan no disponible",
                active_extras=extras,
                start_date=m.start_date,
                end_date=m.end_date,
                days_remaining=days_remaining,
                expiring_soon=0 <= days_remaining <= _VENTANA_TABLERO_DIAS,
            )
        )

    monthly_revenue: Decimal | None = None
    if current_user.role == "admin":
        month_prefix = today.strftime("%Y-%m")
        total = Decimal("0")
        for profile in client_repository.list_all():
            for membership in membership_repository.list_by_client(profile.id):  # type: ignore[arg-type]
                for payment in payment_repository.list_by_membership(membership.id):  # type: ignore[arg-type]
                    if payment.payment_date.strftime("%Y-%m") == month_prefix:
                        total += payment.amount
        monthly_revenue = total

    indicators = ActiveMembershipsIndicators(
        total_active=len(all_rows),
        expiring_soon=sum(1 for r in all_rows if r.expiring_soon),
        monthly_revenue=monthly_revenue,
    )

    items = all_rows
    if plan_id is not None:
        items = [r for r in items if r.plan_id == plan_id]
    if q and q.strip():
        needle = q.strip().lower()
        items = [r for r in items if needle in r.client_name.lower()]

    return ActiveMembershipsBoard(indicators=indicators, items=items)


# IMPORTANTE: estas rutas estaticas ("/board", "/expiring" y
# "/detect-expiring") deben declararse ANTES que "/{membership_id}" --
# FastAPI/Starlette resuelve las rutas en el orden en que se registran, y
# calzarian con el patron "/{membership_id}" (fallando la validacion de
# tipo `int`) si quedaran despues.
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


@router.post(
    "/{membership_id}/renew",
    response_model=MembershipRead,
    dependencies=[Depends(require_role("admin"))],
)
def renew_membership(membership_id: int, db: Session = Depends(get_db)) -> MembershipRead:
    """Accion "Renovar" del tablero de membresias activas. Solo `admin` --
    ver `RenewMembershipUseCase` y el docstring del modulo arriba."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    plan_repository = SqlAlchemyMembershipPlanRepository(db)
    use_case = RenewMembershipUseCase(
        membership_repository=membership_repository, plan_repository=plan_repository
    )

    try:
        renewed = use_case.execute(membership_id)
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    db.commit()
    return MembershipRead.model_validate(renewed)


def _build_plan_change_preview(
    impact: PlanChangeImpact, service_repository: SqlAlchemyServiceRepository
) -> PlanChangePreview:
    """Traduce `PlanChangeImpact` (ids/entidades de dominio) a la
    respuesta HTTP (con nombres de servicio resueltos) -- usado por los
    dos endpoints de cambio de plan, que comparten el mismo calculo."""

    def _extra_row(extra) -> PlanChangeExtraRow:  # noqa: ANN001
        service = service_repository.get_by_id(extra.service_id)
        return PlanChangeExtraRow(
            membership_service_id=extra.id,  # type: ignore[arg-type]
            service_id=extra.service_id,
            service_name=service.name if service else f"Servicio #{extra.service_id}",
            price_at_purchase=extra.price_at_purchase,
        )

    def _contractable_row(service_id: int) -> PlanChangeContractableRow:
        service = service_repository.get_by_id(service_id)
        return PlanChangeContractableRow(
            service_id=service_id,
            service_name=service.name if service else f"Servicio #{service_id}",
            price=service.price if service else Decimal("0"),
        )

    return PlanChangePreview(
        membership_id=impact.membership_id,
        client_id=impact.client_id,
        old_plan_id=impact.old_plan_id,
        old_plan_name=impact.old_plan_name,
        old_plan_price=impact.old_plan_price,
        new_plan_id=impact.new_plan_id,
        new_plan_name=impact.new_plan_name,
        new_plan_price=impact.new_plan_price,
        price_difference=impact.price_difference,
        cancelled_extras=[_extra_row(e) for e in impact.cancelled_extras],
        cancelled_extras_total=impact.cancelled_extras_total,
        kept_extras=[_extra_row(e) for e in impact.kept_extras],
        newly_contractable_services=[
            _contractable_row(sid) for sid in impact.newly_contractable_service_ids
        ],
    )


@router.post(
    "/{membership_id}/change-plan/preview",
    response_model=PlanChangePreview,
    dependencies=[Depends(require_role("admin"))],
)
def preview_change_membership_plan(
    membership_id: int, payload: PlanChangeRequest, db: Session = Depends(get_db)
) -> PlanChangePreview:
    """Previsualiza el efecto de cambiar el plan SIN guardar nada -- mismo
    calculo que la confirmacion, ver docstring del modulo arriba y de
    `PreviewChangeMembershipPlanUseCase`. Solo `admin`."""
    use_case = PreviewChangeMembershipPlanUseCase(
        membership_repository=SqlAlchemyMembershipRepository(db),
        plan_repository=SqlAlchemyMembershipPlanRepository(db),
        plan_service_repository=SqlAlchemyPlanServiceRepository(db),
        membership_service_repository=SqlAlchemyMembershipServiceRepository(db),
    )

    try:
        impact = use_case.execute(membership_id, payload.new_plan_id)
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SamePlanChangeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InactiveMembershipPlanError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _build_plan_change_preview(impact, SqlAlchemyServiceRepository(db))


@router.post(
    "/{membership_id}/change-plan",
    response_model=PlanChangePreview,
    dependencies=[Depends(require_role("admin"))],
)
def change_membership_plan(
    membership_id: int,
    payload: PlanChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PlanChangePreview:
    """Confirma el cambio de plan -- reusa el mismo calculo que el preview
    y lo persiste en una sola transaccion (ver `ChangeMembershipPlanUseCase`).
    Solo `admin`."""
    preview_use_case = PreviewChangeMembershipPlanUseCase(
        membership_repository=SqlAlchemyMembershipRepository(db),
        plan_repository=SqlAlchemyMembershipPlanRepository(db),
        plan_service_repository=SqlAlchemyPlanServiceRepository(db),
        membership_service_repository=SqlAlchemyMembershipServiceRepository(db),
    )
    use_case = ChangeMembershipPlanUseCase(
        preview_use_case=preview_use_case,
        membership_repository=SqlAlchemyMembershipRepository(db),
        membership_service_repository=SqlAlchemyMembershipServiceRepository(db),
        client_repository=SqlAlchemyClientProfileRepository(db),
        audit_log_repository=SqlAlchemyAuditLogRepository(db),
        notify_use_case=NotifyUserUseCase(notification_repository=SqlAlchemyNotificationRepository(db)),
    )

    try:
        impact = use_case.execute(
            membership_id, payload.new_plan_id, current_user.id, payload.notes  # type: ignore[arg-type]
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SamePlanChangeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InactiveMembershipPlanError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    db.commit()
    return _build_plan_change_preview(impact, SqlAlchemyServiceRepository(db))


# --- Servicios extra contratados sobre una membresia -------------------------


@router.post(
    "/{membership_id}/services",
    response_model=MembershipServiceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def contract_membership_service(
    membership_id: int, payload: MembershipServiceCreate, db: Session = Depends(get_db)
) -> MembershipServiceRead:
    """RF005 (Fase 2): contratar un servicio extra sobre la membresia de un
    cliente. Solo `admin` -- ver docstring del modulo arriba."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    service_repository = SqlAlchemyServiceRepository(db)
    plan_service_repository = SqlAlchemyPlanServiceRepository(db)
    membership_service_repository = SqlAlchemyMembershipServiceRepository(db)
    use_case = ContractMembershipServiceUseCase(
        membership_repository=membership_repository,
        service_repository=service_repository,
        plan_service_repository=plan_service_repository,
        membership_service_repository=membership_service_repository,
    )

    try:
        created = use_case.execute(
            membership_id=membership_id,
            service_id=payload.service_id,
            start_date_value=payload.start_date or date.today(),
            end_date_value=payload.end_date,
        )
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InactiveServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ServiceIncludedInPlanError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    db.commit()
    return MembershipServiceRead.model_validate(created)


@router.get("/{membership_id}/services")
def list_membership_services(
    membership_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MembershipServiceRead] | list[MembershipServiceReadLimited]:
    """Ownership por dato (mismo patron que `GET /memberships/{id}`) +
    recorte de columnas por rol -- ver docstring del modulo arriba:
    `entrenador` ve la lista sin `price_at_purchase`."""
    membership_repository = SqlAlchemyMembershipRepository(db)
    client_repository = SqlAlchemyClientProfileRepository(db)
    membership_service_repository = SqlAlchemyMembershipServiceRepository(db)

    membership = membership_repository.get_by_id(membership_id)
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_MEMBRESIA_NO_ENCONTRADA)

    profile = client_repository.get_by_id(membership.client_id)
    if profile is not None:
        _ensure_access_to_membership(current_user, profile)

    contracted = membership_service_repository.list_by_membership(membership_id)

    if current_user.role == "entrenador":
        # Solo extras VIGENTES -- un extra cancelado (manualmente o por un
        # cambio de plan, ver `ChangeMembershipPlanUseCase`) deja de
        # aparecerle (regla explicita del encargo). `admin`/`cliente` ven
        # el historial completo mas abajo -- "se conserva" es para los
        # datos, no para ocultarlo de quien necesita auditarlo.
        active_only = [ms for ms in contracted if ms.status == "activa"]
        return [MembershipServiceReadLimited.model_validate(ms) for ms in active_only]
    return [MembershipServiceRead.model_validate(ms) for ms in contracted]
