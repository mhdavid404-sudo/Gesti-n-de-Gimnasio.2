# MODELO-DATOS.md — SmartGym v2 (Entrega 1)

Tabla plana derivada 1:1 de las migraciones de Alembic
(`src/infrastructure/migrations/versions/0001_initial_schema.py`) y de los
modelos SQLAlchemy (`src/infrastructure/db/models/`). Pensada para que Leo
(frontend) escriba sus tipos TypeScript sin tener que leer Python.

**Nota sobre el conteo de entidades:** `../DECISIONES.md` titula el modelo
como "13 entidades" pero la lista que aprobo Isai enumera 14 (incluye
`AuditLog`, necesario para RF015). Este documento y el codigo implementan
las 14. `AuditLog` se agrupo bajo el modulo de codigo `notifications`
(carpeta `domain/notifications`, `infrastructure/db/models/notifications.py`)
por afinidad ("eventos del sistema"), no porque el modelo de datos lo
requiera asi.

**Regla aplicada en toda la tabla:** cualquier columna de rol/estado/metodo/
tipo es `VARCHAR` + `CHECK constraint`, nunca `ENUM` nativo de PostgreSQL
(DECISIONES.md, correccion #1 de Isai).

---

## users

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL (login funcional no implementado en Entrega 1) |
| full_name | VARCHAR(255) | NOT NULL |
| role | VARCHAR(20) | NOT NULL, CHECK IN ('admin', 'entrenador', 'cliente') |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now(), se actualiza en cada UPDATE |

## client_profiles

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| user_id | INTEGER | NOT NULL, UNIQUE, FK -> users.id (ON DELETE CASCADE) |
| trainer_id | INTEGER | NULLABLE, FK -> users.id (ON DELETE SET NULL) |
| phone | VARCHAR(30) | NULLABLE |
| birth_date | DATE | NULLABLE |
| address | VARCHAR(255) | NULLABLE |
| emergency_contact | VARCHAR(255) | NULLABLE (campo unico de texto libre, igual que `address`; no separado en nombre/telefono) |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now(), se actualiza en cada UPDATE |

**Invariante de negocio no garantizada por la FK (responsabilidad de
`application/clients`):** `trainer_id` debe apuntar a un `User` con
`role = 'entrenador'`.

**Arbitraje de Isai (DECISIONES.md, 2026-09-12 — Arbitraje de desalineacion
backend↔frontend):** `emergency_contact` no existia en el backend (no
implementado, no divergente). Se agrego como campo unico, no como par
`emergency_contact_name`/`emergency_contact_phone`.

## membership_plans

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| name | VARCHAR(100) | NOT NULL, UNIQUE (ej. "Basica", "VIP", "Premium") |
| price | NUMERIC(10,2) | NOT NULL |
| duration_days | INTEGER | NOT NULL |
| description | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## memberships

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| client_id | INTEGER | NOT NULL, FK -> client_profiles.id (ON DELETE CASCADE) |
| plan_id | INTEGER | NOT NULL, FK -> membership_plans.id (ON DELETE RESTRICT) |
| start_date | DATE | NOT NULL |
| end_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, CHECK IN ('activa', 'vencida', 'cancelada', 'pendiente') |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## payments

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| membership_id | INTEGER | NOT NULL, FK -> memberships.id (ON DELETE CASCADE) |
| amount | NUMERIC(10,2) | NOT NULL |
| payment_date | TIMESTAMPTZ | NOT NULL |
| method | VARCHAR(20) | NOT NULL, CHECK IN ('efectivo', 'tarjeta', 'transferencia') |
| status | VARCHAR(20) | NOT NULL, CHECK IN ('completado', 'pendiente', 'rechazado') |
| registered_by | INTEGER | NOT NULL, FK -> users.id (ON DELETE RESTRICT) |
| notes | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Arbitraje de Isai (DECISIONES.md, 2026-09-12 — Arbitraje de desalineacion
backend↔frontend):** `registered_by`/`notes` agregados al backend --
`payments` era la unica tabla de movimiento de dinero sin FK de "quien lo
hizo" (inconsistente con `assigned_by` en `routine_assignments`/
`diet_assignments`).

## exercises

Catalogo reutilizable de ejercicios (sin esta tabla, RF008 -- historial
estructurado -- queda roto).

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| name | VARCHAR(150) | NOT NULL, UNIQUE |
| muscle_group | VARCHAR(100) | NULLABLE |
| description | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## routines

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| name | VARCHAR(150) | NOT NULL |
| created_by | INTEGER | NOT NULL, FK -> users.id (ON DELETE RESTRICT) |
| description | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Invariante de negocio no garantizada por la FK (responsabilidad de
`application/routines`):** `created_by` debe ser un `User` con
`role = 'entrenador'` o `role = 'admin'`.

## routine_exercises

