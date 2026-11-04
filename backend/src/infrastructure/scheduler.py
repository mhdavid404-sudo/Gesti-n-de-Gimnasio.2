"""Job diario de deteccion de vencimientos (RF006).

Hasta Entrega 2 `DetectExpiringMembershipsUseCase` solo se disparaba a mano
(`POST /memberships/detect-expiring`, solo admin) -- documentado como
limitacion conocida porque no habia infraestructura de scheduler en el
proyecto. Entrega 3 pide un "reporte diario de vencimientos que genere
Notification"; se resuelve aqui con un job en proceso (APScheduler,
`BackgroundScheduler`) en vez de agregar un contenedor/cron nuevo al stack
-- mas simple para un proyecto escolar de un solo proceso backend, y no
rompe el endpoint manual existente (sigue sirviendo para que el admin lo
dispare bajo demanda, p. ej. justo despues de cargar datos de prueba).

Corre a las 06:00 hora del contenedor (antes de que abra el gimnasio) --
hora arbitraria razonable, sin requerimiento especifico del encargo.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from src.application.memberships.use_cases import DetectExpiringMembershipsUseCase
from src.application.notifications.use_cases import NotifyUserUseCase
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.clients import SqlAlchemyClientProfileRepository
from src.infrastructure.repositories.memberships import SqlAlchemyMembershipRepository
from src.infrastructure.repositories.notifications import SqlAlchemyNotificationRepository

logger = logging.getLogger("smartgym.scheduler")

DAILY_JOB_ID = "detect-expiring-memberships-daily"
_VENTANA_POR_VENCER_DIAS = 7


def run_daily_expiring_detection() -> None:
    """Misma logica que el endpoint manual, pero con su propia sesion de
    base de datos (no hay request/`get_db` aqui -- el job corre fuera del
    ciclo de vida de una peticion HTTP, mismo criterio que
    `api/main.py::_record_audit_event`)."""
    session = SessionLocal()
    try:
        membership_repository = SqlAlchemyMembershipRepository(session)
        client_repository = SqlAlchemyClientProfileRepository(session)
        notification_repository = SqlAlchemyNotificationRepository(session)
        notify_use_case = NotifyUserUseCase(notification_repository=notification_repository)

        use_case = DetectExpiringMembershipsUseCase(
            membership_repository=membership_repository,
            client_repository=client_repository,
            notify_use_case=notify_use_case,
        )
        affected = use_case.execute(days_ahead=_VENTANA_POR_VENCER_DIAS)
        session.commit()
        logger.info("Deteccion diaria de vencimientos: %d membresia(s) afectadas.", len(affected))
    except Exception:
        session.rollback()
        logger.exception("Fallo la deteccion diaria de vencimientos.")
    finally:
        session.close()


_scheduler: BackgroundScheduler | None = None


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    _scheduler = BackgroundScheduler(timezone="America/Mexico_City")
    _scheduler.add_job(
        run_daily_expiring_detection,
        trigger="cron",
        hour=6,
        minute=0,
        id=DAILY_JOB_ID,
        replace_existing=True,
    )
    _scheduler.start()
    return _scheduler


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
