"""Casos de uso del modulo Memberships (RF004) y Vencimientos/Notificaciones
(RF006).

Entrega 2: `AssignMembershipUseCase` (RF004) y `DetectExpiringMembershipsUseCase`
(RF006, modulo "Vencimientos/Notificaciones" -- ver DECISIONES.md, orden
fijo de modulos, va DESPUES de Pagos) tienen logica real.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from src.application.notifications.use_cases import NotifyUserUseCase
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.memberships.entities import (
    ESTADOS_MEMBRESIA_VALIDOS,
    Membership,
    MembershipPlan,
    MembershipService,
    PlanService,
    Service,
)
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
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
    MembershipServiceRepository,
    PlanServiceRepository,
    ServiceRepository,
)
from src.domain.notifications.entities import AuditLog, Notification
from src.domain.notifications.repositories import AuditLogRepository


@dataclass
class AssignMembershipUseCase:
    """RF004: asignar un plan de membresia a un cliente.

    Valida, en este orden:
    1. que `client_id` exista (`ClientProfileRepository.get_by_id`) --
       `ClientNotFoundError` (reusada de `domain.clients.exceptions`, ver
       nota en `domain/memberships/exceptions.py`).
    2. que `plan_id` exista (`MembershipPlanRepository.get_by_id`) --
       `MembershipPlanNotFoundError`.
    3. que `status` sea uno de `ESTADOS_MEMBRESIA_VALIDOS` --
       `InvalidMembershipStatusError`.
    4. que `end_date` sea estrictamente posterior a `start_date` --
       `InvalidMembershipDateRangeError`.

    Depende de `ClientProfileRepository` ademas de los dos repositorios de
    Memberships ya declarados en el esqueleto original -- mismo patron de
    orquestar varios repositorios de dominio desde un caso de uso de
    aplicacion que ya usa `RegisterClientUseCase` (modulo Clientes).
    """

    membership_repository: MembershipRepository
    plan_repository: MembershipPlanRepository
    client_repository: ClientProfileRepository

    def execute(self, membership: Membership) -> Membership:
        if self.client_repository.get_by_id(membership.client_id) is None:
            raise ClientNotFoundError(membership.client_id)

        if self.plan_repository.get_by_id(membership.plan_id) is None:
            raise MembershipPlanNotFoundError(membership.plan_id)

        if membership.status not in ESTADOS_MEMBRESIA_VALIDOS:
            raise InvalidMembershipStatusError(membership.status)

        if membership.end_date <= membership.start_date:
            raise InvalidMembershipDateRangeError()

        return self.membership_repository.add(membership)


@dataclass
class DetectExpiringMembershipsUseCase:
    """RF006: detectar membresias vencidas o proximas a vencer.

    Modulo "Vencimientos/Notificaciones" (ver DECISIONES.md). No existe
    infraestructura de cron/scheduler en este proyecto (stack escolar, sin
    job runner): en produccion esto correria como un job diario; aqui se
    expone como una accion que el admin dispara manualmente via
    `POST /memberships/detect-expiring`.

    Dos casos, cada uno con una semantica de persistencia distinta (ver
    tambien `frontend/src/utils/membership.ts`, que ya documenta que "por
    vencer" NUNCA se persiste como status):

    1. Membresias `status == "activa"` con `end_date` ya pasada (antes de
       hoy) -> TRANSICION REAL: pasan a `status = "vencida"`
       (`membership_repository.update`) y generan una `Notification` tipo
       `membresia_vencida` para el usuario dueno (resuelto
       `Membership.client_id` -> `ClientProfile.user_id`). Como la
       consulta subyacente filtra sobre `status == "activa"`, una
       membresia que ya paso a "vencida" no vuelve a aparecer en corridas
       futuras -- esta notificacion es naturalmente idempotente (una sola
       vez por membresia), sin necesitar deduplicacion extra.
    2. Membresias `status == "activa"` con `end_date` dentro de la ventana
       `days_ahead` (todavia no vencida) -> NO cambia el status (sigue
       "activa"; "por vencer" se sigue calculando al vuelo, nunca se
       persiste), pero SI genera una `Notification` tipo
       `membresia_por_vencer`. Este caso SI necesita deduplicacion manual
       porque la membresia sigue "activa" y volveria a aparecer en cada
       corrida: antes de notificar, se revisa (`NotificationRepository.
       list_by_user`) si ya existe una notificacion no leida de tipo
       `membresia_por_vencer` para ese usuario, creada dentro de la misma
       ventana de `days_ahead` dias -- si ya existe, no se duplica. Esta
       deduplicacion es heuristica (por tipo + usuario + ventana de
       tiempo, no por un vinculo directo a la membresia, porque
       `Notification` no tiene `membership_id` en su esquema actual) y es
       una limitacion conocida, aceptable para el alcance de esta entrega
       (dos membresias distintas por vencer del mismo usuario en la misma
       ventana solo generarian una notificacion combinada).

    Devuelve la lista combinada de membresias afectadas (vencidas +
    por vencer), para que el endpoint que dispara esto informe el
    resultado.
    """

    membership_repository: MembershipRepository
    client_repository: ClientProfileRepository
    notify_use_case: NotifyUserUseCase

    def execute(self, days_ahead: int = 7) -> list[Membership]:
        today = date.today()
        cutoff = today + timedelta(days=days_ahead)

        # Una sola consulta cubre ambos casos (vencidas y por vencer): todo
        # lo que tenga `end_date <= cutoff`. Se separan por fecha dentro del
        # propio caso de uso en vez de pedir dos consultas al repositorio.
        candidates = self.membership_repository.list_expiring_before(cutoff)
        affected: list[Membership] = []

        for membership in candidates:
            if membership.status != "activa":
                continue

            owner_user_id = self._resolve_owner_user_id(membership)

            if membership.end_date < today:
                # Caso 1: transicion real.
                membership.status = "vencida"
                updated = self.membership_repository.update(membership)
                if owner_user_id is not None:
                    self.notify_use_case.execute(
                        Notification(
                            id=None,
                            user_id=owner_user_id,
                            type="membresia_vencida",
                            title="Membresia vencida",
                            message=f"Tu membresia vencio el {updated.end_date.isoformat()}.",
                        )
                    )
                affected.append(updated)
            else:
                # Caso 2: por vencer, dentro de la ventana -- status sin cambio.
                if owner_user_id is None:
                    continue
                if self._has_recent_expiring_notification(owner_user_id, days_ahead):
                    continue
                days_left = (membership.end_date - today).days
                self.notify_use_case.execute(
                    Notification(
                        id=None,
                        user_id=owner_user_id,
                        type="membresia_por_vencer",
                        title="Membresia por vencer",
                        message=(
                            f"Tu membresia vence el {membership.end_date.isoformat()}, "
                            f"faltan {days_left} dias."
                        ),
                    )
                )
                affected.append(membership)

        return affected

    def _resolve_owner_user_id(self, membership: Membership) -> int | None:
        """Resuelve `Membership.client_id` -> `ClientProfile.user_id`. Si el
        perfil no existe (dato huerfano), se omite solo la notificacion --
        la membresia igual se procesa y se reporta en el resultado."""
        profile = self.client_repository.get_by_id(membership.client_id)
        return profile.user_id if profile is not None else None

    def _has_recent_expiring_notification(self, user_id: int, days_ahead: int) -> bool:
        """Deduplicacion heuristica del caso 2 -- ver docstring de la clase."""
        window_start = datetime.now(timezone.utc) - timedelta(days=days_ahead)
        notifications = self.notify_use_case.notification_repository.list_by_user(user_id)
        return any(
            n.type == "membresia_por_vencer"
            and not n.is_read
            and n.created_at is not None
            and n.created_at >= window_start
            for n in notifications
        )


# --- Entrega 3, Fase 2: Planes y servicios extra (amplia RF004/RF005) ------


@dataclass
class RenewMembershipUseCase:
    """Renovar una membresia desde el tablero de membresias activas
    (Entrega 3, ajuste de UX de la pantalla "Membresias").

    Extiende `end_date` por la duracion del PROPIO plan
    (`MembershipPlan.duration_days`), a partir de la fecha de fin vigente
    si todavia no paso, o de hoy si ya vencio -- nunca deja huecos sin
    cobertura ni acumula sobre una fecha ya pasada. Si la membresia
    estaba `"vencida"`, vuelve a `"activa"`.

    Decision explicita (ver DECISIONES.md): NO crea una `Membership`
    nueva ni un `Payment` automatico -- "renovar" (extender vigencia) y
    "cobrar" (registrar el pago) son dos acciones separadas en la UI a
    proposito, para no asumir metodo de pago ni monto cobrado.
    """

    membership_repository: MembershipRepository
    plan_repository: MembershipPlanRepository

    def execute(self, membership_id: int) -> Membership:
        membership = self.membership_repository.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id)

        plan = self.plan_repository.get_by_id(membership.plan_id)
        if plan is None:
            raise MembershipPlanNotFoundError(membership.plan_id)

        today = date.today()
        base_date = membership.end_date if membership.end_date >= today else today
        membership.end_date = base_date + timedelta(days=plan.duration_days)
        membership.status = "activa"
        return self.membership_repository.update(membership)


@dataclass
class DeleteOrDeactivateMembershipPlanUseCase:
    """Regla de negocio explicita del encargo: "Eliminar un plan ... con
    contrataciones lo DESACTIVA; si no tiene ninguna, se elimina de
    verdad." -- un `DELETE` nunca es simplemente "borrar la fila", decide
    entre dos acciones segun si existen `Membership` sobre ese plan.
    """

    plan_repository: MembershipPlanRepository
    membership_repository: MembershipRepository

    def execute(self, plan_id: int) -> MembershipPlan:
        plan = self.plan_repository.get_by_id(plan_id)
        if plan is None:
            raise MembershipPlanNotFoundError(plan_id)

        if self.membership_repository.has_memberships_for_plan(plan_id):
            plan.is_active = False
            return self.plan_repository.update(plan)

        self.plan_repository.delete(plan_id)
        return plan


@dataclass
class DeleteOrDeactivateServiceUseCase:
    """Mismo criterio que `DeleteOrDeactivateMembershipPlanUseCase`, mirado
    desde `Service`: "contrataciones" son filas de `MembershipService`
    (clientes que ya lo contrataron), no las filas de `plan_services`
    (que servicios incluye un plan) -- un servicio puede quitarse de un
    plan sin que eso cuente como "contratacion"."""

    service_repository: ServiceRepository

    def execute(self, service_id: int) -> Service:
        service = self.service_repository.get_by_id(service_id)
        if service is None:
            raise ServiceNotFoundError(service_id)

        if self.service_repository.has_contracts(service_id):
            service.is_active = False
            return self.service_repository.update(service)

        self.service_repository.delete(service_id)
        return service


@dataclass
class AddServiceToPlanUseCase:
    """Marca que un `Service` esta incluido en un `MembershipPlan` (lo que
    un cliente con ese plan ya no paga aparte)."""

    plan_repository: MembershipPlanRepository
    service_repository: ServiceRepository
    plan_service_repository: PlanServiceRepository

    def execute(self, plan_id: int, service_id: int):
        if self.plan_repository.get_by_id(plan_id) is None:
            raise MembershipPlanNotFoundError(plan_id)
        if self.service_repository.get_by_id(service_id) is None:
            raise ServiceNotFoundError(service_id)
        if self.plan_service_repository.exists(plan_id, service_id):
            raise ServiceAlreadyIncludedInPlanError(plan_id, service_id)

        return self.plan_service_repository.add(PlanService(plan_id=plan_id, service_id=service_id))


# Duracion por defecto de un servicio contratado segun su periodo de
# facturacion, cuando la peticion no manda `end_date` explicito.
_DIAS_POR_DEFECTO_SERVICIO_MENSUAL = 30


@dataclass
class ContractMembershipServiceUseCase:
    """RF005 (Fase 2): un cliente contrata un servicio extra, NO incluido
    en su plan, sobre una membresia concreta.

    Valida, en este orden:
    1. que `membership_id` exista -- `MembershipNotFoundError`.
    2. que `service_id` exista -- `ServiceNotFoundError`.
    3. que el servicio siga activo (`is_active`) -- `InactiveServiceError`:
       un servicio desactivado (sin contrataciones nuevas) no deberia
       poder contratarse de nuevo.
    4. que el servicio NO este ya incluido en el plan de esa membresia --
       `ServiceIncludedInPlanError` (regla explicita: "un servicio
       incluido en el plan del cliente no se cobra aparte").

    `price_at_purchase` se congela del `Service.price` ACTUAL al momento
    de la contratacion (regla explicita: "un cambio de precio de plan o
    servicio aplica solo a contrataciones nuevas; lo ya contratado
    conserva price_at_purchase") -- un cambio de precio del catalogo
    despues de esta llamada nunca toca esta fila.

    `end_date`, si no se especifica, se calcula segun `billing_period`:
    'unico' -> igual a `start_date` (sin vigencia que renovar); 'mensual'
    -> `start_date` + 30 dias; 'periodo' -> el `end_date` de la propia
    membresia (vigente mientras dure el periodo de la membresia que lo
    contrato). Documentado como interpretacion razonable en DECISIONES.md
    -- el encargo no especifica la duracion exacta de cada periodo.
    """

    membership_repository: MembershipRepository
    service_repository: ServiceRepository
    plan_service_repository: PlanServiceRepository
    membership_service_repository: MembershipServiceRepository

    def execute(
        self,
        membership_id: int,
        service_id: int,
        start_date_value: date,
        end_date_value: date | None = None,
    ) -> MembershipService:
        membership = self.membership_repository.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id)

        service = self.service_repository.get_by_id(service_id)
        if service is None:
            raise ServiceNotFoundError(service_id)

        if not service.is_active:
            raise InactiveServiceError(service_id)

        if self.plan_service_repository.exists(membership.plan_id, service_id):
            raise ServiceIncludedInPlanError(membership.plan_id, service_id)

        if end_date_value is not None:
            resolved_end_date = end_date_value
        elif service.billing_period == "unico":
            resolved_end_date = start_date_value
        elif service.billing_period == "mensual":
            resolved_end_date = start_date_value + timedelta(days=_DIAS_POR_DEFECTO_SERVICIO_MENSUAL)
        else:  # 'periodo'
            resolved_end_date = membership.end_date

        return self.membership_service_repository.add(
            MembershipService(
                id=None,
                membership_id=membership_id,
                service_id=service_id,
                price_at_purchase=service.price,
                start_date=start_date_value,
                end_date=resolved_end_date,
                status="activa",
            )
        )


# --- Cambio de plan (amplia RF004/RF005 de nuevo) ---------------------------


@dataclass
class PlanChangeImpact:
    """Resultado del calculo de un cambio de plan -- objeto de aplicacion
    (no una entidad de dominio persistida), compartido EXACTAMENTE por
    `PreviewChangeMembershipPlanUseCase` (no persiste nada) y
    `ChangeMembershipPlanUseCase` (persiste esto mismo), para que la
    pantalla de resumen y el resultado final de la confirmacion sean
    siempre el mismo calculo, nunca dos logicas separadas que puedan
    desincronizarse."""

    membership_id: int
    client_id: int
    old_plan_id: int
    old_plan_name: str
    old_plan_price: Decimal
    new_plan_id: int
    new_plan_name: str
    new_plan_price: Decimal
    price_difference: Decimal
    # Extras ACTIVOS que el plan nuevo ya incluye -- se cancelan.
    cancelled_extras: list[MembershipService] = field(default_factory=list)
    cancelled_extras_total: Decimal = Decimal("0")
    # Extras ACTIVOS que el plan nuevo NO incluye -- se conservan tal cual.
    kept_extras: list[MembershipService] = field(default_factory=list)
    # Servicios que el plan VIEJO incluia y el NUEVO no (bajada de plan) --
    # pasan a poder contratarse como extra; esta lista es solo informativa,
    # el caso de uso NUNCA crea una fila `MembershipService` para ellos.
    newly_contractable_service_ids: list[int] = field(default_factory=list)


@dataclass
class PreviewChangeMembershipPlanUseCase:
    """Calcula el efecto de cambiar el plan de una membresia SIN escribir
    nada en la base -- de solo lectura a proposito, para que la pantalla
    de resumen (antes de confirmar) pueda llamarse las veces que haga
    falta sin ningun efecto secundario.

    Regla de negocio (ver DECISIONES.md, entrada "Cambio de plan: efecto
    en servicios extra"):
    1. Compara los servicios incluidos en el plan NUEVO (`PlanService`)
       contra los extras ACTIVOS de la membresia (`MembershipService`).
    2. Todo extra activo que el plan nuevo YA INCLUYE se marca para
       cancelar (`cancelled_extras`) -- un servicio incluido en el plan
       nunca se cobra aparte (mismo criterio que
       `ContractMembershipServiceUseCase`/`ServiceIncludedInPlanError`).
    3. Los extras que el plan nuevo NO incluye se conservan tal cual
       (`kept_extras`).
    4. Los servicios que el plan VIEJO incluia y el nuevo no (bajada de
       plan) se reportan como "ahora contratables"
       (`newly_contractable_service_ids`) -- NUNCA se agregan solos ni se
       cobran sin que el admin los contrate explicitamente despues, como
       cualquier otro extra.
    """

    membership_repository: MembershipRepository
    plan_repository: MembershipPlanRepository
    plan_service_repository: PlanServiceRepository
    membership_service_repository: MembershipServiceRepository

    def execute(self, membership_id: int, new_plan_id: int) -> PlanChangeImpact:
        membership = self.membership_repository.get_by_id(membership_id)
        if membership is None:
            raise MembershipNotFoundError(membership_id)

        if membership.plan_id == new_plan_id:
            raise SamePlanChangeError(new_plan_id)

        old_plan = self.plan_repository.get_by_id(membership.plan_id)
        if old_plan is None:
            raise MembershipPlanNotFoundError(membership.plan_id)

        new_plan = self.plan_repository.get_by_id(new_plan_id)
        if new_plan is None:
            raise MembershipPlanNotFoundError(new_plan_id)

        if not new_plan.is_active:
            raise InactiveMembershipPlanError(new_plan_id)

        old_plan_service_ids = {
            ps.service_id for ps in self.plan_service_repository.list_for_plan(membership.plan_id)
        }
        new_plan_service_ids = {
            ps.service_id for ps in self.plan_service_repository.list_for_plan(new_plan_id)
        }

        active_extras = [
            ms
            for ms in self.membership_service_repository.list_by_membership(membership_id)
            if ms.status == "activa"
        ]
        cancelled_extras = [ms for ms in active_extras if ms.service_id in new_plan_service_ids]
        kept_extras = [ms for ms in active_extras if ms.service_id not in new_plan_service_ids]
        newly_contractable_ids = sorted(old_plan_service_ids - new_plan_service_ids)

        cancelled_total = sum(
            (ms.price_at_purchase for ms in cancelled_extras), start=Decimal("0")
        )

        return PlanChangeImpact(
            membership_id=membership_id,
            client_id=membership.client_id,
            old_plan_id=old_plan.id,  # type: ignore[arg-type]
            old_plan_name=old_plan.name,
            old_plan_price=old_plan.price,
            new_plan_id=new_plan.id,  # type: ignore[arg-type]
            new_plan_name=new_plan.name,
            new_plan_price=new_plan.price,
            price_difference=new_plan.price - old_plan.price,
            cancelled_extras=cancelled_extras,
            cancelled_extras_total=cancelled_total,
            kept_extras=kept_extras,
            newly_contractable_service_ids=newly_contractable_ids,
        )


@dataclass
class ChangeMembershipPlanUseCase:
    """Ejecuta el cambio de plan calculado por
    `PreviewChangeMembershipPlanUseCase` (reusa el MISMO calculo, nunca una
    logica separada) y lo persiste:

    1. Actualiza `Membership.plan_id`.
    2. Cada extra en `impact.cancelled_extras` pasa a
       `status = "cancelado_por_cambio_de_plan"`, `end_date = hoy` -- NO se
       borra, NO se toca `price_at_purchase` (el historial y los pagos ya
       hechos se conservan intactos, regla explicita del encargo).
    3. Los extras en `impact.kept_extras` NO se tocan.
    4. Los servicios de `impact.newly_contractable_service_ids` NO generan
       ninguna fila nueva -- quedan disponibles para contratarse despues
       como cualquier otro extra, nunca automaticamente.
    5. Deja una entrada en la bitacora (`AuditLog`) y notifica al cliente
       (`Notification`, tipo `plan_cambiado`).

    Atomico por construccion: todas las escrituras (`update`/`add` de los
    repositorios) comparten la MISMA `Session` inyectada desde el router;
    el router hace un unico `db.commit()` despues de que `execute()`
    retorna sin excepcion. Si cualquier paso de aqui levanta una
    excepcion, el router nunca llega a comitear -- nada de lo escrito con
    `flush()` queda persistido (mismo patron de atomicidad "por sesion
    compartida" que ya usa el resto de la API, ver `get_db`).

    Reembolso o saldo a favor del extra cancelado: decision pendiente de
    validar con el cliente real (ver DECISIONES.md) -- por default NO se
    calcula ningun prorrateo ni reembolso automatico; `notes` (opcional)
    es donde el admin deja registrado el acuerdo comercial, y
    `cancelled_extras_total` del resultado ya le dice cuanto habia pagado
    de cada extra cancelado para que decida con esa cifra en mano.
    """

    preview_use_case: PreviewChangeMembershipPlanUseCase
    membership_repository: MembershipRepository
    membership_service_repository: MembershipServiceRepository
    client_repository: ClientProfileRepository
    audit_log_repository: AuditLogRepository
    notify_use_case: NotifyUserUseCase

    def execute(
        self,
        membership_id: int,
        new_plan_id: int,
        changed_by_user_id: int,
        notes: str | None = None,
    ) -> PlanChangeImpact:
        impact = self.preview_use_case.execute(membership_id, new_plan_id)

        membership = self.membership_repository.get_by_id(membership_id)
        assert membership is not None  # ya lo valido preview_use_case arriba
        membership.plan_id = new_plan_id
        self.membership_repository.update(membership)

        today = date.today()
        for extra in impact.cancelled_extras:
            extra.status = "cancelado_por_cambio_de_plan"
            extra.end_date = today
            self.membership_service_repository.update(extra)

        self.audit_log_repository.add(
            AuditLog(
                id=None,
                user_id=changed_by_user_id,
                action="cambio_de_plan",
                entity_type="membership",
                entity_id=str(membership_id),
                details=(
                    f"Plan '{impact.old_plan_name}' (#{impact.old_plan_id}) -> "
                    f"'{impact.new_plan_name}' (#{impact.new_plan_id}). "
                    f"Extras cancelados por inclusion en el plan nuevo: "
                    f"{[extra.id for extra in impact.cancelled_extras]} "
                    f"(total ya pagado: ${impact.cancelled_extras_total}). "
                    f"Notas del admin: {notes or '(sin notas)'}"
                ),
            )
        )

        profile = self.client_repository.get_by_id(membership.client_id)
        if profile is not None:
            self.notify_use_case.execute(
                Notification(
                    id=None,
                    user_id=profile.user_id,
                    type="plan_cambiado",
                    title="Tu plan cambió",
                    message=(
                        f"Tu membresía pasó del plan {impact.old_plan_name} "
                        f"al plan {impact.new_plan_name}."
                    ),
                )
            )

        return impact
