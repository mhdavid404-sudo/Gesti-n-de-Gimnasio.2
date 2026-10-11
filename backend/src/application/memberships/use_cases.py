"""Casos de uso del modulo Memberships (RF004) y Vencimientos/Notificaciones
(RF006).

Entrega 2: `AssignMembershipUseCase` (RF004) y `DetectExpiringMembershipsUseCase`
(RF006, modulo "Vencimientos/Notificaciones" -- ver DECISIONES.md, orden
fijo de modulos, va DESPUES de Pagos) tienen logica real.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from src.application.notifications.use_cases import NotifyUserUseCase
from src.domain.clients.exceptions import ClientNotFoundError
from src.domain.clients.repositories import ClientProfileRepository
from src.domain.memberships.entities import ESTADOS_MEMBRESIA_VALIDOS, Membership
from src.domain.memberships.exceptions import (
    InvalidMembershipDateRangeError,
    InvalidMembershipStatusError,
    MembershipPlanNotFoundError,
)
from src.domain.memberships.repositories import (
    MembershipPlanRepository,
    MembershipRepository,
)
from src.domain.notifications.entities import Notification


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
