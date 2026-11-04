"""Excepciones de dominio del modulo Memberships (RF004).

Mismo patron que `domain/clients/exceptions.py`: el dominio no conoce HTTP
ni FastAPI. Estos casos de uso (`application/memberships/use_cases.py`)
lanzan estas excepciones; la traduccion a `HTTPException`/codigo de estado
ocurre unicamente en `api/v1/routers/memberships.py`.

La falta de existencia del CLIENTE (`client_id`) se senaliza reusando
`domain.clients.exceptions.ClientNotFoundError` -- no se duplica aqui un
segundo tipo de excepcion para el mismo caso real (cliente inexistente),
siguiendo el mismo criterio que ya usa `application/clients/use_cases.py`
al reusar `domain.users.exceptions.EmailAlreadyExistsError` desde un caso
de uso que orquesta mas de un modulo de dominio.
"""

from __future__ import annotations


class MembershipPlanNotFoundError(Exception):
    """No existe un `MembershipPlan` con el id solicitado."""

    def __init__(self, plan_id: int) -> None:
        self.plan_id = plan_id
        super().__init__(f"El plan de membresia {plan_id} no existe")


class MembershipNotFoundError(Exception):
    """No existe una `Membership` con el id solicitado."""

    def __init__(self, membership_id: int) -> None:
        self.membership_id = membership_id
        super().__init__(f"La membresia {membership_id} no existe")


class InvalidMembershipDateRangeError(Exception):
    """`end_date` debe ser estrictamente posterior a `start_date`."""

    def __init__(self) -> None:
        super().__init__("La fecha de fin debe ser posterior a la fecha de inicio")


class InvalidMembershipStatusError(Exception):
    """`status` no esta en `ESTADOS_MEMBRESIA_VALIDOS`."""

    def __init__(self, status_value: str) -> None:
        self.status_value = status_value
        super().__init__(f"El estado '{status_value}' no es un estado de membresia valido")


# --- Entrega 3, Fase 2 (Planes y servicios extra) --------------------------


class ServiceNotFoundError(Exception):
    """No existe un `Service` con el id solicitado."""

    def __init__(self, service_id: int) -> None:
        self.service_id = service_id
        super().__init__(f"El servicio {service_id} no existe")


class InactiveServiceError(Exception):
    """No se puede contratar un `Service` con `is_active = False`."""

    def __init__(self, service_id: int) -> None:
        self.service_id = service_id
        super().__init__(f"El servicio {service_id} ya no esta disponible")


class ServiceAlreadyIncludedInPlanError(Exception):
    """El servicio ya forma parte de los incluidos de ese plan."""

    def __init__(self, plan_id: int, service_id: int) -> None:
        self.plan_id = plan_id
        self.service_id = service_id
        super().__init__(f"El servicio {service_id} ya esta incluido en el plan {plan_id}")


class ServiceIncludedInPlanError(Exception):
    """RF: un servicio incluido en el plan del cliente no se cobra
    aparte -- no tiene sentido (ni se permite) contratarlo como extra."""

    def __init__(self, plan_id: int, service_id: int) -> None:
        self.plan_id = plan_id
        self.service_id = service_id
        super().__init__(
            f"El servicio {service_id} ya esta incluido en el plan {plan_id} del cliente, "
            "no se puede contratar como extra."
        )


class InvalidMembershipServiceStatusError(Exception):
    """`status` no esta en `ESTADOS_MEMBERSHIP_SERVICE_VALIDOS`."""

    def __init__(self, status_value: str) -> None:
        self.status_value = status_value
        super().__init__(f"El estado '{status_value}' no es un estado valido para un servicio contratado")
