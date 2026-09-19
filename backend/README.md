# backend — SmartGym v2 (Entrega 1)

Backend en Python 3.13 + FastAPI + PostgreSQL, arquitectura hexagonal
(`domain/application/infrastructure/api`). Alcance exacto de esta entrega
en `../DECISIONES.md` y `../COORDINACION-ENTREGA1.md` (raiz del repo).

## Para Royer (Dockerfile / docker-compose)

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
-> tipo -> constraints, pensada para que Leo (frontend) escriba sus tipos
TypeScript sin necesidad de leer este codigo Python/SQLAlchemy.

## Estructura (arquitectura hexagonal)

```
src/
  domain/            entidades planas (dataclasses) + puertos (ABC), por modulo
  application/        casos de uso (Entrega 1: firmas/esqueleto, sin logica completa)
  infrastructure/
    db/               Base declarativa, engine/session, modelos SQLAlchemy
    repositories/      implementaciones concretas de los puertos de dominio
    migrations/        Alembic (env.py, versions/)
  api/
    main.py            entry point de FastAPI
    v1/                routers + schemas Pydantic por modulo
tests/                 smoke tests (plan de pruebas formal es alcance de Cofi/QA)
```

## Alcance de Entrega 1 (que SI y que NO)

Ver `../DECISIONES.md` y `../SMARTGYM-V2-BRIEF.md`. En resumen: modelo de
datos completo (13-14 entidades, ver nota en `MODELO-DATOS.md`) +
esqueleto hexagonal, SIN casos de uso completos ni login/JWT funcional.
