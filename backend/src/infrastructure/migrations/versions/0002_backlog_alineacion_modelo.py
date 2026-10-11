"""resolucion del backlog de alineacion de modelo para Entrega 2

Ver DECISIONES.md, entrada "2026-09-12 -- Backlog de alineacion de modelo
para Entrega 2" (los 11 puntos encontrados por QA) y la entrada del
2026-10-10 que registra como se resolvio cada uno.

De los 11 puntos, SOLO 4 requieren cambio de esquema real (los demas eran
renombrados de solo-frontend o columnas que ya existian en el backend y
solo faltaba reflejarlas en `models.ts`):

1. `membership_plans.benefits` -- el frontend ya tenia `benefits: string[]`
   sin respaldo en el backend; tiene sentido de negocio real (texto de
   marketing del plan), se agrega como columna JSON NOT NULL con default
   `[]` en vez de forzar al frontend a borrar un campo que si se usa en
   Membresias/Landing.
2. `exercises.equipment` -- mismo caso: el frontend ya lo usaba en el
   catalogo mock, se agrega VARCHAR(100) NULLABLE (no todo ejercicio
   requiere equipo, ej. plancha abdominal).
3. `routine_assignments.notes` / `diet_assignments.notes` -- el frontend
   ya modelaba una nota opcional del entrenador al asignar rutina/dieta;
   se agregan como TEXT NULLABLE en ambas tablas.

Las otras 7 divergencias del backlog (Notification.title, order_index,
calories_target, MembershipPlan.created_at, AuditLog.entity_id,
updated_at de users/client_profiles, created_at de payments/exercises,
nulabilidad relajada, AuditLog.entity_type) ya existian correctamente en
el esquema real desde la migracion 0001 -- la divergencia estaba
unicamente en `frontend/src/types/models.ts`, que se corrige aparte sin
tocar la base de datos.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # membership_plans.benefits: lista de beneficios en texto libre
    # (ej. "Acceso a piso de pesas"), persistida como JSON -- no amerita
    # una tabla aparte (no se consulta/filtra por beneficio individual).
    op.add_column(
        "membership_plans",
        sa.Column(
            "benefits",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )

    # exercises.equipment: equipo requerido por el ejercicio del catalogo.
    # Nullable porque varios ejercicios de peso corporal no requieren nada.
    op.add_column(
        "exercises",
        sa.Column("equipment", sa.String(100), nullable=True),
    )

    # routine_assignments.notes / diet_assignments.notes: nota libre del
    # entrenador/admin al asignar (ej. "cliente nuevo, revisar tecnica
    # primero"), consistente con el `notes` que ya existe en `payments` y
    # en `body_progress`.
    op.add_column(
        "routine_assignments",
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "diet_assignments",
        sa.Column("notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("diet_assignments", "notes")
    op.drop_column("routine_assignments", "notes")
    op.drop_column("exercises", "equipment")
    op.drop_column("membership_plans", "benefits")
