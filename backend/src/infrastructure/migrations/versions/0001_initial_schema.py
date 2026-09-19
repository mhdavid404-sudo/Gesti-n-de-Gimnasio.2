"""esquema inicial: 14 tablas del modelo aprobado en DECISIONES.md

Escrita a mano (no autogenerada) porque no hay una base de datos viva en
este entorno de desarrollo -- ver COORDINACION-ENTREGA1.md, seccion
"Verificacion antes de terminar". Refleja 1:1 los modelos SQLAlchemy en
`infrastructure/db/models/` y la tabla de `backend/MODELO-DATOS.md`.

Regla dura aplicada en toda esta migracion (DECISIONES.md, correccion #1):
`role`/`status`/`method`/`type` son VARCHAR + CHECK constraint. NUNCA
ENUM nativo de PostgreSQL.

Revision ID: 0001
Revises:
Create Date: 2026-09-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "role IN ('admin', 'entrenador', 'cliente')", name="ck_users_role"
        ),
    )

    # ------------------------------------------------------------------
    # client_profiles
    # ------------------------------------------------------------------
    op.create_table(
        "client_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "trainer_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("address", sa.String(255), nullable=True),
        # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): campo unico de texto
        # libre, igual que `address` -- no separado en nombre/telefono.
        sa.Column("emergency_contact", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_client_profiles_trainer_id", "client_profiles", ["trainer_id"]
    )

    # ------------------------------------------------------------------
    # membership_plans
    # ------------------------------------------------------------------
    op.create_table(
        "membership_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ------------------------------------------------------------------
    # memberships
    # ------------------------------------------------------------------
    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "client_id",
            sa.Integer(),
            sa.ForeignKey("client_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.Integer(),
            sa.ForeignKey("membership_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
            "status IN ('activa', 'vencida', 'cancelada', 'pendiente')",
            name="ck_memberships_status",
        ),
    )
    op.create_index("ix_memberships_client_id", "memberships", ["client_id"])
    op.create_index("ix_memberships_end_date", "memberships", ["end_date"])

    # ------------------------------------------------------------------
    # payments
    # ------------------------------------------------------------------
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "membership_id",
            sa.Integer(),
            sa.ForeignKey("memberships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("payment_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): `payments` era la
        # unica tabla de movimiento de dinero sin FK de "quien lo hizo"
        # (inconsistente con `assigned_by` en routine/diet assignments).
        sa.Column(
            "registered_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "method IN ('efectivo', 'tarjeta', 'transferencia')",
            name="ck_payments_method",
        ),
        sa.CheckConstraint(
            "status IN ('completado', 'pendiente', 'rechazado')",
            name="ck_payments_status",
        ),
    )
    op.create_index("ix_payments_membership_id", "payments", ["membership_id"])
    op.create_index("ix_payments_registered_by", "payments", ["registered_by"])

    # ------------------------------------------------------------------
    # exercises (catalogo reutilizable)
    # ------------------------------------------------------------------
    op.create_table(
        "exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False, unique=True),
        sa.Column("muscle_group", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ------------------------------------------------------------------
    # routines
    # ------------------------------------------------------------------
    op.create_table(
        "routines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_routines_created_by", "routines", ["created_by"])

    # ------------------------------------------------------------------
    # routine_exercises (tabla puente Routine <-> Exercise)
    # ------------------------------------------------------------------
    op.create_table(
        "routine_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "routine_id",
            sa.Integer(),
            sa.ForeignKey("routines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            sa.Integer(),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.Integer(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint(
            "routine_id", "order_index", name="uq_routine_exercises_order"
        ),
    )
    op.create_index(
        "ix_routine_exercises_routine_id", "routine_exercises", ["routine_id"]
    )
    op.create_index(
        "ix_routine_exercises_exercise_id", "routine_exercises", ["exercise_id"]
    )

    # ------------------------------------------------------------------
    # routine_assignments
    # ------------------------------------------------------------------
    op.create_table(
        "routine_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "routine_id",
            sa.Integer(),
            sa.ForeignKey("routines.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.Integer(),
            sa.ForeignKey("client_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "status IN ('activa', 'completada', 'cancelada')",
            name="ck_routine_assignments_status",
        ),
    )
    op.create_index(
        "ix_routine_assignments_client_id", "routine_assignments", ["client_id"]
    )
    op.create_index(
        "ix_routine_assignments_routine_id", "routine_assignments", ["routine_id"]
    )

    # ------------------------------------------------------------------
    # diet_plans
    # ------------------------------------------------------------------
    op.create_table(
        "diet_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("calories_target", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_diet_plans_created_by", "diet_plans", ["created_by"])

    # ------------------------------------------------------------------
    # diet_assignments
    # ------------------------------------------------------------------
    op.create_table(
        "diet_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "diet_plan_id",
            sa.Integer(),
            sa.ForeignKey("diet_plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "client_id",
            sa.Integer(),
            sa.ForeignKey("client_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assigned_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("assigned_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.CheckConstraint(
            "status IN ('activa', 'completada', 'cancelada')",
            name="ck_diet_assignments_status",
        ),
    )
    op.create_index(
        "ix_diet_assignments_client_id", "diet_assignments", ["client_id"]
    )
    op.create_index(
        "ix_diet_assignments_diet_plan_id", "diet_assignments", ["diet_plan_id"]
    )

    # ------------------------------------------------------------------
    # body_progress
    # ------------------------------------------------------------------
    op.create_table(
        "body_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "client_id",
            sa.Integer(),
            sa.ForeignKey("client_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("record_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(5, 2), nullable=False),
        # Nota (DECISIONES.md, punto menor no bloqueante): height_cm se deja
        # aqui y no en client_profiles por ahora.
        sa.Column("height_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("body_fat_pct", sa.Numeric(4, 2), nullable=True),
        sa.Column("muscle_mass_kg", sa.Numeric(5, 2), nullable=True),
        # Arbitraje de Isai, 2026-09-12 (DECISIONES.md): RF010 pide "peso,
        # medidas, fecha de registro" -- medidas individuales, todas
        # nullable, sin costo de integridad frente a muscle_mass_kg.
        sa.Column("chest_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("waist_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("hip_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("arm_cm", sa.Numeric(5, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_body_progress_client_id", "body_progress", ["client_id"])

    # ------------------------------------------------------------------
    # notifications
    # ------------------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "is_read", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "type IN ('membresia_vencida', 'membresia_por_vencer', "
            "'pago_registrado', 'rutina_asignada', 'dieta_asignada', 'sistema')",
            name="ck_notifications_type",
        ),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ------------------------------------------------------------------
    # audit_logs (RF015)
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", sa.String(50), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    # Orden inverso al de creacion, respetando dependencias de FK.
    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("body_progress")
    op.drop_table("diet_assignments")
    op.drop_table("diet_plans")
    op.drop_table("routine_assignments")
    op.drop_table("routine_exercises")
    op.drop_table("routines")
    op.drop_table("exercises")
    op.drop_table("payments")
    op.drop_table("memberships")
    op.drop_table("membership_plans")
    op.drop_table("client_profiles")
    op.drop_table("users")
