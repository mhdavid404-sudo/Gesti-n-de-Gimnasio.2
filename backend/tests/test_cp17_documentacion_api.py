"""CP17 -- Documentacion de la API accesible.

Fuente: docs/Plan-de-Pruebas-SmartGym-v2.docx, modulo "API y Sistema" (RF014).

Que se prueba: acceder a /docs del backend.
Pasos: 1. Acceder a /docs del backend.
Resultado esperado: se muestra la documentacion Swagger de todos los endpoints.

Es el unico de los 18 casos de prueba del documento que corresponde a
funcionalidad real de Entrega 1 -- FastAPI expone /docs y /openapi.json
automaticamente a partir de los routers ya montados, sin necesitar
logica de negocio ni base de datos viva. El resto de los CP requieren
casos de uso implementados (Entrega 2, ver DECISIONES.md).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_docs_endpoint_serves_swagger_ui() -> None:
    """Acceder a /docs debe mostrar la interfaz Swagger."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger-ui" in response.text.lower()


def test_openapi_schema_lists_endpoints_from_every_module() -> None:
    """La documentacion debe cubrir los endpoints de los 9 modulos (RF001-RF015)."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    paths = schema["paths"]
    assert len(paths) > 0

    expected_prefixes = [
        "/api/v1/users",
        "/api/v1/clients",
        "/api/v1/membership-plans",
        "/api/v1/memberships",
        "/api/v1/payments",
        "/api/v1/exercises",
        "/api/v1/routines",
        "/api/v1/diets",
        "/api/v1/progress",
        "/api/v1/notifications",
        "/api/v1/audit-logs",
    ]
    for prefix in expected_prefixes:
        assert any(path.startswith(prefix) for path in paths), (
            f"No se encontro ningun endpoint documentado bajo {prefix}"
        )
