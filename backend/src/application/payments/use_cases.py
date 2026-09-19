"""Casos de uso del modulo Payments. Entrega 1: solo el esqueleto."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.memberships.repositories import MembershipRepository
from src.domain.payments.entities import Payment
from src.domain.payments.repositories import PaymentRepository


@dataclass
class RegisterPaymentUseCase:
    """RF005: registrar un pago asociado a una membresia."""

    payment_repository: PaymentRepository
    membership_repository: MembershipRepository

    def execute(self, payment: Payment) -> Payment:
        raise NotImplementedError("Entrega 2: logica pendiente")


@dataclass
class ListPaymentsByMembershipUseCase:
    """RF005: consultar historial de pagos de una membresia."""

    payment_repository: PaymentRepository

    def execute(self, membership_id: int) -> list[Payment]:
        raise NotImplementedError("Entrega 2: logica pendiente")
