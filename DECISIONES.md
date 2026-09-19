# DECISIONES.md — SmartGym v2

Registro de decisiones de arquitectura tomadas por Isai (revisor de diseño) durante el desarrollo. Ninguna decisión de arquitectura pasa sin quedar escrita aquí.

---

### 2026-09-12 — Modelo de datos y estructura hexagonal para Entrega 1

- **Propuesta original:**
  - Modelo lógico con 14 entidades: `User`, `ClientProfile` (separado de `User`), `MembershipPlan`, `Membership`, `Payment`, `Exercise`, `Routine`, `RoutineExercise`, `RoutineAssignment`, `DietPlan`, `DietAssignment`, `BodyProgress`, `Notification`, `AuditLog`, cubriendo RF001-RF015.
  - `trainer_id` como FK simple 1:n en `ClientProfile` (no tabla puente n:n).
  - Roles y estados (`role`, `status`, `method`, `type`) modelados como enums nativos de PostgreSQL.
  - `RoutineExercise` + `Exercise` como catálogo reutilizable de ejercicios.
  - `password_hash` presente en `User` desde ya, aunque el login funcional no se implementa en esta entrega.
  - Estructura hexagonal: `domain/application/infrastructure/api`, cada uno subdividido por módulo (users, clients, memberships, payments, routines, diets, progress, notifications).
  - Frontend: 8 pantallas (Login, Dashboard, Clientes, Detalle de Cliente con tabs, Membresías, Rutinas, Dietas, Progreso) con datos mock, sin conexión real a backend.

- **Decisión de Isai:** aprobada con correcciones

- **Por qué:**
  - El modelo cubre correctamente los 15 RF sin relaciones faltantes ni redundantes.
  - Separar `User` de `ClientProfile` evita un modelo anémico (admin/entrenador arrastrando columnas de cliente que nunca usan) y alinea el modelo con los bounded contexts de la arquitectura hexagonal.
  - `trainer_id` 1:n es válido para el alcance actual (ningún RF pide múltiples entrenadores por cliente); es una decisión reversible y de bajo riesgo si cambia en Entrega 2/3.
  - `RoutineExercise`/`Exercise` no es sobre-ingeniería: sin esa tabla puente, RF008 (historial estructurado) queda roto.
  - `password_hash` debe existir ya para no migrar dos veces — el alcance de Entrega 1 pide explícitamente el modelo de datos de usuarios/roles completo, aunque el login no funcione todavía.

- **Alternativa aplicada (correcciones obligatorias antes de codear):**
  1. **Enums de PostgreSQL → VARCHAR + CHECK constraint** para `role/status/method/type`. Razón: un ENUM nativo de Postgres es más caro de migrar con Alembic que un CHECK; es casi seguro que aparezca un status o método nuevo en Entrega 2.
  2. **Entidades de dominio sin imports de SQLAlchemy.** Las entidades en `domain/*/entities` deben ser clases planas (dataclasses); los modelos SQLAlchemy viven aparte en `infrastructure/db/models`. El mapeo entidad↔ORM ocurre solo en `infrastructure/repositories/`, nunca en el dominio.
  3. **Interfaces de puerto sin `Session` en la firma.** Las interfaces de repositorio (`domain/*/repositories`, Protocol/ABC) reciben y devuelven entidades de dominio, nunca un objeto de sesión de SQLAlchemy — ese es detalle de infraestructura inyectado en la implementación concreta.
  4. **Invariantes de negocio documentadas como responsabilidad de `application/`, no de la FK:** "`trainer_id` debe apuntar a un `User` con `role=entrenador`" y "`Routine.created_by` debe ser entrenador o admin" no las garantiza la base de datos — deben quedar explícitas en el código de casos de uso para que nadie asuma una protección que la FK no da.
  5. **Frontend:** los tipos TypeScript de los datos mock deben reflejar 1:1 los nombres, tipos y enums del modelo lógico aprobado aquí (mismo `role`, mismo `status` de membership, mismos campos de `BodyProgress`), para que en Entrega 2 conectar al backend real sea un swap de fuente de datos y no una reescritura de pantallas.
  - Punto menor no bloqueante, pendiente de confirmar con el negocio real más adelante: si `height_cm` debe fijarse en `ClientProfile` o quedarse remedible en `BodyProgress` (se deja en `BodyProgress` por ahora).

---

### 2026-09-12 — Corrección de conteo de entidades

