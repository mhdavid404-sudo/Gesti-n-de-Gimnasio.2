"""Separar contacto de emergencia en nombre/telefono

Ver DECISIONES.md, entrada "Separacion de contacto de emergencia en
nombre/telefono" -- reversion del arbitraje de 2026-09-12 (que lo habia
dejado como un solo campo de texto libre, igual que `address`). Cambio
aditivo: se agregan `emergency_contact_name`/`emergency_contact_phone`,
se migran los datos existentes partiendo `emergency_contact` por el
primer guion (" - " o "-"), y se elimina la columna vieja.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-22

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "client_profiles",
        sa.Column("emergency_contact_name", sa.String(255), nullable=True),
    )
    op.add_column(
        "client_profiles",
        sa.Column("emergency_contact_phone", sa.String(30), nullable=True),
    )

    # Mejor esfuerzo: si el texto libre tiene un "-", lo de antes es el
    # nombre y lo de despues el telefono (TRIM quita los espacios del
    # patron "Nombre - Telefono"). Si no tiene "-", todo se trata como
    # nombre (no hay forma confiable de adivinar un telefono suelto).
    op.execute(
        """
        UPDATE client_profiles
        SET emergency_contact_name = TRIM(SPLIT_PART(emergency_contact, '-', 1)),
            emergency_contact_phone = TRIM(SUBSTRING(emergency_contact FROM POSITION('-' IN emergency_contact) + 1))
        WHERE emergency_contact IS NOT NULL AND POSITION('-' IN emergency_contact) > 0
        """
    )
    op.execute(
        """
        UPDATE client_profiles
        SET emergency_contact_name = TRIM(emergency_contact)
        WHERE emergency_contact IS NOT NULL AND POSITION('-' IN emergency_contact) = 0
        """
    )

    op.drop_column("client_profiles", "emergency_contact")


def downgrade() -> None:
    op.add_column(
        "client_profiles",
        sa.Column("emergency_contact", sa.String(255), nullable=True),
    )
    op.execute(
        """
        UPDATE client_profiles
        SET emergency_contact = CASE
            WHEN emergency_contact_name IS NOT NULL AND emergency_contact_phone IS NOT NULL
                THEN emergency_contact_name || ' - ' || emergency_contact_phone
            ELSE COALESCE(emergency_contact_name, emergency_contact_phone)
        END
        """
    )
    op.drop_column("client_profiles", "emergency_contact_phone")
    op.drop_column("client_profiles", "emergency_contact_name")
