# COORDINACION-ENTREGA1.md — SmartGym v2

Plan de coordinación para Entrega 1, escrito por Benja tras la aprobación (con correcciones) de Isai registrada en `DECISIONES.md` (2026-09-12). Agentes: **Valde** (backend), **Leo** (frontend), **Royer** (DevOps).

**Aclaración de mecanismo:** no existe un bus de mensajes en vivo entre estos agentes. Coordinan de dos formas nada más: (1) archivos compartidos que uno escribe y otro lee, y (2) el orquestador (David / Claude Code invocando a cada subagente en su turno) que pasa contexto de uno a otro. Este documento asume ese modelo, no un runtime de colas/RPC.

---

## 1. Agentes y alcance de cada uno (recordatorio del límite duro)

| Agente | Entrega en Entrega 1 | NO hace todavía |
|---|---|---|
| **Valde** | Modelo lógico+físico (Alembic), esqueleto hexagonal `domain/application/infrastructure/api` | Casos de uso completos, JWT funcional |
| **Leo** | 8 pantallas con datos mock, navegación, diseño propio | Conexión real a la API del backend |
| **Royer** | `docker-compose.yml` con `db`, `backend`, `frontend` | Pipelines CI/CD, orquestación de producción |

---

## 2. Secuenciación

### Regla general: Valde, Leo y Royer son independientes entre sí en esta entrega
No hay integración real (Leo usa mocks, Valde no expone nada que Leo consuma, Royer no necesita que el código funcione, solo que exista para construir la imagen). Esto significa que **los tres pueden trabajar en paralelo** una vez que exista el contrato de la sección 3 — que es precisamente lo que este documento fija de antemano para no tener que esperar a que alguien lo "descubra" en runtime.

### Lo único secuencial de verdad
1. **Isai → todos** (ya ocurrió): sin el modelo de datos aprobado en `DECISIONES.md`, ni Valde ni Leo tienen qué construir. Punto de partida ya cumplido.
2. **Valde/Leo → Royer, parcialmente**: Royer puede escribir el `docker-compose.yml` completo y el servicio `db` (Postgres) sin esperar a nadie, porque ese contrato queda fijo en la sección 3 de este documento. Pero el `Dockerfile` de `backend/` y de `frontend/` sí necesita que exista, como mínimo:
   - `backend/requirements.txt` (o el manifiesto de dependencias que Valde elija) y el path del módulo de entrada (`app.main:app` o equivalente).
   - `frontend/package.json` con script `dev` (Vite ya trae uno por defecto) y el puerto configurado.

   **Recomendación concreta:** Valde y Leo deben crear ese archivo de manifiesto como uno de sus primeros pasos (antes incluso de escribir entidades o componentes), para no bloquear a Royer más que unos minutos. Royer, mientras tanto, puede avanzar con placeholders (`# TODO: confirmar entrypoint con Valde`) y no tiene que esperar sentado.

3. **Valde → Leo, informalmente, solo para el modelo de datos (no para código):** Leo no lee código Python de Valde. Lee el modelo de datos aprobado en `DECISIONES.md` (que ya tiene los nombres/tipos/enums definitivos) para escribir sus tipos TS. Si Valde ajusta algo del modelo durante la implementación (un campo que se renombra, por ejemplo), ese cambio debe reflejarse primero en `DECISIONES.md` o en el archivo de la sección 4, y de ahí Leo lo toma — nunca al revés, y nunca leyendo el ORM de Valde directamente.

No hay más dependencias duras. Todo lo demás puede iniciar en paralelo desde ahora.

---

## 3. Convenciones compartidas (fijas — nadie las improvisa)

Esta tabla es el contrato. Si alguno de los tres necesita desviarse, debe registrarlo en `DECISIONES.md` como corrección, igual que las de Isai.