- **Propuesta original:** esta misma acta decía "13 entidades" en la entrada anterior.
- **Decisión:** corregida (error de conteo del orquestador, no una decisión de Isai).
- **Por qué:** Valde, al construir el esqueleto, notó que la lista enumerada son 14 entidades (el conteo omitía `AuditLog`, que sí está en la lista y es necesaria para RF015). Confirmado contra `backend/MODELO-DATOS.md`.
- **Alternativa aplicada:** se corrigió el texto a "14 entidades" en la entrada del 2026-09-12 arriba. Sin impacto en el modelo real, que siempre incluyó las 14.

---

### 2026-09-12 — Bug real en endpoints DELETE (backend no arrancaba)

- **Propuesta original:** `@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)` con `def ... -> None` en `clients.py` y `users.py`, sin `response_model` explícito.
- **Decisión:** corregida.
- **Por qué:** Cofi (QA) encontró que esto tumbaba toda la aplicación al importar (`0 rutas registradas`) y hacía fallar la colección completa de `pytest`. FastAPI, sin `response_model` explícito, infiere el response model de la anotación de retorno; `-> None` se traduce a la clase `NoneType`, que es *truthy* en Python, así que dispara el assert de que un status 204 no puede llevar body — y falla en tiempo de import, no solo al llamar el endpoint.
- **Alternativa aplicada:** se agregó `response_model=None` explícito en ambos decoradores (`backend/src/api/v1/routers/clients.py:49`, `backend/src/api/v1/routers/users.py:43`). Verificado con `docker compose build` exitoso tras el fix.

---

### 2026-09-12 — `psycopg2-binary` sin wheel para Python 3.13

- **Propuesta original:** `psycopg2-binary==2.9.9` en `backend/requirements.txt`.
- **Decisión:** corregida.
- **Por qué:** esa versión no publica wheel precompilado para `cp313`, así que `pip install` dentro de la imagen `python:3.13-slim` intentaba compilar desde código fuente y fallaba (`fatal error: assert.h: No such file or directory`, falta headers de build en la imagen slim).
- **Alternativa aplicada:** subir a `psycopg2-binary==2.9.10`, que sí trae wheel `cp313` (`manylinux_2_17_x86_64`). Confirmado con `docker compose build` — instala en ~1s vía wheel, sin compilar nada, y las dos imágenes (`smartgym-backend`, `smartgym-frontend`) construyen sin errores.

---

### 2026-09-12 — Arbitraje de desalineación de modelo backend↔frontend

- **Propuesta original:** Cofi (QA) reportó 4 puntos de divergencia entre `backend/MODELO-DATOS.md` (real) y `frontend/src/types/models.ts` (real): `Membership.status` con valores distintos, `BodyProgress` con campos distintos, `Payment.status` faltante en frontend, y `ClientProfile.emergency_contact` modelado distinto en cada lado.

- **Decisión de Isai:** corregida (en ambos lados, no solo uno) — y ampliada: al verificar el código real (no solo el reporte de Cofi), Isai encontró 3 divergencias silenciosas adicionales no reportadas (`AssignmentStatus`, `NotificationType`, `AuditLog.entity` vs `entity_type`), más un caso donde el frontend tenía razón y el backend estaba corto (`Payment.registered_by`/`notes`).

- **Por qué:**
  - `Membership.status`: "próxima a vencer" es un hecho relativo al tiempo (`end_date` vs hoy), no un estado que alguien decide y persiste. Persistirlo exige un job diario que puede desincronizarse de la fecha real, duplicando la fuente de verdad. El modelo ya tiene el lugar correcto para esto: `notifications.type` (`'membresia_por_vencer'`), que es exactamente lo que pide RF006 ("detectar y **notificar**"). `'pendiente'` sí es un estado real (membresía creada, pago no confirmado) que el frontend omitió por descuido.
  - `BodyProgress`: RF010 dice literalmente "peso, **medidas**, fecha de registro" — medidas en plural es requisito explícito. Valde las quitó al construir sin dejarlo documentado, violando la propia regla de este archivo. Las medidas individuales (`chest/waist/hip/arm_cm`) y `muscle_mass_kg` no son mutuamente excluyentes: ambas son nullable, sin costo de integridad. `hip_cm` (agregado por Leo, no estaba en el diseño original) se aprueba porque es el complemento estándar de `waist_cm` (ratio cintura-cadera).
  - `Payment.registered_by`/`notes`: existían en el frontend pero no en el backend — es el caso inverso, el backend quedó corto. `payments` era la única tabla de movimiento de dinero sin un FK de "quién lo hizo" (inconsistente con `assigned_by` en `routine_assignments`/`diet_assignments`).
  - `emergency_contact`: verificado en la migración real, el backend no tiene NINGÚN campo de contacto de emergencia (ni uno ni dos) — no implementado, no divergente. Se resuelve como campo único de texto libre, igual que `address` en la misma tabla (consistencia de normalización).
  - **Nota de proceso:** dos desviaciones silenciosas (Valde quitando medidas, Leo agregando `por_vencer`) terminaron divergiendo entre sí en vez de converger. Confirma por qué ninguna desviación del modelo aprobado —aunque parezca una mejora— se construye sin pasar por arbitraje primero.

