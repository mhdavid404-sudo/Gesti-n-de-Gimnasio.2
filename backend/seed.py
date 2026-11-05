"""Seed de datos de prueba -- SmartGym v2 (Entrega 3).

Antes de esta entrega las cuentas/datos de demostracion se creaban a mano
via API en cada sesion de trabajo (curl + `POST /clients`, etc.) -- se
perdian cada vez que corria la suite completa de pytest (`conftest.py`
trunca `users`/`client_profiles`/... entre pruebas, y una corrida completa
contra la misma base de desarrollo arrastra con las cuentas demo). Este
script reemplaza ese proceso manual: un usuario por rol (admin/entrenador/
cliente), fechas realistas de 2026, y un recorrido completo por los 9
modulos para que la demo de la entrega no empiece con el sistema vacio.

Uso:
    docker compose exec backend python seed.py

Es DESTRUCTIVO e idempotente a proposito -- trunca las mismas tablas que
`tests/conftest.py` (mismo criterio de aislamiento) antes de insertar, asi
que se puede correr las veces que haga falta sin acumular duplicados ni
chocar con un `UNIQUE` (email, nombre de plan, nombre de ejercicio). NO
correr contra una base con datos reales de produccion.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev",
)

from sqlalchemy import text  # noqa: E402

from src.domain.clients.entities import ClientProfile  # noqa: E402
from src.domain.diets.entities import DietAssignment, DietPlan  # noqa: E402
from src.domain.memberships.entities import (  # noqa: E402
    Membership,
    MembershipPlan,
    MembershipService,
    PlanService,
    Service,
)
from src.domain.notifications.entities import Notification  # noqa: E402
from src.domain.payments.entities import Payment  # noqa: E402
from src.domain.progress.entities import BodyProgress  # noqa: E402
from src.domain.routines.entities import Exercise, Routine, RoutineAssignment, RoutineExercise  # noqa: E402
from src.domain.users.entities import User  # noqa: E402
from src.infrastructure.db.session import SessionLocal, engine  # noqa: E402
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository  # noqa: E402
from src.infrastructure.repositories.diets import (  # noqa: E402
    SqlAlchemyDietAssignmentRepository,
    SqlAlchemyDietPlanRepository,
)
from src.infrastructure.repositories.memberships import (  # noqa: E402
    SqlAlchemyMembershipPlanRepository,
    SqlAlchemyMembershipRepository,
    SqlAlchemyMembershipServiceRepository,
    SqlAlchemyPlanServiceRepository,
    SqlAlchemyServiceRepository,
)
from src.infrastructure.repositories.notifications import SqlAlchemyNotificationRepository  # noqa: E402
from src.infrastructure.repositories.payments import SqlAlchemyPaymentRepository  # noqa: E402
from src.infrastructure.repositories.progress import SqlAlchemyBodyProgressRepository  # noqa: E402
from src.infrastructure.repositories.routines import (  # noqa: E402
    SqlAlchemyExerciseRepository,
    SqlAlchemyRoutineAssignmentRepository,
    SqlAlchemyRoutineRepository,
)
from src.infrastructure.repositories.users import SqlAlchemyUserRepository  # noqa: E402
from src.infrastructure.security.password import hash_password  # noqa: E402

DEMO_PASSWORD = "Demo2026!"
TODAY = date.today()


def _truncate_all(session) -> None:
    # Mismas tablas que `tests/conftest.py` (mismo criterio de aislamiento,
    # ver docstring ahi de por que cada una esta o no esta en la lista) mas
    # las que ese archivo documenta como innecesarias por CASCADE --
    # listadas aqui explicitas de todas formas, para que este script no
    # dependa de memorizar la cadena de FKs.
    session.execute(
        text(
            "TRUNCATE TABLE users, client_profiles, membership_plans, memberships, "
            "payments, payment_items, services, plan_services, membership_services, "
            "exercises, routines, routine_exercises, routine_assignments, "
            "diet_plans, diet_assignments, body_progress, notifications, audit_logs "
            "RESTART IDENTITY CASCADE"
        )
    )
    session.commit()


def run() -> None:
    session = SessionLocal()
    try:
        print("Vaciando tablas de datos de prueba...")
        _truncate_all(session)

        user_repo = SqlAlchemyUserRepository(session)
        client_repo = SqlAlchemyClientProfileRepository(session)
        plan_repo = SqlAlchemyMembershipPlanRepository(session)
        membership_repo = SqlAlchemyMembershipRepository(session)
        payment_repo = SqlAlchemyPaymentRepository(session)
        exercise_repo = SqlAlchemyExerciseRepository(session)
        routine_repo = SqlAlchemyRoutineRepository(session)
        routine_assignment_repo = SqlAlchemyRoutineAssignmentRepository(session)
        diet_plan_repo = SqlAlchemyDietPlanRepository(session)
        diet_assignment_repo = SqlAlchemyDietAssignmentRepository(session)
        progress_repo = SqlAlchemyBodyProgressRepository(session)
        notification_repo = SqlAlchemyNotificationRepository(session)
        service_repo = SqlAlchemyServiceRepository(session)
        plan_service_repo = SqlAlchemyPlanServiceRepository(session)
        membership_service_repo = SqlAlchemyMembershipServiceRepository(session)

        # --- Un usuario por rol -------------------------------------------
        print("Creando cuentas demo (una por rol)...")
        admin = user_repo.add(
            User(
                id=None,
                email="admin@demo.com",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Admin Demo",
                role="admin",
                is_active=True,
            )
        )
        entrenador = user_repo.add(
            User(
                id=None,
                email="entrenador@demo.com",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Entrenador Demo",
                role="entrenador",
                is_active=True,
            )
        )
        cliente_user = user_repo.add(
            User(
                id=None,
                email="cliente@demo.com",
                password_hash=hash_password(DEMO_PASSWORD),
                full_name="Cliente Demo",
                role="cliente",
                is_active=True,
            )
        )
        session.commit()

        cliente_profile = client_repo.add(
            ClientProfile(
                id=None,
                user_id=cliente_user.id,  # type: ignore[arg-type]
                trainer_id=entrenador.id,
                phone="5512345678",
                birth_date=date(1995, 5, 20),
                address="Calle Falsa 123, Aragón, CDMX",
                emergency_contact="María Demo - 55 0000 0001",
            )
        )
        session.commit()

        # --- Planes de membresía -------------------------------------------
        print("Creando catálogo de planes...")
        plan_basica = plan_repo.add(
            MembershipPlan(
                id=None,
                name="Básica",
                price=Decimal("399.00"),
                duration_days=30,
                description="Acceso a área de pesas y cardio en horario regular.",
                benefits=["Acceso a área de pesas", "Acceso a cardio", "Casillero compartido"],
            )
        )
        plan_vip = plan_repo.add(
            MembershipPlan(
                id=None,
                name="VIP",
                price=Decimal("649.00"),
                duration_days=30,
                description="Acceso completo más 2 clases grupales por semana.",
                benefits=[
                    "Acceso a área de pesas",
                    "Acceso a cardio",
                    "2 clases grupales por semana",
                    "Casillero individual",
                ],
            )
        )
        plan_premium = plan_repo.add(
            MembershipPlan(
                id=None,
                name="Premium",
                price=Decimal("999.00"),
                duration_days=30,
                description="Acceso ilimitado, clases grupales y asesoría con entrenador.",
                benefits=[
                    "Acceso a área de pesas",
                    "Acceso a cardio",
                    "Clases grupales ilimitadas",
                    "Asesoría con entrenador",
                    "Casillero individual",
                ],
            )
        )
        session.commit()

        # --- Catálogo de servicios extra (Entrega 3, Fase 2) ---------------
        # Precios de ejemplo, marcados como dato de prueba en el propio
        # nombre/README -- no son tarifario real del gimnasio.
        print("Creando catálogo de servicios extra (dato de prueba)...")
        servicio_rutina = service_repo.add(
            Service(
                id=None,
                name="Rutinas personalizadas",
                price=Decimal("250.00"),
                billing_period="mensual",
                description="Rutina diseñada y ajustada por un entrenador (precio de prueba).",
            )
        )
        servicio_casillero = service_repo.add(
            Service(
                id=None,
                name="Casillero individual",
                price=Decimal("120.00"),
                billing_period="mensual",
                description="Casillero con llave asignado de forma individual (precio de prueba).",
            )
        )
        servicio_clases = service_repo.add(
            Service(
                id=None,
                name="Clases grupales",
                price=Decimal("180.00"),
                billing_period="mensual",
                description="Acceso a clases grupales (spinning, funcional, etc.) (precio de prueba).",
            )
        )
        servicio_dieta = service_repo.add(
            Service(
                id=None,
                name="Plan de dieta personalizado",
                price=Decimal("300.00"),
                billing_period="unico",
                description="Plan de alimentación diseñado por un entrenador (precio de prueba).",
            )
        )
        servicio_entrenador = service_repo.add(
            Service(
                id=None,
                name="Entrenador asignado",
                price=Decimal("450.00"),
                billing_period="mensual",
                description="Seguimiento personal de un entrenador durante el mes (precio de prueba).",
            )
        )
        servicio_evaluacion = service_repo.add(
            Service(
                id=None,
                name="Evaluación de progreso quincenal",
                price=Decimal("150.00"),
                billing_period="periodo",
                description="Medición y evaluación corporal cada quince días (precio de prueba).",
            )
        )
        session.commit()

        # --- Inclusión de servicios por plan -------------------------------
        # Básica: solo el casillero. VIP: suma clases grupales + evaluación.
        # Premium: todos los servicios incluidos (justifica su precio más alto).
        print("Asignando servicios incluidos por plan...")
        for service_id in (servicio_casillero.id,):
            plan_service_repo.add(PlanService(plan_id=plan_basica.id, service_id=service_id))  # type: ignore[arg-type]
        for service_id in (servicio_casillero.id, servicio_clases.id, servicio_evaluacion.id):
            plan_service_repo.add(PlanService(plan_id=plan_vip.id, service_id=service_id))  # type: ignore[arg-type]
        for service_id in (
            servicio_rutina.id,
            servicio_casillero.id,
            servicio_clases.id,
            servicio_dieta.id,
            servicio_entrenador.id,
            servicio_evaluacion.id,
        ):
            plan_service_repo.add(PlanService(plan_id=plan_premium.id, service_id=service_id))  # type: ignore[arg-type]
        session.commit()

        # --- Membresía del cliente demo: vence en 4 días (demuestra RF006) -
        print("Asignando membresía (por vencer, para demostrar RF006)...")
        membership_start = TODAY - timedelta(days=26)
        membership_end = TODAY + timedelta(days=4)
        membership = membership_repo.add(
            Membership(
                id=None,
                client_id=cliente_profile.id,  # type: ignore[arg-type]
                plan_id=plan_basica.id,  # type: ignore[arg-type]
                start_date=membership_start,
                end_date=membership_end,
                status="activa",
            )
        )
        session.commit()

        payment_repo.add(
            Payment(
                id=None,
                membership_id=membership.id,  # type: ignore[arg-type]
                amount=plan_basica.price,
                payment_date=datetime.combine(membership_start, datetime.min.time(), tzinfo=timezone.utc),
                method="tarjeta",
                status="completado",
                registered_by=admin.id,  # type: ignore[arg-type]
                notes="Pago de alta, plan Básica.",
            )
        )
        session.commit()

        notification_repo.add(
            Notification(
                id=None,
                user_id=cliente_user.id,  # type: ignore[arg-type]
                type="pago_registrado",
                title="Pago registrado",
                message=f"Se registró tu pago del plan {plan_basica.name} por ${plan_basica.price}.",
            )
        )
        session.commit()

        # --- Extra contratado por el cliente demo (no incluido en su plan) -
        # Básica solo incluye casillero -- el cliente contrata "Entrenador
        # asignado" por su cuenta, para que la ficha tenga un ejemplo real
        # de "Extras contratados" con price_at_purchase propio.
        print("Contratando un servicio extra para el cliente demo...")
        membership_service_repo.add(
            MembershipService(
                id=None,
                membership_id=membership.id,  # type: ignore[arg-type]
                service_id=servicio_entrenador.id,  # type: ignore[arg-type]
                price_at_purchase=servicio_entrenador.price,
                start_date=membership_start,
                end_date=membership_start + timedelta(days=30),
                status="activa",
            )
        )
        session.commit()

        # --- Progreso corporal: 2 registros en 2026, con evolución --------
        print("Registrando progreso corporal...")
        progress_repo.add(
            BodyProgress(
                id=None,
                client_id=cliente_profile.id,  # type: ignore[arg-type]
                record_date=TODAY - timedelta(days=20),
                weight_kg=Decimal("78.5"),
                height_cm=Decimal("175.0"),
                notes="Primera medición.",
            )
        )
        progress_repo.add(
            BodyProgress(
                id=None,
                client_id=cliente_profile.id,  # type: ignore[arg-type]
                record_date=TODAY,
                weight_kg=Decimal("77.2"),
                height_cm=Decimal("175.0"),
                waist_cm=Decimal("81.0"),
                notes="Segunda medición, a la quincena.",
            )
        )
        session.commit()

        # --- Rutina asignada -------------------------------------------------
        print("Creando y asignando una rutina...")
        exercise = exercise_repo.add(
            Exercise(
                id=None,
                name="Sentadilla con barra",
                muscle_group="Piernas",
                description="Técnica, profundidad por debajo de la paralela.",
                equipment="Barra olímpica",
            )
        )
        routine = routine_repo.add(
            Routine(
                id=None,
                name="Fuerza - Tren inferior",
                created_by=entrenador.id,  # type: ignore[arg-type]
                description="3 días por semana, enfoque en fuerza máxima.",
            )
        )
        routine_repo.add_exercise(
            RoutineExercise(
                id=None,
                routine_id=routine.id,  # type: ignore[arg-type]
                exercise_id=exercise.id,  # type: ignore[arg-type]
                sets=4,
                reps=6,
                order_index=0,
                rest_seconds=120,
            ),
        )
        routine_assignment_repo.add(
            RoutineAssignment(
                id=None,
                routine_id=routine.id,  # type: ignore[arg-type]
                client_id=cliente_profile.id,  # type: ignore[arg-type]
                assigned_by=entrenador.id,  # type: ignore[arg-type]
                assigned_date=TODAY - timedelta(days=20),
                status="activa",
            )
        )
        session.commit()

        # --- Dieta asignada ----------------------------------------------
        print("Creando y asignando un plan de dieta...")
        diet_plan = diet_plan_repo.add(
            DietPlan(
                id=None,
                name="Déficit calórico moderado",
                created_by=entrenador.id,  # type: ignore[arg-type]
                description="4 comidas al día, alta en proteína.",
                calories_target=2100,
            )
        )
        diet_assignment_repo.add(
            DietAssignment(
                id=None,
                diet_plan_id=diet_plan.id,  # type: ignore[arg-type]
                client_id=cliente_profile.id,  # type: ignore[arg-type]
                assigned_by=entrenador.id,  # type: ignore[arg-type]
                assigned_date=TODAY - timedelta(days=20),
                status="activa",
            )
        )
        session.commit()

        print("\nListo. Cuentas demo (todas con password:", DEMO_PASSWORD, "):")
        print("  admin@demo.com       (admin)")
        print("  entrenador@demo.com  (entrenador)")
        print("  cliente@demo.com     (cliente, membresía Básica por vencer en 4 días)")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
    engine.dispose()
