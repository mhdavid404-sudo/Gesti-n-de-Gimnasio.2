"""editar/eliminar rutinas y dietas (amplia RF007/RF009/RF012)

Ver DECISIONES.md, entrada "Edicion/eliminacion de rutinas y dietas".
Migracion aditiva, mismo patron ya usado en `0003_planes_y_servicios_extra`
para `membership_plans`/`services`: se agrega `is_active` a `routines` y
`diet_plans` -- antes ninguna de las dos tenia ningun concepto de
activo/inactivo. Necesario para la regla "eliminar una rutina/dieta con
asignaciones la DESACTIVA en vez de borrarla" (conserva el historial de
quien la tuvo asignada).

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "routines",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "diet_plans",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("diet_plans", "is_active")
    op.drop_column("routines", "is_active")