- **Alternativa aplicada:**
  - **`Membership.status`** (sin cambios en backend): `'activa' | 'vencida' | 'cancelada' | 'pendiente'`. Leo quita `'por_vencer'` de `MembershipStatus`, agrega `'pendiente'`.
  - **`BodyProgress`** (columnas finales): `id, client_id, record_date, weight_kg, height_cm, body_fat_pct, muscle_mass_kg, chest_cm, waist_cm, hip_cm, arm_cm, notes` — todas las de medidas nullable. Valde agrega `chest_cm/waist_cm/hip_cm/arm_cm` al backend. Leo renombra `body_fat_percent` → `body_fat_pct` y agrega `muscle_mass_kg`.
  - **`Payment`**: Valde agrega `registered_by INTEGER NOT NULL FK->users.id ON DELETE RESTRICT` y `notes TEXT NULLABLE` al backend. Leo agrega `status: PaymentStatus` (`'completado'|'pendiente'|'rechazado'`) al frontend.
  - **`ClientProfile.emergency_contact`**: Valde agrega `emergency_contact VARCHAR(255) NULLABLE` al backend (no existía). Leo colapsa `emergency_contact_name`/`_phone` en un solo `emergency_contact: string | null`.
  - **`AssignmentStatus`**: backend es fuente de verdad (`'activa'|'completada'|'cancelada'`), Leo corrige el frontend (tenía `'pausada'|'finalizada'`, scope creep sin respaldo en RF007-RF009).
  - **`NotificationType`**: Leo agrega `'sistema'`, que faltaba en el frontend.
  - **`AuditLog`**: Leo renombra `entity` → `entity_type` para calzar con la columna real.
  - **Verificación de cierre:** Cofi debe re-correr la comparación completa backend↔frontend después de que Valde y Leo apliquen esto — no se autocertifica, dado que ya divergieron una vez sin que nadie lo notara hasta QA.

- **Resultado de la re-verificación de Cofi:** los 7 puntos arbitrados arriba quedaron 7/7 PASA (confirmado contra el DDL real generado por Alembic dentro de la imagen Docker `python:3.13-slim`, no solo contra `MODELO-DATOS.md`). `pytest` (2/2), dominio limpio de SQLAlchemy/FastAPI, sin ENUM nativo, 43 rutas registradas sin error, y frontend (`tsc -b`, lint) — todo PASA.

---

### 2026-09-12 — Backlog de alineación de modelo para Entrega 2 (no bloquea el cierre de Entrega 1)

- **Qué se encontró:** al hacer la re-verificación de los 7 puntos arbitrados, Cofi comparó también las 14 entidades completas (no solo los 7 puntos pedidos) contra el DDL real y encontró 11 divergencias adicionales entre `backend/MODELO-DATOS.md` y `frontend/src/types/models.ts`, no cubiertas por el arbitraje anterior:
  1. `Notification.title` (backend, `NOT NULL`) falta por completo en el frontend.
  2. `RoutineExercise.order` (frontend) vs `order_index` (backend, columna real) — nombre distinto.
  3. `DietPlan.daily_calories` (frontend) vs `calories_target` (backend, columna real) — nombre distinto.
  4. `RoutineAssignment.notes` / `DietAssignment.notes` existen en el frontend pero no en el backend (columna inexistente).
  5. `MembershipPlan.benefits` existe en el frontend sin respaldo en el backend; `MembershipPlan.created_at` existe en backend pero falta en el frontend.
  6. `AuditLog.entity_id`: backend `VARCHAR(50)` (string), frontend `number | null` — tipo incompatible, no solo nulabilidad.
  7. `users.updated_at` y `client_profiles.updated_at` (backend, `NOT NULL`) faltan en el frontend.
  8. `Payment.created_at` y `Exercise.created_at` (backend, `NOT NULL`) faltan en el frontend.
  9. `Exercise.equipment` existe en el frontend sin respaldo en el backend.
  10. Nullabilidad relajada de forma sistemática en el frontend para varios campos que sí son `NULLABLE` en el backend (`ClientProfile.phone/birth_date/address`, `Exercise.muscle_group/description`, `Routine.description`, `BodyProgress.height_cm`) — mismo patrón de riesgo que el punto 7b de abajo.
  11. `AuditLog.entity_type` es `NULLABLE` en el backend pero `string` no-nulo en el frontend (hallazgo original de Leo durante la corrección anterior, confirmado real por Cofi).

