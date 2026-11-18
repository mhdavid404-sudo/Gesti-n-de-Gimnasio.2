# SmartGym v2 — Stronger Aragón

Sistema de gestión integral para gimnasio: usuarios y roles, clientes,
membresías y pagos, vencimientos y notificaciones, rutinas, dietas,
progreso corporal y bitácora de auditoría. Arquitectura hexagonal en el
backend (`domain/application/infrastructure/api`), React + TypeScript en
el frontend, PostgreSQL como base de datos.

Estado detallado de cada requerimiento funcional (RF001-RF015) en
[`docs/ESTADO-ACTUAL.md`](docs/ESTADO-ACTUAL.md). Historial completo de
decisiones de arquitectura en [`DECISIONES.md`](DECISIONES.md). Auditoría
completa documentación-vs-código en
[`docs/AUDITORIA-DOC-VS-CODIGO.md`](docs/AUDITORIA-DOC-VS-CODIGO.md),
resultados de pruebas en
[`docs/RESULTADOS-FINALES.md`](docs/RESULTADOS-FINALES.md) y verificación
de despliegue desde un clon limpio en
[`docs/PUESTA-EN-PRODUCCION.md`](docs/PUESTA-EN-PRODUCCION.md). Manual de
usuario e instalación para una persona sin conocimientos técnicos en
[`docs/MANUAL-USUARIO.md`](docs/MANUAL-USUARIO.md).

## Cómo levantar el proyecto (Docker)

Requiere Docker y Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (documentación interactiva Swagger/OpenAPI en **http://localhost:8000/docs**)
- Base de datos PostgreSQL: puerto 5432

Las migraciones no corren automáticamente al levantar el stack -- aplicarlas a mano la primera vez:

```bash
docker compose exec backend alembic upgrade head
```

## Datos de prueba (seed)

El proyecto incluye un script de seed con un usuario por rol y datos
realistas fechados en 2026 (membresía, progreso, rutina y dieta
asignadas, catálogo de 3 planes y 6 servicios extra con un extra ya
contratado de ejemplo). Es destructivo e idempotente: trunca y vuelve a
poblar las tablas de datos de prueba, se puede correr las veces que haga
falta.

```bash
docker compose exec backend python seed.py
```

**Nota:** correr la suite completa de `pytest` también trunca estas
tablas (es la estrategia de aislamiento entre pruebas, ver
`backend/tests/conftest.py`) -- si acabas de correr las pruebas y quieres
volver a tener las cuentas demo, corre `seed.py` de nuevo después.

**Nota sobre qué servicio incluye cada plan:** la asignación del seed
(Básica solo incluye casillero; VIP suma clases grupales y evaluación;
Premium incluye los 6) es **dato de ejemplo para la demo, no una decisión
de negocio confirmada con el cliente real** -- qué servicios trae cada
plan es 100% configurable desde la pantalla "Planes y servicios" (solo
Admin), sin tocar código ni el seed.

### Cuentas demo

Todas con contraseña `Demo2026!`.

| Rol | Correo | Notas |
|---|---|---|
| Admin | `admin@demo.com` | Control total: clientes, membresías, pagos, catálogo de planes, bitácora. |
| Entrenador | `entrenador@demo.com` | Ve y gestiona solo a sus clientes asignados (Cliente Demo). |
| Cliente | `cliente@demo.com` | Solo lectura de su propia membresía (vence en pocos días, para ver la alerta de vencimiento), rutina, dieta y progreso. |

## Pruebas automatizadas

```bash
docker compose exec backend pytest tests/ -v
```

Un archivo por módulo en `backend/tests/`. Resultado real más reciente en
`docs/RESULTADOS-FINALES.md` (106/106 casos).

## Estructura del repositorio

```
backend/    API FastAPI, arquitectura hexagonal (ver backend/README.md)
frontend/   Panel React + Vite + TypeScript, y la landing pública
docs/       Auditorías, resultados de pruebas, diagrama ER, capturas (docs/capturas/)
```
