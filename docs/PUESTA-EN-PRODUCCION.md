# Puesta en producción — verificación desde un clon limpio

Fecha: 2026-11-16/17. Toda la salida de esta página es real, copiada
literal de los comandos ejecutados (ningún resultado fue inventado o
estimado). Verificación hecha en una carpeta nueva
(`C:\Users\User\Desktop\dev\SmartGym-v2-clon-limpio`), clonada desde el
repositorio local en el commit `b995464`, con un nombre de proyecto Docker
Compose aislado (`-p smartgym-clon`) para garantizar un volumen de base de
datos genuinamente vacío (el entorno de desarrollo original usa el nombre
de proyecto por defecto, `smartgym`, fijado en `docker-compose.yml`; sin
aislar el nombre, el clon habría reusado el volumen con los datos ya
sembrados del entorno de desarrollo, lo que no demuestra un arranque real
desde cero).

## Comandos exactos

```bash
# 1. Clonar a una carpeta nueva
cd C:\Users\User\Desktop\dev
git clone <repo> SmartGym-v2-clon-limpio
cd SmartGym-v2-clon-limpio

# 2. Variables de entorno — copiar el ejemplo, sin editar nada
cp .env.example .env

# 3. Levantar desde cero (build real, sin reusar el volumen del entorno de
#    desarrollo -- -p aisla contenedores/red/volumen con otro nombre)
docker compose -p smartgym-clon up --build -d

# 4. Migraciones (nunca automáticas, se corren a mano -- ver backend/README.md)
docker compose -p smartgym-clon exec backend alembic upgrade head

# 5. Datos de prueba
docker compose -p smartgym-clon exec backend python seed.py
```

## .env.example (completo, el usado tal cual)

```dotenv
# .env.example — SmartGym v2
#
# Copia este archivo a `.env` (no versionado) antes de correr
# `docker compose up`. Valores de DEV unicamente.
# NUNCA usar estos valores en un ambiente real/productivo.

# --- Postgres (servicio "db") ---
POSTGRES_DB=smartgym_dev
POSTGRES_USER=smartgym
POSTGRES_PASSWORD=smartgym_dev_pass

# --- Backend (servicio "backend") ---
# Host "db" porque backend y db comparten la red default de compose
# (smartgym_default) -- nunca "localhost" dentro de Docker.
DATABASE_URL=postgresql+psycopg2://smartgym:smartgym_dev_pass@db:5432/smartgym_dev

# --- Backend (servicio "backend") -- auth (Entrega 2) ---
# Secreto de firma de JWT. Valor de DESARROLLO unicamente.
JWT_SECRET=dev-only-insecure-secret-smartgym-v2-cambiar-en-produccion

# --- Frontend (servicio "frontend") ---
# Usado por el cliente HTTP del frontend (frontend/src/api/client.ts)
# para construir la URL base de la API.
VITE_API_URL=http://localhost:8000
```

## Puertos y URLs

| Servicio | Puerto | URL |
|---|---|---|
| Frontend (Vite dev server) | 5173 | http://localhost:5173 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| Documentación interactiva (Swagger/OpenAPI) | 8000 | http://localhost:8000/docs |
| PostgreSQL | 5432 | `localhost:5432` (cliente de BD) |

## Resultado real de cada paso

- **Build (`docker compose -p smartgym-clon up --build -d`):** las 3
  imágenes (`smartgym-clon-backend`, `smartgym-clon-frontend`, `postgres:16`
  oficial) construyeron y arrancaron sin errores. `docker compose -p
  smartgym-clon ps` confirmó los 3 contenedores `Up`/`healthy`.
- **Migraciones (`alembic upgrade head`):** las 4 migraciones corrieron en
  orden sobre una base vacía, sin error:
  ```
  Running upgrade  -> 0001, esquema inicial: 14 tablas del modelo aprobado en DECISIONES.md
  Running upgrade 0001 -> 0002, resolucion del backlog de alineacion de modelo para Entrega 2
  Running upgrade 0002 -> 0003, planes y servicios extra (Entrega 3, amplia RF004/RF005)
  Running upgrade 0003 -> 0004, cambio de plan y su efecto en servicios extra (amplia RF004/RF005)
  ```
- **Seed (`python seed.py`):** corrió sin error, confirmó la creación de
  las 3 cuentas demo, el catálogo de planes/servicios y los datos de
  ejemplo (membresía por vencer, extra contratado, progreso, rutina, dieta).

## Cuentas demo (todas con contraseña `Demo2026!`)

| Rol | Correo |
|---|---|
| Admin | `admin@demo.com` |
| Entrenador | `entrenador@demo.com` |
| Cliente | `cliente@demo.com` |

## Verificación con `curl` — resultado real de cada paso

```
$ curl -s -w "\n[HTTP %{http_code}]\n" http://localhost:8000/health
{"status":"ok"}
[HTTP 200]

$ curl -s -w "\n[HTTP %{http_code}]\n" -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"admin@demo.com","password":"Demo2026!"}'
{"access_token":"…","token_type":"bearer","user":{"id":1,"email":"admin@demo.com","role":"admin",…}}
[HTTP 200]

# Mismo resultado (200, token real) para entrenador@demo.com y cliente@demo.com.
```