- **Decisión:** no se resuelve ahora — queda como backlog explícito para Entrega 2, no bloquea el cierre de Entrega 1.
- **Por qué:** el alcance de Entrega 1 dice explícitamente "prototipo... SIN lógica de negocio conectada al backend todavía (puede usar datos mock/estáticos)". Estas 11 divergencias solo importan cuando exista integración real; hoy el frontend funciona con mocks propios y el backend no tiene casos de uso implementados que dependan de estos campos. Forzar una tercera ronda de arbitraje ahora arriesga un ciclo sin fin de "QA encuentra más divergencias en cada vuelta" sobre un esqueleto que todavía va a cambiar en Entrega 2.
- **Alternativa aplicada:** este backlog queda registrado aquí como el punto de partida obligatorio de la sesión de Entrega 2 — antes de conectar frontend↔backend de verdad, alguien (Isai primero) debe revisar esta lista completa, no solo los 7 puntos ya resueltos.

---

### 2026-09-12 — Identidad visual real de marca en la landing pública (`/`)

- **Propuesta original:** el dueño del proyecto colocó el logo real de Stronger Aragón (`frontend/src/assets/logo-stronger.jpg`) y pidió construir la página principal pública en la ruta `/`, usando la estructura de layout de Smart Fit como referencia pero con identidad visual 100% propia: verde extraído del logo (no lima), fondo negro, tipografía condensada agresiva, botones de esquina recta, fotos placeholder de alto contraste hasta tener fotografía real.

- **Decisión:** aprobada y construida — no es una decisión de Isai (no toca arquitectura de dominio/backend), es un cambio de producto/identidad de marca que se registra aquí por instrucción explícita del dueño.

- **Por qué:**
  - El panel interno (Dashboard, Clientes, Membresías, etc.) y la landing pública son dos productos distintos con audiencias distintas: uno es una herramienta de administración (paleta grafito/cobre "sala de pesas" ya aprobada), el otro es la cara pública de la marca real Stronger Aragón. Mezclarlos en una sola paleta habría sido incorrecto para ambos.
  - El verde de marca no se inventó: se extrajo pixel a pixel del logo real (`logo-stronger.jpg`, muestreo directo con `System.Drawing`) — promedio `#1E581B`, tono dominante `#204020`, sombra `#004400`, brillo `#177016`–`#206020`. Es un verde bosque/militar con degradado real, consistente con la marca, no un verde genérico de "app fitness".
  - Sin fotografías reales del gimnasio disponibles todavía, se optó por tratamiento gráfico (gradientes duotono con el verde de marca + firma geométrica de esquina cortada) en vez de fotos de stock o inventadas — evita presentar como "real" algo que no lo es, y deja el swap a fotos reales como un cambio de una sola custom property por sección.

