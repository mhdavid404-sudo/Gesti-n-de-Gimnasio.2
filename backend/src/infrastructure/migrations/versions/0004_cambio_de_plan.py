"""cambio de plan y su efecto en servicios extra (amplia RF004/RF005)

Ver DECISIONES.md, entrada "Cambio de plan: efecto en servicios extra".
Migracion que SOLO amplia dos `CHECK` existentes (ningun cambio
estructural de tablas/columnas):

- `membership_services.status` admite ahora el valor
  'cancelado_por_cambio_de_plan' -- distinto de 'cancelada' (cancelacion
  manual) para que el propio status deje trazabilidad de POR QUE se
  cancelo un extra, sin tener que leer la bitacora.
- `notifications.type` admite ahora 'plan_cambiado', para la notificacion
  que recibe el cliente cuando un admin le cambia el plan.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-04

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_MEMBERSHIP_SERVICE_STATUSES = "status IN ('activa', 'vencida', 'cancelada')"
_NEW_MEMBERSHIP_SERVICE_STATUSES = (
    "status IN ('activa', 'vencida', 'cancelada', 'cancelado_por_cambio_de_plan')"
)

_OLD_NOTIFICATION_TYPES = (
    "type IN ('membresia_vencida', 'membresia_por_vencer', "
    "'pago_registrado', 'rutina_asignada', 'dieta_asignada', 'sistema')"
)
_NEW_NOTIFICATION_TYPES = (
    "type IN ('membresia_vencida', 'membresia_por_vencer', "
    "'pago_registrado', 'rutina_asignada', 'dieta_asignada', 'sistema', "
    "'plan_cambiado')"
)


def upgrade() -> None:
    op.drop_constraint("ck_membership_services_status", "membership_services", type_="check")
    # "cancelado_por_cambio_de_plan" (29 caracteres) no entra en el
    # VARCHAR(20) original -- se ensancha antes de permitir el valor nuevo
    # en el CHECK, si no el primer UPDATE con ese status truena con
    # StringDataRightTruncation.
    op.alter_column(
        "membership_services", "status", type_=sa.String(40), existing_type=sa.String(20)
    )
    op.create_check_constraint(
        "ck_membership_services_status", "membership_services", _NEW_MEMBERSHIP_SERVICE_STATUSES
    )

    op.drop_constraint("ck_notifications_type", "notifications", type_="check")
    op.create_check_constraint("ck_notifications_type", "notifications", _NEW_NOTIFICATION_TYPES)


def downgrade() -> None:
    op.drop_constraint("ck_notifications_type", "notifications", type_="check")
    op.create_check_constraint("ck_notifications_type", "notifications", _OLD_NOTIFICATION_TYPES)

    op.drop_constraint("ck_membership_services_status", "membership_services", type_="check")
    op.alter_column(
        "membership_services", "status", type_=sa.String(20), existing_type=sa.String(40)
    )
    op.create_check_constraint(
        "ck_membership_services_status", "membership_services", _OLD_MEMBERSHIP_SERVICE_STATUSES
    )
