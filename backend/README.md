# backend — SmartGym v2

Backend en Python 3.13 + FastAPI + PostgreSQL, arquitectura hexagonal
(`domain/application/infrastructure/api`). Los 15 RF (RF001-RF015) tienen
casos de uso reales, autenticacion JWT por rol y pruebas automatizadas --
ver `../docs/ESTADO-ACTUAL.md` para el estado detallado y `../DECISIONES.md`
para el historial de decisiones de arquitectura.

## Dockerfile / docker-compose

- **Gestor de dependencias:** `requirements.txt` (pip simple, no Poetry).
- **Comando de arranque exacto** (correr con cwd = `backend/`):

  ```
  uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
  ```

  El modulo es `src.api.main` (variable `app`) porque el esqueleto sigue
  la estructura `backend/src/api/...`. Para que `import src...` resuelva,
  el `WORKDIR` del contenedor debe ser el directorio que contiene `src/`
  (es decir, `backend/` copiado dentro del contenedor), y ese mismo
  directorio debe quedar en `PYTHONPATH` (uvicorn agrega el directorio
  actual por defecto; si en tu imagen no ocurre, agrega
  `ENV PYTHONPATH=/app` o el path que uses de `WORKDIR`).
- Migraciones (`alembic upgrade head`) **no** se corren automaticamente en
  el `CMD`/`entrypoint` -- se corren a mano, ver mas abajo.

## Variables de entorno

| Variable | Valor esperado (dev, via docker-compose) |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://smartgym:smartgym_dev_pass@db:5432/smartgym_dev` |

`DATABASE_URL` nunca esta hardcodeada en el codigo -- ver
`src/infrastructure/db/session.py` y `src/infrastructure/migrations/env.py`.
Fuera de Docker (dev local sin compose), usa `localhost` en vez de `db`.

## Como correr en local (sin Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg2://smartgym:smartgym_dev_pass@localhost:5432/smartgym_dev
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Con el servidor arriba: documentacion interactiva en
`http://localhost:8000/docs` (Swagger UI, RF014) y health check en
`http://localhost:8000/health`.

## Migraciones (Alembic)

Requiere una base Postgres viva y accesible via `DATABASE_URL` (la levanta
Royer con docker-compose; no hay una en este entorno de desarrollo). Correr
siempre a mano, nunca automatico:

```bash
cd backend
alembic upgrade head
```

o, dentro de docker-compose ya levantado:

```bash
docker compose exec backend alembic upgrade head
```

La migracion inicial (`src/infrastructure/migrations/versions/0001_initial_schema.py`)
crea las 14 tablas del modelo aprobado en `../DECISIONES.md`. Esta escrita
a mano (no autogenerada) porque no hay BD viva en este entorno para que
Alembic compare contra ella.

## Modelo de datos

Ver `MODELO-DATOS.md` en esta misma carpeta -- tabla plana entidad -> campo
-> tipo -> constraints, pensada para escribir los tipos TypeScript del
frontend sin necesidad de leer este codigo Python/SQLAlchemy.

## Estructura (arquitectura hexagonal)

```
src/
  domain/            entidades planas (dataclasses) + puertos (ABC), por modulo
  application/        casos de uso (logica de negocio real, sin SQLAlchemy/FastAPI)
  infrastructure/
    db/               Base declarativa, engine/session, modelos SQLAlchemy
    repositories/      implementaciones concretas de los puertos de dominio
    migrations/        Alembic (env.py, versions/)
    scheduler.py        job diario de deteccion de vencimientos (RF006, APScheduler)
  api/
    main.py            entry point de FastAPI, manejo de errores y arranque del scheduler
    v1/                routers + schemas Pydantic por modulo
tests/                 plan de pruebas automatizado (pytest), un archivo por modulo
```

## Alcance actual

Ver `../docs/ESTADO-ACTUAL.md` (estado real de cada RF, verificado contra
el codigo) y `../DECISIONES.md` (historial completo de decisiones de
arquitectura). En resumen: los 15 RF tienen modelo de datos, API y logica
de negocio reales, autenticacion JWT por rol, y bitacora de auditoria
automatica.