- **Alternativa aplicada:**
  - Nueva página `frontend/src/pages/LandingPage.tsx` + `LandingPage.css`, con toda su paleta/tipografía bajo el scope `.landing` — cero variables tocan `:root` ni `src/styles/theme.css` (verificado: el panel interno, incluyendo `/login`, conserva su paleta cobre/grafito y radio de 6px sin cambios).
  - Reestructura de rutas en `App.tsx`: `"/"` → `LandingPage` (nueva), `"/login"` → `LoginPage` (contenido sin tocar, solo cambió su path), `"*"` → redirige a `"/"`. Se corrigió además el link "Cerrar sesión" del `Sidebar.tsx` interno, que apuntaba a `"/"` y con el cambio de rutas hubiera mandado al usuario a la landing pública en vez de a `/login`.
  - Tipografía: `Anton` (nueva, solo para el titular del hero) + `Bebas Neue` (ya cargada, reutilizada para el resto de títulos) + `Inter` (texto de lectura) — mantiene hilo de familia tipográfica con el panel interno sin compartir su paleta.
  - Secciones construidas: Header fijo (logo real + nav + CTA a `/login`), Hero ("ENTRENA COMO BESTIA"), propuesta de valor, Planes (3 tarjetas reutilizando `membershipPlans` real de `src/mocks/data.ts` — Básica $399, VIP $649 destacada como "Más popular", Premium $999, sin precios inventados), Clases de Box (tabla de horario: L-V 6:00–10:00 y 17:00–21:00, sábados 8:00–11:00), Galería de instalaciones (3 bloques placeholder: peso libre, ring de box, área funcional), Footer (logo real, contacto de ejemplo explícitamente genérico, redes sociales sin links reales).
  - **Fix de infraestructura relacionado:** el contenedor `frontend` de Docker no detectaba los cambios de archivo del host (bind mount + `chokidar` de Vite no reciben eventos de sistema de archivos de Windows sin polling). Se agregó `server.watch.usePolling: true` a `frontend/vite.config.ts` y se reinició el contenedor — confirmado con hot-reload funcionando después del fix.
  - Verificado en navegador tras el fix: `/` carga la landing con el logo real y las 7 secciones completas; `/login` conserva su paleta original intacta; el header con `position: fixed` está genuinamente pinneado a `top: 0` (confirmado con `getBoundingClientRect()` vía JavaScript, no solo captura de pantalla — la herramienta de captura tuvo un artefacto visual de composición con `backdrop-filter` + scroll que no reflejaba el render real).

---

### 2026-09-12 — Extensión de la identidad visual de marca al panel interno completo

- **Propuesta original:** el dueño del proyecto pidió aplicar la misma identidad visual de Stronger (paleta del logo, tipografía bold/industrial, negro + verde de marca) a las 7 pantallas detrás del login (Dashboard, Lista de Clientes, Detalle de Cliente, Membresías, Rutinas, Dietas, Progreso corporal), manteniendo consistencia total con la landing ya construida. `/login` quedó explícitamente fuera de este alcance ("todo lo que está detrás del login").

- **Decisión:** aprobada y construida — de nuevo, decisión de producto/identidad de marca, no de arquitectura de dominio; se registra aquí por instrucción explícita del dueño.

- **Por qué:**
  - Unificar la identidad de marca entre la landing pública y el panel interno evita que el sistema se sienta como dos productos inconexos una vez que un usuario pasa de una a otro.
  - Reusar exactamente los mismos valores de verde ya extraídos del logo (no re-derivarlos) mantiene una única fuente de verdad de color en todo el proyecto.
  - **Problema real detectado por Leo antes de tocar nada:** `LoginPage.css` consume directamente las variables de `:root` (`--color-bg`, `--color-accent`, `.card`, `.btn-primary`, etc.), sin scope propio como sí tiene `.landing`. Cambiar los valores en `:root` habría reskinado el login de forma invisible, violando el alcance pedido. Solución aplicada: `:root` se queda con la paleta cobre/grafito original (sigue sirviendo a `/login` intacto), y se agregó un bloque `.app-shell { ... }` que sobreescribe esas mismas variables con la paleta de marca. Como `AppShell.tsx` envuelve exactamente las 7 pantallas internas y nada más, todo el sistema de componentes compartidos (`.card`, `.btn-primary`, `StatusPill`, tabs, etc.) heredó el verde/negro por cascada de variables CSS, sin reescribir esos componentes uno por uno.
  - **`--color-success` deliberadamente alejado por hue, no solo por brillo, del nuevo `--color-accent`:** ambos eran verdes: si solo se hubiera bajado la luminosidad de uno, "botón de acción" y "membresía al día" habrían seguido leyéndose como la misma señal visual. Se movió `--color-success` a un teal verde-azulado (`#3fb6ad`, ~178° de hue) mientras `--color-accent` se mantiene en verde puro (~119°, derivado de `#177016` pero aclarado a `#229620` para dar ~4.7:1 de contraste sobre superficie — el tono real del logo es demasiado oscuro para usarse igual como acento interactivo en una UI de datos).
  - Verde como texto pequeño sobre negro casi puro (nav activo del sidebar, iniciales de avatar) no alcanzaba ni AA-large en la verificación manual de contraste — se resolvió con el mismo principio ya aplicado en la landing: verde solo en fondos sólidos de chip/botón con texto claro u ojo oscuro encima, nunca como texto pequeño directo sobre negro.