| Convención | Valor |
|---|---|
| Nombre del proyecto compose | `smartgym` |
| Servicio backend | `backend` |
| Servicio frontend | `frontend` |
| Servicio de base de datos | `db` |
| Puerto backend (host y contenedor) | `8000` (FastAPI/Uvicorn, `uvicorn app.main:app --host 0.0.0.0 --port 8000`) |
| Puerto frontend dev server (host y contenedor) | `5173` (default de Vite, `--host 0.0.0.0` para exponerlo fuera del contenedor) |
| Puerto Postgres (host y contenedor) | `5432` |
| Nombre de la base de datos (dev) | `smartgym_dev` |
| Usuario de Postgres (dev) | `smartgym` |
| Password de Postgres (dev) | `smartgym_dev_pass` — **solo dev, va en `.env` no versionado, nunca hardcodeado en `docker-compose.yml`** |
| Cadena de conexión SQLAlchemy | `postgresql+psycopg2://smartgym:smartgym_dev_pass@db:5432/smartgym_dev` (host `db`, no `localhost`, porque backend y db están en la misma red de compose) |
| Red de docker-compose | la red default que crea compose (`smartgym_default`) — no se declara una custom a menos que surja una razón concreta |
| Carpetas raíz del monorepo | `backend/`, `frontend/`, `docker-compose.yml` en la raíz junto a `DECISIONES.md` |
| Variables de entorno | `.env.example` en la raíz (versionado) con todas las de arriba sin valores reales sensibles; `.env` real ignorado en `.gitignore` |

**Nota para Royer:** en Entrega 1 no hay lógica de negocio ni login funcionando, así que el `docker-compose.yml` puede (y debería) priorizar developer experience: volúmenes montados para hot-reload tanto en `backend` (uvicorn `--reload`) como en `frontend` (Vite ya trae HMR), en vez de una imagen de producción multi-stage. Producción/optimización de imagen no es parte del alcance de esta entrega.

**Nota para Valde:** no ejecutar `alembic upgrade head` automáticamente en el `CMD`/`entrypoint` del contenedor `backend`. Ver sección 5 (manejo de fallas) — se corre manualmente para no tumbar todo el stack si una migración falla.

---

## 4. Dónde vive el estado compartido

| Archivo | Quién escribe | Quién lee | Para qué |
|---|---|---|---|
| `DECISIONES.md` | Isai (y quien registre correcciones futuras) | Valde, Leo, Royer | Fuente de verdad del modelo de 13 entidades, las 5 correcciones obligatorias, y cualquier decisión de arquitectura posterior |
| `COORDINACION-ENTREGA1.md` (este archivo) | Benja | Valde, Leo, Royer, orquestador | Contrato de convenciones (sección 3) y plan de secuenciación |
| `backend/infrastructure/db/migrations/versions/*` (Alembic) | Valde | — | Esquema físico real; es la fuente de verdad técnica del modelo, pero **no es lo que Leo debe leer** |
| Recomendado: `backend/MODELO-DATOS.md` (tabla plana: entidad → campos → tipo → constraints, en lenguaje simple) | Valde | Leo | Leo no debería tener que leer Python/SQLAlchemy para escribir sus tipos TS. Valde debería producir este resumen legible como parte de su entrega, derivado 1:1 de sus migraciones/entidades. Si Valde no lo produce, Leo trabaja directo desde `DECISIONES.md`, que ya tiene el detalle suficiente para Entrega 1. |
| `.env.example` | Royer (o quien defina el compose primero) | Valde, Leo, Royer | Único lugar con los nombres de variables de entorno reales que todos deben usar (`DATABASE_URL`, `VITE_API_URL` aunque no se use aún, etc.) |

---

## 5. Manejo de fallas

**Caso: Valde entrega migraciones de Alembic que no corren (`alembic upgrade head` falla).**
- No debe tumbar el resto del stack. Por eso la recomendación de la sección 3: el contenedor `backend` no corre migraciones automáticamente al arrancar. El servicio `db` levanta solo; `backend` puede levantar (aunque sin tablas) sin que compose falle.
- Leo no se ve afectado — trabaja con mocks, no con la base real.
- Royer no se ve afectado — su trabajo es que el contenedor construya y el servicio levante, no que las migraciones sean correctas.
- Acción: Valde corrige y vuelve a correr `docker compose exec backend alembic upgrade head` manualmente hasta que pase. Esto es responsabilidad exclusiva de Valde; no bloquea la entrega de Leo ni de Royer.