### Flujo completo: alta de cliente → membresía → pago con extra → cambio de plan

Todo ejecutado con el token de `admin@demo.com`, contra el clon limpio recién
levantado (base de datos vacía hasta el seed, cliente nuevo creado aparte
del cliente demo):

1. **Alta de cliente** — `POST /clients` → `201`, cliente `id=2` creado
   junto con su `User` (`temporary_password` generada por el backend).
2. **Asignar membresía** — `POST /memberships` (`client_id=2, plan_id=1`
   Básica) → `201`, membresía `id=2`, `status: "activa"`.
3. **Contratar un extra** — `POST /memberships/2/services`
   (`service_id=1`, "Rutinas personalizadas", $250 — no incluido en
   Básica) → `201`, `price_at_purchase: "250.00"`.
4. **Registrar el pago con desglose** — `POST /payments`
   (`amount: 649.00`, `items: [plan $399 + servicio $250]`) → `201`,
   `items` persistidos y devueltos correctamente (399 + 250 = 649 ✓).
5. **Cambiar de plan (Básica → VIP)** — `POST
   /memberships/2/change-plan/preview` → `200`, `cancelled_extras: []`,
   `kept_extras: [Rutinas personalizadas]` (VIP no incluye ese servicio,
   se conserva correctamente) — `POST /memberships/2/change-plan` (mismo
   body) → `200`, mismo resultado persistido. `GET /memberships/2`
   confirma `plan_id: 2` (VIP).

**Resultado: los 5 pasos del flujo completo funcionaron sin errores en la
primera corrida**, desde un clon que nunca había visto `docker compose
build` ni una base de datos antes de este procedimiento.

## Problemas encontrados y su solución

Ninguno durante esta verificación. El único ajuste necesario, ya aplicado
antes de clonar (no durante la verificación en sí), fue decidir el nombre
de proyecto Compose aislado (`-p smartgym-clon`) para no reusar el volumen
de datos del entorno de desarrollo — ver `DECISIONES.md`, entrada del
2026-11-16 ("Cierre final: Parte 2, Parte 5 y Parte 4").

## Cierre de la verificación

Tras confirmar el flujo completo, se detuvo y eliminó el stack del clon
(`docker compose -p smartgym-clon down`) y se restauró el entorno de
desarrollo original (`docker compose up -d` desde
`C:\Users\User\Desktop\dev\SmartGym-v2`, con su propio volumen de datos
intacto, nunca tocado por esta verificación). La carpeta del clon se
conserva en `C:\Users\User\Desktop\dev\SmartGym-v2-clon-limpio` como
evidencia reproducible.

## Publicar con túnel para demo

Para mostrar el sistema a alguien fuera de esta máquina (sin desplegarlo
de verdad) alcanza con **un solo túnel** apuntando al frontend
(`localhost:5173`) -- no hace falta un segundo túnel para el backend.

El frontend llama a la API por ruta relativa (`/api/v1/...`, ver
`frontend/src/api/client.ts`) en vez de una URL absoluta con su propio
puerto, y `frontend/vite.config.ts` reenvía `/api` al servicio `backend`
del lado del servidor (dentro del contenedor, nunca algo que el navegador
tenga que resolver). Como la llamada queda en el MISMO origen que la
página, el navegador nunca hace una petición entre orígenes distintos --
no hace falta tocar `CORSMiddleware` en `backend/src/api/main.py` ni
agregar el dominio del túnel a ninguna lista (que además cambia cada vez
que se abre un túnel rápido de Cloudflare).

### 1. Levantar el sistema normal

```powershell
docker compose up -d
```

### 2. Instalar `cloudflared` (una sola vez)

```powershell
winget install Cloudflare.cloudflared
```

### 3. Abrir el túnel apuntando al frontend

```powershell
cloudflared tunnel --url http://localhost:5173
```

La terminal imprime una URL pública tipo
`https://palabras-al-azar.trycloudflare.com` -- compártela para la demo.
Es un **túnel rápido** (sin cuenta de Cloudflare, sin configuración
previa): vive mientras la terminal siga abierta y la URL cambia cada vez
que se vuelve a correr el comando.

### Notas

- Quien entre por esa URL ve exactamente lo mismo que `localhost:5173` en
  esta máquina, incluida la pantalla de login real (los 3 roles/cuentas
  demo siguen aplicando) -- no es una copia de datos ni un ambiente
  aislado, es la misma base de datos de desarrollo.
- Para cerrar la demo: `Ctrl+C` en la terminal del túnel. El sistema
  sigue corriendo en local (`docker compose down` lo apaga, si hace falta).
- Si el contenedor del frontend ya estaba corriendo desde antes de que
  existiera el proxy de `vite.config.ts`, hace falta un
  `docker compose restart frontend` una vez para que tome la configuración
  nueva (un `docker compose up -d` normal, en una máquina que recién
  clona el repo, ya la incluye).