- **Alternativa aplicada:**
  - `src/styles/theme.css`: `:root` conserva la paleta cobre/grafito original (para `/login`); nuevo bloque `.app-shell` con la paleta de marca completa (fondos `#0a0a0a`→`#1c1c1c`, texto `#f5f5f0`/`#a8a8a2`/`#7a7a75`, `--color-accent: #229620` con hover `#26a824`, `--color-success: #3fb6ad`, warning/danger sin cambio de tono, `--radius-sm/md/lg: 3px/6px/10px` — familia de esquina mínima igual que la landing, ajustada ligeramente respecto a los 2-3px de `.landing` para legibilidad de tablas).
  - Ajustes puntuales de componentes que usaban valores fuera del sistema de tokens o pill-shape: `Sidebar.css` (nav activo a texto claro en vez de verde pequeño), `Topbar.css` (avatar e indicador de notificaciones), `StatusPill.css` (radio mínimo en vez de `100px` pill), `ClientDetailPage.css` (avatar de iniciales a relleno sólido).
  - Sin placeholders de imagen nuevos: las 7 pantallas son tablas/formularios/gráfica SVG propia sin huecos de foto; los avatares de iniciales ya existentes se unificaron visualmente con el nuevo acento en vez de introducir fotos o icon-packs.
  - Verificado en navegador: Dashboard, Detalle de Cliente (con tabs) y `/login` — el panel interno adoptó negro+verde de marca de forma consistente, `/login` permanece exactamente igual (paleta cobre/grafito, sin cambios).

---

### 2026-09-12 — Identidad de marca extendida a Login (última pantalla pendiente)

- **Propuesta original:** el dueño pidió que `/login` (la única pantalla que había quedado fuera a propósito en la entrada anterior) también adoptara la paleta verde/negro de marca.

- **Decisión:** aprobada y construida.

- **Por qué:** con Login sumado, ya no queda ningún consumidor de la paleta cobre/grafito original en todo el proyecto — mantener dos capas de variables (`:root` cobre/grafito + override `.app-shell` verde/negro) habría sido complejidad sin propósito.

- **Alternativa aplicada:**
  - `src/styles/theme.css`: la paleta de marca se movió directamente a `:root` (reemplazando los valores cobre/grafito ahí mismo) y se eliminó el bloque de override `.app-shell` que ya no cumplía función. `.app-shell` sigue existiendo solo como clase de layout (flex container) en `AppShell.css`, sin relación con color.
  - `--radius-sm/md/lg` unificados en `3px/6px/10px` en `:root` para todo el sistema.
  - Único color hardcodeado que quedaba de la paleta vieja: el gradiente radial de `.login__hero` (`rgba(217,142,62,.10)`, cobre) corregido a `rgba(34,150,32,.10)` (verde de marca, mismo hue que `--color-accent`).
  - Verificado: `/login`, `/` (landing) y `/dashboard` (panel interno) revisados visualmente tras el cambio — landing sigue con su scope `.landing` independiente sin alteración, panel interno sin cambios visuales, login ahora consistente con el resto del sistema. Grep final confirma cero rastros de los valores hex de la paleta cobre/grafito original en el código fuente de `src/`.

---

### 2026-09-13 — Taste DNA de UFC Gym adaptado al panel interno

- **Propuesta original:** el dueño corrió el skill `/taste` sobre `https://www.ufcgym.mx/` (análisis completo en `ufcgym.mx.md`/`.json` y exportado a `CLAUDE.md`, sección "Design Taste") y pidió aplicar los 4 patrones extraídos —no los colores literales de UFC Gym— al Dashboard, la tabla de clientes/membresías, y un formulario nuevo de registro/pago, con la paleta real de Stronger (verde/negro/blanco, nunca el rojo/negro de UFC Gym).

- **Decisión:** aprobada y construida — decisión de producto/identidad visual, no de arquitectura de dominio.

- **Por qué:**
  - El verde de marca (`--color-accent`) se usaba hasta ahora como color de TEXTO en números protagonistas, precios y tabs activos — violaba directamente el principio "un acento en reserva" de UFC Gym (rojo <1% del área visible en las 3 páginas analizadas, confinado a CTAs). Se migró a blanco/neutro todo uso decorativo (números de `StatNumber`, precios de plan, avatares de iniciales, marca del sidebar, tabs, viñetas), dejando el verde exclusivamente en `.btn-primary`, focus-ring, y links de acción reales.
  - El protagonismo visual de los números grandes necesitaba una fuente distinta de color: UFC Gym logra jerarquía con tipografía+tamaño, nunca con `font-weight` (100% peso "400" en las 3 páginas). Se adoptó el mismo principio: `Permanent Marker` (brush) para títulos de sección y números protagonistas, en blanco.
  - `Helvetica Neue` (system font stack, sin auto-hosteo por licencia) reemplaza a Inter para todo lo funcional (tablas, formularios), replicando la separación display/funcional observada en el sitio original.
  - A diferencia de UFC Gym (gaps arbitrarios sin unidad base — correcto para un sitio editorial), esto es una interfaz operativa: se definió una escala de espaciado sistemática (`--space-1: 4px` a `--space-6: 48px`) para Dashboard, tabla y formulario.
  - La sombra dura de una sola capa ("photos are cut out, not lit") se adoptó para las tarjetas de resumen del Dashboard, pero explícitamente NUNCA en inputs de formulario — un input necesita affordance de control interactivo (borde, fondo elevado, anillo de foco), no de "objeto cortado y pegado" como una foto/tarjeta de resumen.

