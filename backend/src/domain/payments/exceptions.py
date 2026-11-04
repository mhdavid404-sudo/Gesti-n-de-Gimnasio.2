"""Excepciones de dominio del modulo Payments (RF005).

Mismo patron que `domain/clients/exceptions.py` y
`domain/memberships/exceptions.py`: el dominio no conoce HTTP ni FastAPI.
`application/payments/use_cases.py` lanza estas excepciones; la traduccion a
`HTTPException`/codigo de estado ocurre unicamente en
`api/v1/routers/payments.py`.

La falta de existencia de la MEMBRESIA (`membership_id`) se senaliza
reusando `domain.memberships.exceptions.MembershipNotFoundError` -- no se
duplica aqui un segundo tipo de excepcion para el mismo caso real
(membresia inexistente), mismo criterio que ya aplico
`application/memberships/use_cases.py` al reusar
`domain.clients.exceptions.ClientNotFoundError`.
"""

from __future__ import annotations


class InvalidPaymentMethodError(Exception):
    """`method` no esta en `METODOS_PAGO_VALIDOS`."""

    def __init__(self, method: str) -> None:
        self.method = method
        super().__init__(f"El metodo de pago '{method}' no es valido")


class InvalidPaymentStatusError(Exception):
    """`status` no esta en `ESTADOS_PAGO_VALIDOS`."""

    def __init__(self, status_value: str) -> None:
        self.status_value = status_value
        super().__init__(f"El estado de pago '{status_value}' no es valido")


class InvalidPaymentItemConceptError(Exception):
    """`concept` no esta en `CONCEPTOS_PAYMENT_ITEM_VALIDOS` (Entrega 3)."""

    def __init__(self, concept: str) -> None:
        self.concept = concept
        super().__init__(f"El concepto de pago '{concept}' no es valido")


class PaymentItemsAmountMismatchError(Exception):
    """Entrega 3: si se manda un desglose (`items`), la suma de sus montos
    debe coincidir exactamente con `Payment.amount` -- de lo contrario el
    desglose miente sobre lo realmente cobrado."""

    def __init__(self, expected: object, actual: object) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"La suma del desglose ({actual}) no coincide con el monto total del pago ({expected})"
        )
