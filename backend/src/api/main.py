"""Entry point de FastAPI.

Comando de arranque exacto (COORDINACION-ENTREGA1.md, seccion 3), corrido
desde el directorio `backend/`:

    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Ver `backend/README.md` para el detalle completo (por que `src.api.main`,
donde debe correrse el comando, y donde queda documentado para Royer).

Entrega 3: autenticacion JWT y logica de negocio completas en los 15 RF.
Este archivo monta el router agregado de la v1, expone un health check,
registra automaticamente en la bitacora (RF015, modulo "Bitacora
(AuditLog)") cada error HTTP (4xx/5xx) que la API devuelve -- ver
`_record_audit_event` abajo -- y arranca el job diario de deteccion de
vencimientos (RF006, ver `src/infrastructure/scheduler.py`) al levantar el
proceso. Se eligio un manejador de excepciones global en vez de que cada
router llame `RecordAuditEventUseCase` a mano: es el unico punto por el que
pasan TODOS los errores controlados (`HTTPException` de cualquier router) y
los de validacion de Pydantic (`RequestValidationError`), sin depender de
que cada desarrollador se acuerde de instrumentar su propio endpoint.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router
from src.application.notifications.use_cases import RecordAuditEventUseCase
from src.domain.notifications.entities import AuditLog
from src.infrastructure.db.session import SessionLocal
from src.infrastructure.repositories.notifications import SqlAlchemyAuditLogRepository
from src.infrastructure.scheduler import shutdown_scheduler, start_scheduler
from src.infrastructure.security.jwt import decode_access_token


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="SmartGym v2 API",
    description=(
        "API REST de SmartGym v2 (Stronger Aragon) -- RF001-RF015, "
        "autenticacion JWT y logica de negocio completas."
    ),
    version="0.3.0",
    lifespan=_lifespan,
)


def _resolve_user_id(request: Request) -> int | None:
    """Mejor esfuerzo: identifica quien hizo la peticion para la bitacora.

    Nunca lanza -- un token ausente/invalido es justo el tipo de peticion
    que SI queremos poder auditar (ej. un 401), asi que no puede bloquear
    el registro del evento.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header[7:]
    try:
        payload = decode_access_token(token)
        return int(payload["sub"])
    except Exception:
        return None


def _record_audit_event(request: Request, status_code: int, detail: str) -> None:
    """Persiste un evento en la bitacora usando una sesion propia.

    Sesion propia (no la del request, via `get_db`) a proposito: para
    cuando este handler corre, la peticion ya fallo -- su sesion puede
    estar en un estado que no se presta para un INSERT mas. Mismo criterio
    de aislamiento que ya usa `tests/conftest.py` al abrir su propia
    `SessionLocal()` fuera del ciclo de vida normal de un request.
    """
    session = SessionLocal()
    try:
        use_case = RecordAuditEventUseCase(
            audit_log_repository=SqlAlchemyAuditLogRepository(session)
        )
        use_case.execute(
            AuditLog(
                id=None,
                user_id=_resolve_user_id(request),
                action=f"{request.method} {request.url.path}",
                entity_type=request.url.path.removeprefix("/api/v1/").split("/")[0] or None,
                entity_id=None,
                details=f"HTTP {status_code}: {detail}"[:500],
            )
        )
        session.commit()
    except Exception:
        # La bitacora es un efecto secundario de auditoria, nunca debe
        # impedir que el error original (la razon real del fallo) llegue
        # al cliente -- ver re-raise del error original en cada handler.
        session.rollback()
    finally:
        session.close()


@app.exception_handler(HTTPException)
async def audited_http_exception_handler(request: Request, exc: HTTPException):
    _record_audit_event(request, exc.status_code, str(exc.detail))
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def audited_validation_exception_handler(request: Request, exc: RequestValidationError):
    _record_audit_event(request, status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc.errors()))
    return await request_validation_exception_handler(request, exc)

# El frontend (Vite, puerto 5173) consume esta API en serio desde la
# Entrega 2 -- sin este origen habilitado, cada fetch del panel falla por
# CORS antes de llegar a ningun router.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Verifica que el proceso FastAPI esta arriba (no valida la BD)."""
    return {"status": "ok"}
