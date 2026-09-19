"""Entry point de FastAPI.

Comando de arranque exacto (COORDINACION-ENTREGA1.md, seccion 3), corrido
desde el directorio `backend/`:

    uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

Ver `backend/README.md` para el detalle completo (por que `src.api.main`,
donde debe correrse el comando, y donde queda documentado para Royer).

Entrega 1: NO hay login/JWT funcional ni logica de negocio completa (ver
DECISIONES.md y SMARTGYM-V2-BRIEF.md). Este archivo solo monta el router
agregado de la v1 y expone un health check para verificar que el
contenedor `backend` de docker-compose levanto correctamente.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.router import api_router

app = FastAPI(
    title="SmartGym v2 API",
    description=(
        "API REST de SmartGym v2 (Stronger Aragon) -- RF001-RF015. "
        "Entrega 1: modelo de datos + esqueleto hexagonal. Sin logica de "
        "negocio completa ni autenticacion funcional todavia."
    ),
    version="0.1.0",
)

# Dev-friendly: el frontend (Vite, puerto 5173) no consume esta API todavia
# en Entrega 1 (usa datos mock), pero se deja configurado para no
# bloquear la integracion real en Entrega 2.
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