Tabla puente `routines` <-> `exercises`, con el detalle de series/
repeticiones de cada ejercicio dentro de una rutina.

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| routine_id | INTEGER | NOT NULL, FK -> routines.id (ON DELETE CASCADE) |
| exercise_id | INTEGER | NOT NULL, FK -> exercises.id (ON DELETE RESTRICT) |
| sets | INTEGER | NOT NULL |
| reps | INTEGER | NOT NULL |
| order_index | INTEGER | NOT NULL, UNIQUE junto con routine_id (uq_routine_exercises_order) |
| rest_seconds | INTEGER | NULLABLE |
| notes | TEXT | NULLABLE |

## routine_assignments

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| routine_id | INTEGER | NOT NULL, FK -> routines.id (ON DELETE CASCADE) |
| client_id | INTEGER | NOT NULL, FK -> client_profiles.id (ON DELETE CASCADE) |
| assigned_by | INTEGER | NOT NULL, FK -> users.id (ON DELETE RESTRICT) |
| assigned_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, CHECK IN ('activa', 'completada', 'cancelada') |

## diet_plans

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| name | VARCHAR(150) | NOT NULL |
| created_by | INTEGER | NOT NULL, FK -> users.id (ON DELETE RESTRICT) |
| description | TEXT | NULLABLE |
| calories_target | INTEGER | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

**Invariante de negocio no garantizada por la FK (responsabilidad de
`application/diets`):** igual que en `routines.created_by`, debe ser
entrenador o admin.

## diet_assignments

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| diet_plan_id | INTEGER | NOT NULL, FK -> diet_plans.id (ON DELETE CASCADE) |
| client_id | INTEGER | NOT NULL, FK -> client_profiles.id (ON DELETE CASCADE) |
| assigned_by | INTEGER | NOT NULL, FK -> users.id (ON DELETE RESTRICT) |
| assigned_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, CHECK IN ('activa', 'completada', 'cancelada') |

## body_progress

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| client_id | INTEGER | NOT NULL, FK -> client_profiles.id (ON DELETE CASCADE) |
| record_date | DATE | NOT NULL |
| weight_kg | NUMERIC(5,2) | NOT NULL |
| height_cm | NUMERIC(5,2) | NULLABLE (ver nota abajo) |
| body_fat_pct | NUMERIC(4,2) | NULLABLE |
| muscle_mass_kg | NUMERIC(5,2) | NULLABLE |
| chest_cm | NUMERIC(5,2) | NULLABLE |
| waist_cm | NUMERIC(5,2) | NULLABLE |
| hip_cm | NUMERIC(5,2) | NULLABLE |
| arm_cm | NUMERIC(5,2) | NULLABLE |
| notes | TEXT | NULLABLE |

**Nota (DECISIONES.md, punto menor no bloqueante):** `height_cm` se deja
aqui, no en `client_profiles`, hasta que se confirme con el negocio real.
Leo: no mover este campo por tu cuenta al diseñar la pantalla de perfil.

**Arbitraje de Isai (DECISIONES.md, 2026-09-12 — Arbitraje de desalineacion
backend↔frontend):** `chest_cm`/`waist_cm`/`hip_cm`/`arm_cm` restauradas --
RF010 pide literalmente "peso, medidas, fecha de registro" (medidas en
plural es requisito explicito, se habian omitido al construir sin dejarlo
documentado). Todas nullable, sin exclusion mutua con `muscle_mass_kg`.
`hip_cm` se aprueba como complemento estandar de `waist_cm` (ratio
cintura-cadera).

## notifications

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| user_id | INTEGER | NOT NULL, FK -> users.id (ON DELETE CASCADE) |
| type | VARCHAR(30) | NOT NULL, CHECK IN ('membresia_vencida', 'membresia_por_vencer', 'pago_registrado', 'rutina_asignada', 'dieta_asignada', 'sistema') |
| title | VARCHAR(150) | NOT NULL |
| message | TEXT | NOT NULL |
| is_read | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

## audit_logs

Bitacora de eventos/errores del sistema (RF015).

| Campo | Tipo | Constraints |
|---|---|---|
| id | INTEGER | PK, autoincrement |
| user_id | INTEGER | NULLABLE, FK -> users.id (ON DELETE SET NULL) -- un evento de sistema puede no tener usuario asociado |
| action | VARCHAR(100) | NOT NULL |
| entity_type | VARCHAR(100) | NULLABLE |
| entity_id | VARCHAR(50) | NULLABLE |
| details | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

## Resumen de valores permitidos (para los enums de TypeScript de Leo)

| Campo | Valores |
|---|---|
| `users.role` | `admin` \| `entrenador` \| `cliente` |
| `memberships.status` | `activa` \| `vencida` \| `cancelada` \| `pendiente` |
| `payments.method` | `efectivo` \| `tarjeta` \| `transferencia` |
| `payments.status` | `completado` \| `pendiente` \| `rechazado` |
| `routine_assignments.status` / `diet_assignments.status` | `activa` \| `completada` \| `cancelada` |
| `notifications.type` | `membresia_vencida` \| `membresia_por_vencer` \| `pago_registrado` \| `rutina_asignada` \| `dieta_asignada` \| `sistema` |

## Entrypoint FastAPI (para Royer)

```
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Corrido con cwd = `backend/`. Detalle completo en `backend/README.md`.
