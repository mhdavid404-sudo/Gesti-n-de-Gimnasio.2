"""Puerto (interfaz) del repositorio de Payments.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.payments.entities import Payment, PaymentItem


class PaymentRepository(ABC):
    @abstractmethod
    def get_by_id(self, payment_id: int) -> Payment | None: ...

    @abstractmethod
    def list_by_membership(self, membership_id: int) -> list[Payment]: ...

    @abstractmethod
    def add(self, payment: Payment) -> Payment: ...

    @abstractmethod
    def update(self, payment: Payment) -> Payment: ...

    @abstractmethod
    def delete(self, payment_id: int) -> None: ...


class PaymentItemRepository(ABC):
    """Entrega 3, Fase 2: desglose de un pago por concepto (plan vs.
    servicios extra)."""

    @abstractmethod
    def list_by_payment(self, payment_id: int) -> list[PaymentItem]: ...

    @abstractmethod
    def add(self, item: PaymentItem) -> PaymentItem: ...