- **Alternativa aplicada:**
  - `theme.css`: nueva variable `--font-display-brush` (Permanent Marker), `--font-body` cambiado a `'Helvetica Neue', Helvetica, Arial, sans-serif`, nueva escala `--space-1`...`--space-6`, nueva `--shadow-card` (`rgba(0,0,0,0.6) -1px 2px 6px 0px`, una sola capa). Bebas Neue no se retiró, bajó a segundo nivel (insignias pequeñas).
  - Auditoría completa de `var(--color-accent)` en `src/`: se quedó verde solo donde hay una acción real (botones primarios, focus-ring, 3 links de navegación explícitos); todo lo demás (números, precios, avatares, tabs, viñetas) pasó a blanco/neutro. Los colores semánticos (warning/danger/success) no se tocaron — comunican estado real, no son decoración de marca.
  - Pantalla nueva `/clientes/nuevo` (`ClientFormPage.tsx`/`.css`): dos tarjetas (Datos del cliente / Membresía y pago inicial), monto autocompletado según plan elegido, único botón verde en toda la pantalla (submit). Solo UI/mock, sin conexión real a backend — consistente con el alcance de Entrega 1.
  - Verificado en navegador: Dashboard, Clientes, `/clientes/nuevo` (incluida la interactividad de selección de plan → autocompletado de monto), y Membresías (pantalla no tocada directamente, para confirmar que el cambio global de tokens no rompió nada) — todo consistente, sin regresiones.

---

### 2026-09-13 — Fotos reales en la landing (reemplazo de placeholders gráficos)

- **Propuesta original:** el dueño pidió reemplazar los placeholders gráficos de la landing (gradientes CSS documentados como "hasta tener fotografía real") con fotos reales de gimnasio, de un banco libre de derechos, para el hero y las 3 tarjetas de instalaciones.

- **Decisión:** aprobada y construida.

- **Por qué:** los placeholders siempre estuvieron pensados como temporales (ver entrada "Identidad visual real de marca en la landing pública" — "cuando haya fotos reales, basta sobreescribir esa custom property con url(...)"); esto ejecuta ese plan.

- **Fuente y licencia:** las 4 fotos son de Unsplash, licencia gratuita (verificado en cada una que decía "Foto gratuita en Unsplash" / "Descargar gratis" — no Unsplash+, que es contenido pagado de Getty Images y se descartó explícitamente al encontrarlo en la búsqueda inicial). Créditos:
  - Hero: Corey Young — silueta de levantamiento olímpico a contraluz (`photo-1604247584233-99c80a8aae2c`)
  - Peso libre: Brett Jordan — rack de pesas en escala de grises (`photo-1590487988256-9ed24133863e`)
  - Ring de Box: Bogdan Yukhymchuk — par de guantes de boxeo negros (`photo-1549719386-74dfcbf7dbed`)
  - Área funcional: Heidi Erickson — fila de kettlebells (`photo-1632077804406-188472f1a810`)
  - Guardadas en `frontend/src/assets/photos/` (`hero-training.jpg`, `facility-pesas.jpg`, `facility-box.jpg`, `facility-funcional.jpg`).

