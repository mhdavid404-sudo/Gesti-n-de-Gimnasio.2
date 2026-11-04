"""planes y servicios extra (Entrega 3, amplia RF004/RF005)

Ver DECISIONES.md, entrada "Arranque de Entrega 3: Fase 2 (Planes y
servicios extra)". Migracion aditiva -- no toca ninguna de las 14
entidades existentes salvo agregar `is_active` a `membership_plans`
(necesario para la regla "eliminar un plan con contrataciones lo
desactiva en vez de borrarlo", antes `membership_plans` no tenia ningun
concepto de activo/inactivo).

Tablas nuevas:
- `services`: catalogo de servicios extra (rutinas personalizadas,
  casillero, clases grupales, etc.), mismo patron que `membership_plans`.
- `plan_services`: tabla puente N:M, que servicios incluye cada plan.
  Clave primaria compuesta (plan_id, service_id) -- no necesita su propio
  `id`, es una relacion pura sin atributos propios.
- `membership_services`: un servicio extra CONTRATADO por un cliente
  sobre una membresia concreta, con `price_at_purchase` (el precio del
  servicio al momento de la contratacion, para que un cambio de precio
  futuro del catalogo no afecte lo ya contratado).
- `payment_items`: desglose de un pago (plan vs. servicio individual).

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # membership_plans.is_active: antes no existia ningun concepto de
    # activo/inactivo -- se agrega para la regla de "desactivar en vez de
    # eliminar si tiene contrataciones". Default true: los planes
    # existentes (Basica/VIP/Premium) siguen activos sin cambio visible.
    op.add_column(
        "membership_plans",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    # ------------------------------------------------------------------
    # services
    # ------------------------------------------------------------------
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("billing_period", sa.String(20), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "billing_period IN ('unico', 'mensual', 'periodo')",
            name="ck_services_billing_period",
        ),
    )

    # ------------------------------------------------------------------
    # plan_services (tabla puente, sin id propio -- relacion pura)
    # ------------------------------------------------------------------
    op.create_table(
        "plan_services",
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("membership_plans.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "service_id",
            sa.Integer(),
            sa.ForeignKey("services.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ------------------------------------------------------------------
    # membership_services (servicio extra contratado por un cliente)
    # ------------------------------------------------------------------
    op.create_table(
        "membership_services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "membership_id",
            sa.Integer(),
            sa.ForeignKey("memberships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "service_id",
            sa.Integer(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Precio al momento de la contratacion -- un cambio de precio
        # posterior del catalogo NO afecta esta fila (ver docstring del
        # modulo en application/memberships/use_cases.py).
        sa.Column("price_at_purchase", sa.Numeric(10, 2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('activa', 'vencida', 'cancelada')",
            name="ck_membership_services_status",
        ),
    )
    op.create_index(
        "ix_membership_services_membership_id", "membership_services", ["membership_id"]
    )
    op.create_index(
        "ix_membership_services_service_id", "membership_services", ["service_id"]
    )

    # ------------------------------------------------------------------
    # payment_items (desglose de un pago: plan vs. servicio individual)
    # ------------------------------------------------------------------
    op.create_table(
        "payment_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        # Nullable: un item de concepto 'plan' no referencia ningun
        # service_id (el plan no es un Service, es un MembershipPlan).
        sa.Column(
            "service_id",
            sa.Integer(),
            sa.ForeignKey("services.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "concept IN ('plan', 'servicio')",
            name="ck_payment_items_concept",
        ),
    )
    op.create_index("ix_payment_items_payment_id", "payment_items", ["payment_id"])


def downgrade() -> None:
    op.drop_table("payment_items")
    op.drop_index("ix_membership_services_service_id", table_name="membership_services")
    op.drop_index("ix_membership_services_membership_id", table_name="membership_services")
    op.drop_table("membership_services")
    op.drop_table("plan_services")
    op.drop_table("services")
    op.drop_column("membership_plans", "is_active")