**Caso: Royer arma el `docker-compose.yml` antes de que Valde/Leo tengan manifiesto de dependencias.**
- No es un bloqueo real dado el contrato fijo de la sección 3: Royer ya sabe puertos, nombres de servicio y credenciales sin depender de nadie. Puede escribir el compose completo y el `Dockerfile` de `db` (imagen oficial de Postgres, sin build propio) de inmediato.
- Para `backend/Dockerfile` y `frontend/Dockerfile`, si el manifiesto de dependencias todavía no existe, Royer deja un Dockerfile mínimo con un comentario `TODO` señalando qué falta (nombre del archivo de dependencias, comando de arranque exacto) en vez de inventarlo. Esto se resuelve solo en cuanto Valde/Leo publiquen ese archivo — no requiere que terminen el resto del código.

**Caso: los tipos TS de Leo se desalinean del modelo aprobado (nombres/tipos/enums no calzan 1:1).**
- Esto no lo detecta ninguna herramienta automática en este repo (no hay generación de tipos desde el schema en esta entrega). Es un chequeo manual: quien cierre la Entrega 1 (David, o Isai/Cofi como revisores) debe comparar los tipos mock de Leo contra la tabla de entidades de `DECISIONES.md` antes de dar la entrega por cerrada.
- Si se detecta un desalineado, se corrige en Leo directamente — no implica tocar el backend porque no hay integración real todavía.

**Caso: alguien se desvía de la tabla de convenciones (ej. Leo deja el puerto de Vite en otro valor, o Valde usa otro nombre de base de datos).**
- No hay enforcement automático. Se detecta en revisión cruzada antes de cerrar la entrega, comparando cada entregable contra la sección 3 de este documento. Si el cambio tiene una razón válida, se documenta como corrección en `DECISIONES.md`, igual que las de Isai — no se cambia en silencio.

---

## 6. Supuestos que el orquestador debe confirmar

Estos son puntos donde tomé una decisión razonable sin que estuviera explícita en `DECISIONES.md` ni en el brief, y que Valde/Leo/Royer necesitan para no bloquearse. Deben confirmarse o corregirse antes de que Royer termine los Dockerfiles de `backend`/`frontend`:

1. **Gestor de dependencias de Python de Valde:** asumí `requirements.txt` simple (no Poetry/pipenv) por ser lo más directo para un proyecto de curso. Si Valde prefiere Poetry, el `Dockerfile` de Royer cambia.
2. **Nombre exacto del módulo de entrada FastAPI:** asumí `app.main:app` como convención típica dentro de `backend/api/`. Valde debe confirmar el path real una vez que arme el esqueleto hexagonal (podría ser `src.api.main:app` u otro, dependiendo de cómo subdivida `api/` en el esqueleto).
3. **Layout de monorepo:** asumí `backend/` y `frontend/` como carpetas hermanas en la raíz junto a `docker-compose.yml`. No hay nada en el brief que lo contradiga, pero no está escrito explícitamente en ningún lado — vale la pena que quede fijado la primera vez que alguien cree esas carpetas.
4. **`height_cm` en `ClientProfile` vs `BodyProgress`:** ya viene marcado como punto menor no bloqueante en `DECISIONES.md` (se deja en `BodyProgress` por ahora) — lo repito aquí solo para que Leo no lo mueva por su cuenta al diseñar la pantalla de perfil de cliente.

---

## Resumen de hand-off

- **Isai → Valde/Leo:** ya ocurrió (`DECISIONES.md`, 2026-09-12).
- **Valde/Leo → Royer:** parcial y rápido — solo el nombre del archivo de dependencias y el comando de arranque, idealmente en los primeros minutos de trabajo de cada uno, no al final.
- **Valde → Leo:** informal, vía `DECISIONES.md` (o `backend/MODELO-DATOS.md` si Valde decide producirlo), nunca vía lectura directa de código Python.
- **Todos → revisión final:** contra la tabla de convenciones de la sección 3, antes de cerrar Entrega 1. Esa revisión no la automatiza este documento — la hace quien cierre la entrega (David / Isai / Cofi).