- **Alternativa aplicada:**
  - `LandingPage.css`: `--hero-image`, `--facility-image-pesas`, `--facility-image-box`, `--facility-image-funcional` pasaron de gradiente CSS a `url(...)` apuntando a los archivos reales. `--value-image` se dejó como gradiente — no se pidió foto para esa sección.
  - Se agregó `filter: grayscale(1) contrast(1.15)` al backdrop del hero para garantizar alto contraste en blanco y negro (la foto elegida ya era casi monocromática por el contraluz, pero el filtro lo asegura de forma explícita en vez de depender de que la foto fuente se mantenga así).
  - Se agregó `filter: grayscale(0.3) contrast(1.05)` a las 3 tarjetas de instalaciones — desaturación parcial para que combinen tonalmente con el resto de la paleta negro/verde sin perder legibilidad de la foto.
  - Los íconos de línea dibujados a mano que servían de placeholder dentro de cada tarjeta de instalación (`IconBarbell`/`IconGlove`/`IconKettlebell`) se ocultaron (`display: none`) — con la foto real de fondo, el ícono flotando encima quedaba redundante y se leía como residuo de UI, no como diseño intencional.
  - Verificado en navegador: hero con silueta legible y texto con buen contraste sobre la foto (el overlay de degradado ya existente para legibilidad se conservó sin cambios); las 3 tarjetas de instalaciones muestran la foto real con la firma geométrica de esquina cortada de la landing, sin íconos redundantes.

---

### 2026-09-13 — Animación con propósito (skill `/emil-design-eng`) y aumento de tipografía

- **Propuesta original:** el dueño corrió el skill de diseño `/emil-design-eng` y pidió 4 animaciones específicas (hover/press en botones y tarjetas, entrada suave al hacer scroll, stagger en la tabla de clientes, feedback de validación en el formulario) más un aumento general de tamaño de fuente, exigiendo que cada animación pasara el framework de 4 preguntas (¿debe animarse? ¿qué comunica? ¿qué easing? ¿qué velocidad?) antes de implementarse.

- **Decisión:** aprobada y construida — decisión de producto/craft de interfaz, no de arquitectura de dominio.

- **Por qué:** el frontend se sentía "plano y genérico de IA" sin animación; el framework de Emil Kowalski exige que cada animación tenga un propósito verificable (no decoración porque sí) y respete rendimiento/accesibilidad — se aplicó estrictamente, incluyendo negarse a animar donde no correspondía.

- **Alternativa aplicada:**
  - Nuevas variables de easing reutilizables en `theme.css`: `--ease-out: cubic-bezier(0.23,1,0.32,1)`, `--ease-in-out: cubic-bezier(0.65,0,0.35,1)` — curvas fuertes, no las débiles por defecto de CSS.
  - Botones: `:active { transform: scale(0.97) }` con `--ease-out` a 120ms (feedback de presión real); hovers envueltos en `@media (hover: hover) and (pointer: fine)` para no disparar falsos positivos en touch.
  - Landing: scroll-reveal vía `IntersectionObserver` (hook nuevo `useScrollReveal.ts`) — fade + `translateY(14px)` a 420ms `ease-out`, aplicado solo a secciones editoriales (propuesta de valor, planes, clases, instalaciones, footer); el hero queda excluido (ya es lo primero visible). Verificado en navegador: `data-reveal` pasa de `"hidden"` a `"visible"` al cruzar el margen del observer.
  - Tabla de clientes: stagger de filas vía `animation-delay` por índice (tope 12, ~45ms entre filas) solo en carga/re-filtrado real, nunca en cada tecla del buscador (evitado usando `key` estable de React).
  - Formulario de registro: validación real por campo (antes solo HTML5 nativo) con mensajes de error (`role="alert"`) que aparecen con fade corto y se limpian individualmente al corregir ese campo — verificado en navegador (enviar vacío marca 5 campos requeridos; escribir en "Nombre completo" limpia solo ese error, los demás persisten).
  - `prefers-reduced-motion: reduce` fuerza duración casi nula y quita `transform` en todas las animaciones nuevas (botones, tarjetas, scroll-reveal, filas de tabla, error de formulario), conservando los cambios de opacidad/color.
  - **Deviación documentada por Leo:** no se agregó feedback de presión (`:active` / scale) a las stat cards del Dashboard ni a `.plan-card`/`.lp-facility-card`, porque ninguna es realmente clickeable en el código actual (sin `href`/`onClick`) — según la pregunta 1 del propio framework, simular una acción de presión que no existe sería peor que no animar. Se les dio hover con lift + sombra dura donde el encargo las nombraba explícitamente, sin fingir affordance falsa.
  - Tipografía: `body` 15px→16px, `.section-title` 24px→26px, `.topbar__title` 30px→32px, `StatNumber` y demás texto de tablas/tarjetas subidos proporcionalmente (incrementos de 0.5–2px) — verificado que el `clamp()` de `StatNumber` sigue sin desbordar el grid de 4 columnas del Dashboard tras el cambio.

---
