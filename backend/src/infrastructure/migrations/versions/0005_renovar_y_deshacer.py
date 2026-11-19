"""BUG-12: renovar+cobrar atomico, status 'anulado' y tabla de renovaciones

Ver DECISIONES.md, entrada BUG-12. Dos cambios:

- `payments.status` admite ahora el valor 'anulado' -- un pago de una
  renovacion deshecha no se borra (se conserva el historial), se marca
  asi y se excluye de ingresos/totales.
- Tabla nueva `membership_renewals`: historial de renovaciones (fecha y
  estado anteriores, el pago asociado, y quien/cuando la deshizo si
  aplica) -- es lo que permite deshacer la ULTIMA renovacion de una
  membresia sin perder rastro de lo que paso antes.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_PAYMENT_STATUSES = "status IN ('completado', 'pendiente', 'rechazado')"
_NEW_PAYMENT_STATUSES = "status IN ('completado', 'pendiente', 'rechazado', 'anulado')"


def upgrade() -> None:
    op.drop_constraint("ck_payments_status", "payments", type_="check")
    op.create_check_constraint("ck_payments_status", "payments", _NEW_PAYMENT_STATUSES)

    op.create_table(
        "membership_renewals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "membership_id",
            sa.Integer(),
            sa.ForeignKey("memberships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("payments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("previous_end_date", sa.Date(), nullable=False),
        sa.Column("new_end_date", sa.Date(), nullable=False),
        sa.Column("previous_status", sa.String(20), nullable=False),
        sa.Column(
            "performed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reversed_reason", sa.Text(), nullable=True),
        sa.Column(
            "reversed_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("membership_renewals")

    op.drop_constraint("ck_payments_status", "payments", type_="check")
    op.create_check_constraint("ck_payments_status", "payments", _OLD_PAYMENT_STATUSES)
