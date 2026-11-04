"""Implementacion concreta (SQLAlchemy) del puerto `PaymentRepository`."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.payments.entities import Payment, PaymentItem
from src.domain.payments.repositories import PaymentItemRepository, PaymentRepository
from src.infrastructure.db.models.payments import PaymentItemModel, PaymentModel


def _to_entity(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        membership_id=model.membership_id,
        amount=model.amount,
        payment_date=model.payment_date,
        method=model.method,
        status=model.status,
        registered_by=model.registered_by,
        notes=model.notes,
        created_at=model.created_at,
    )


class SqlAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, payment_id: int) -> Payment | None:
        model = self._session.get(PaymentModel, payment_id)
        return _to_entity(model) if model else None

    def list_by_membership(self, membership_id: int) -> list[Payment]:
        models = self._session.execute(
            select(PaymentModel).where(PaymentModel.membership_id == membership_id)
        ).scalars()
        return [_to_entity(m) for m in models]

    def add(self, payment: Payment) -> Payment:
        model = PaymentModel(
            membership_id=payment.membership_id,
            amount=payment.amount,
            payment_date=payment.payment_date,
            method=payment.method,
            status=payment.status,
            registered_by=payment.registered_by,
            notes=payment.notes,
        )
        self._session.add(model)
        self._session.flush()
        return _to_entity(model)

    def update(self, payment: Payment) -> Payment:
        model = self._session.get(PaymentModel, payment.id)
        if model is None:
            raise ValueError(f"Payment {payment.id} no existe")
        model.amount = payment.amount
        model.payment_date = payment.payment_date
        model.method = payment.method
        model.status = payment.status
        model.registered_by = payment.registered_by
        model.notes = payment.notes
        self._session.flush()
        return _to_entity(model)

    def delete(self, payment_id: int) -> None:
        model = self._session.get(PaymentModel, payment_id)
        if model is not None:
            self._session.delete(model)
            self._session.flush()


def _item_to_entity(model: PaymentItemModel) -> PaymentItem:
    return PaymentItem(
        id=model.id,
        payment_id=model.payment_id,
        concept=model.concept,
        amount=model.amount,
        service_id=model.service_id,
    )


class SqlAlchemyPaymentItemRepository(PaymentItemRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_by_payment(self, payment_id: int) -> list[PaymentItem]:
        models = self._session.execute(
            select(PaymentItemModel).where(PaymentItemModel.payment_id == payment_id)
        ).scalars()
        return [_item_to_entity(m) for m in models]

    def add(self, item: PaymentItem) -> PaymentItem:
        model = PaymentItemModel(
            payment_id=item.payment_id,
            concept=item.concept,
            amount=item.amount,
            service_id=item.service_id,
        )
        self._session.add(model)
        self._session.flush()
        return _item_to_entity(model)
