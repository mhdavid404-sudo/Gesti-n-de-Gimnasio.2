"""Smoke test minimo del esqueleto de Entrega 1.

No requiere una base de datos viva -- el health check no toca la BD. El
plan de pruebas formal (pytest, casos de uso reales) es alcance de Cofi
(QA) en una entrega posterior, una vez que exista logica de negocio que
probar.
"""

from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_check_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema_is_served() -> None:
    """RF014: la API debe estar documentada (OpenAPI/Swagger)."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
