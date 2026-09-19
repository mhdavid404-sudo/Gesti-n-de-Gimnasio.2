"""Puerto (interfaz) del repositorio de Payments.

Solo entidades de dominio en las firmas (DECISIONES.md, correccion #3).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.payments.entities import Payment


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
