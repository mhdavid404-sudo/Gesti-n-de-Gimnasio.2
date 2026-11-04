"""Casos de uso del modulo Payments (RF005)."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.memberships.exceptions import MembershipNotFoundError
from src.domain.memberships.repositories import MembershipRepository
from src.domain.payments.entities import (
    CONCEPTOS_PAYMENT_ITEM_VALIDOS,
    ESTADOS_PAGO_VALIDOS,
    METODOS_PAGO_VALIDOS,
    Payment,
    PaymentItem,
)
from src.domain.payments.exceptions import (
    InvalidPaymentItemConceptError,
    InvalidPaymentMethodError,
    InvalidPaymentStatusError,
    PaymentItemsAmountMismatchError,
)
from src.domain.payments.repositories import PaymentItemRepository, PaymentRepository


@dataclass
class RegisterPaymentUseCase:
    """RF005: registrar un pago asociado a una membresia.

    Valida, en este orden:
    1. que `membership_id` exista (`MembershipRepository.get_by_id`) --
       `MembershipNotFoundError` (reusada de `domain.memberships.exceptions`,
       ver nota en `domain/payments/exceptions.py`).
    2. que `method` sea uno de `METODOS_PAGO_VALIDOS` --
       `InvalidPaymentMethodError`.
    3. que `status` sea uno de `ESTADOS_PAGO_VALIDOS` --
       `InvalidPaymentStatusError`.

    Pydantic ya tipa `method`/`status` como `Literal` en la capa de
    transporte, pero el dominio no confia ciegamente en esa capa -- mismo
    criterio que ya aplico `AssignMembershipUseCase` con
    `ESTADOS_MEMBRESIA_VALIDOS`.
    """

    payment_repository: PaymentRepository
    membership_repository: MembershipRepository
    # Entrega 3 (Fase 2): opcional a proposito -- `None` para no romper el
    # modulo Pagos de Entrega 2 (un pago sin desglose sigue siendo valido,
    # ej. un pago en efectivo registrado sin detalle de conceptos).
    payment_item_repository: PaymentItemRepository | None = None

    def execute(self, payment: Payment, items: list[PaymentItem] | None = None) -> Payment:
        if self.membership_repository.get_by_id(payment.membership_id) is None:
            raise MembershipNotFoundError(payment.membership_id)

        if payment.method not in METODOS_PAGO_VALIDOS:
            raise InvalidPaymentMethodError(payment.method)

        if payment.status not in ESTADOS_PAGO_VALIDOS:
            raise InvalidPaymentStatusError(payment.status)

        if items:
            for item in items:
                if item.concept not in CONCEPTOS_PAYMENT_ITEM_VALIDOS:
                    raise InvalidPaymentItemConceptError(item.concept)
            total = sum((item.amount for item in items), start=type(payment.amount)(0))
            if total != payment.amount:
                raise PaymentItemsAmountMismatchError(payment.amount, total)

        created = self.payment_repository.add(payment)

        if items and self.payment_item_repository is not None:
            for item in items:
                self.payment_item_repository.add(
                    PaymentItem(
                        id=None,
                        payment_id=created.id,  # type: ignore[arg-type]
                        concept=item.concept,
                        amount=item.amount,
                        service_id=item.service_id,
                    )
                )

        return created


@dataclass
class ListPaymentsByMembershipUseCase:
    """RF005: consultar historial de pagos de una membresia."""

    payment_repository: PaymentRepository

    def execute(self, membership_id: int) -> list[Payment]:
        return self.payment_repository.list_by_membership(membership_id)
