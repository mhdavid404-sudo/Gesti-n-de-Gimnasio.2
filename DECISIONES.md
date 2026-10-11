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

### 2026-10-10 — Arranque de Entrega 2: alcance y decisiones de ambigüedad resueltas antes de codear

- **Propuesta original:** desarrollar los 15 RF completos (lógica de negocio real, auth JWT, conexión frontend↔backend), un rediseño de UX/UI del panel (feedback de la profesora: "no tiene buen UI/UX, necesito ver al entrar qué puedo hacer"), y la suite de pruebas CP01-CP18, en una sola corrida módulo por módulo, sin pausas de confirmación salvo por acciones irreversibles/destructivas.

- **Decisión:** aprobada y en ejecución. Antes de empezar, se resuelven aquí las ambigüedades explícitamente delegadas:
  1. **No se agrega un 4.º rol "Recepcionista".** El modelo de datos (`ROLES_VALIDOS` en `domain/users/entities.py`) y RF001/RF002 solo definen Admin/Entrenador/Cliente — el brief de negocio (Apartado I) describe recepcionistas como personas que *operan* el sistema, no como un rol de control de acceso distinto. Se resuelve asignando a las recepcionistas la cuenta con `role="admin"` (mismo nivel de permisos que ya pedían las HU03-HU06, que hablan de "Admin/Recepcionista" indistintamente). Revisable si una entrega futura pide permisos distintos entre ambos.
  2. **El backlog de 11 inconsistencias de modelo (ver entrada "Backlog de alineación de modelo para Entrega 2") se resuelve en una migración nueva (`0002_*`), no editando `0001_initial_schema.py`.** En Entrega 1 se editaba el archivo 0001 directamente porque no había base de datos viva. En Entrega 2 el stack corre contra Postgres real vía `docker compose`, así que el patrón correcto es una migración aditiva.
  3. **Librerías nuevas para auth:** `bcrypt` (hash de contraseña, directo, sin la capa de compatibilidad de `passlib` que tiene historial de fricción con versiones recientes de `bcbrypt`) y `PyJWT` (tokens JWT, más simple que `python-jose` para lo que necesita este proyecto). Se agregan a `backend/requirements.txt`.
  4. **Paleta "verde oliva como color principal"** sustituye el principio de "acento en reserva" adaptado de UFC Gym (entrada "Taste DNA de UFC Gym…") — esa entrada sigue siendo válida como registro histórico de por qué se llegó al verde/negro actual, pero esta instrucción explícita del dueño del proyecto (y el feedback de UI/UX de la profesora) tiene prioridad: ahora se quiere una paleta de sistema de diseño convencional (primario con variantes claras/oscuras, neutros, estados), no un acento ultra-escaso. Detalle de la paleta nueva en la entrada correspondiente a la Parte A (rediseño UX/UI), una vez construida.
  5. **No se hace push** — todo el trabajo de Entrega 2 queda en commits locales, confirmado explícitamente por el dueño del proyecto.
  6. **Ningún nombre de agente/herramienta de IA aparece en código, commits o documentación** desde esta entrada en adelante (ya era la regla de `CLAUDE.md`; se reitera aquí porque esta entrega involucra más superficie de código que cualquier anterior).

- **Por qué:** instrucción explícita y exhaustiva del dueño del proyecto, con autorización previa para decidir ambigüedades menores sin pausar.

- **Alternativa aplicada:** ninguna — se documentan las decisiones arriba y se procede.

---

### 2026-10-10 — Resolución del backlog de alineación de modelo (B0)

- **Propuesta original:** resolver, uno por uno, los 11 puntos listados en la entrada "2026-09-12 — Backlog de alineación de modelo para Entrega 2", decidiendo en cada caso si el backend (fuente de verdad del esquema real) se extiende, si el frontend se corrige, o si ambos lados se alinean a un nombre/tipo/nulabilidad común.

- **Decisión:** los 11 puntos se resuelven así:
  1. **`Notification.title`** — el backend ya lo tenía `NOT NULL` desde la migración `0001`. Se agrega `title: string` a `frontend/src/types/models.ts` y a los 6 registros mock de `notifications` en `mocks/data.ts`. Sin cambio de esquema.
  2. **`RoutineExercise.order` vs `order_index`** — se unifica al nombre del backend (`order_index`), que ya es la columna real desde `0001`. Se renombra en `models.ts`, en los 16 registros mock de `routineExercises` y en el `.sort()` de `getRoutineExercises`. Sin cambio de esquema.
  3. **`DietPlan.daily_calories` vs `calories_target`** — mismo criterio: se unifica al nombre del backend (`calories_target`). Se renombra en `models.ts`, en los 3 registros mock de `dietPlans`, y en los dos lugares del frontend que lo leían (`ClientDetailPage.tsx`, `DietsPage.tsx`). Sin cambio de esquema.
  4. **`RoutineAssignment.notes` / `DietAssignment.notes`** — el frontend ya los modelaba (y los usaba en los formularios de asignación de `RoutinesPage.tsx`/`DietsPage.tsx`) sin respaldo en el backend. Tienen sentido de negocio real (nota del entrenador/admin al asignar) y son consistentes con el `notes` que ya existe en `payments` y `body_progress` — se agregan ambas columnas (`TEXT NULLABLE`) al backend vía migración `0002`.
  5. **`MembershipPlan.benefits`** — mismo criterio que el punto 4: ya se usaba en el frontend (tarjetas de plan en `MembershipsPage`/landing) sin respaldo en el backend. Se agrega como columna `JSON NOT NULL DEFAULT '[]'` vía migración `0002` (lista de texto libre, no amerita tabla puente). **`MembershipPlan.created_at`** ya existía en el backend desde `0001`; se agrega a `models.ts` y a los 3 registros mock. Sin inventar un valor "bonito": se usa la misma fecha arbitraria de alta (`2026-01-01T08:00:00Z`) para los 3 planes del catálogo mock.
  6. **`AuditLog.entity_id`** — el backend es la fuente de verdad (`VARCHAR(50)`, ya así desde `0001` y ya reflejado correctamente como `str | None` en la entidad de dominio `domain/notifications/entities.py`). Se corrige el frontend de `number | null` a `string | null`, y los 4 registros mock de `auditLogs` pasan sus `entity_id` de número a string (`900` -> `'900'`, etc.). Sin cambio de esquema.
  7. **`users.updated_at` / `client_profiles.updated_at`** — ya existían `NOT NULL` en el backend desde `0001`. Se agregan a `User`/`ClientProfile` en `models.ts` y a los 9 + 6 registros mock respectivos (mismo valor que `created_at`, consistente con que en Entrega 1 ningún registro mock ha sido editado todavía).
  8. **`Payment.created_at` / `Exercise.created_at`** — mismo caso: ya existían en el backend desde `0001`. Se agregan a los tipos y a los 7 + 10 registros mock respectivos.
  9. **`Exercise.equipment`** — mismo criterio que los puntos 4/5: ya se usaba en el catálogo mock de ejercicios sin respaldo en el backend. Se agrega como columna `VARCHAR(100) NULLABLE` vía migración `0002` (nullable porque ejercicios de peso corporal, ej. plancha abdominal, no requieren equipo).
  10. **Nulabilidad relajada en el frontend** (`ClientProfile.phone/birth_date/address`, `Exercise.muscle_group/description`, `Routine.description`, `BodyProgress.height_cm`) — el backend es la fuente de verdad (todas son `NULLABLE` desde `0001`). Se corrigen los 7 campos a `| null` en `models.ts`. Esto obligó dos ajustes en cascada: `ClientListRow.phone` (tipo derivado en `mocks/data.ts`) pasa a `string | null`, y `ProgressPage.tsx` agrega un guard `latest?.height_cm != null` antes de pasar el valor a `<StatNumber>` (que no acepta `null`).
  11. **`AuditLog.entity_type`** — el backend es la fuente de verdad (`NULLABLE` desde `0001`). Se corrige el frontend de `string` a `string | null`.

- **Por qué:** en los 7 puntos (1, 2, 3, 6, 7, 8, 11) donde el backend ya tenía la columna/tipo/nulabilidad correcta desde la migración `0001` de Entrega 1, la única causa de la divergencia era que el frontend se escribió sin volver a comparar contra el DDL real — ahí el backend manda y el frontend se corrige. En los 4 puntos restantes (4, 5, 9) el frontend había modelado un campo con respaldo de negocio real (nota de asignación, beneficios de plan, equipo de ejercicio) que el backend nunca tuvo — ahí se amplía el backend en vez de borrar el campo del frontend, siguiendo el mismo criterio que el arbitraje anterior de `registered_by`/`notes` en `Payment` (ver entrada "2026-09-12 — Arbitraje de desalineación de modelo backend↔frontend").

- **Alternativa aplicada:**
  - Migración nueva `backend/src/infrastructure/migrations/versions/0002_backlog_alineacion_modelo.py` (aditiva, `upgrade`/`downgrade` completos): agrega `membership_plans.benefits` (JSON NOT NULL DEFAULT '[]'), `exercises.equipment` (VARCHAR(100) NULLABLE), `routine_assignments.notes` y `diet_assignments.notes` (TEXT NULLABLE). Aplicada con `alembic upgrade head` corrido en local (venv con `DATABASE_URL` apuntando a `localhost:5432`, base levantada con `docker compose up -d db`) — se eligió este método sobre `docker compose exec backend alembic upgrade head` porque no fue necesario reconstruir la imagen del contenedor `backend` solo para correr una migración.
  - `backend/src/infrastructure/db/models/memberships.py`, `routines.py`, `diets.py`: columnas nuevas agregadas a `MembershipPlanModel`, `ExerciseModel`, `RoutineAssignmentModel`, `DietAssignmentModel`.
  - `backend/src/domain/memberships/entities.py`, `domain/routines/entities.py`, `domain/diets/entities.py`: campos nuevos agregados a las dataclasses (`MembershipPlan.benefits`, `Exercise.equipment`, `RoutineAssignment.notes`, `DietAssignment.notes`), todos con default para no romper la construcción existente de estas entidades en otros módulos.
  - `backend/src/infrastructure/repositories/memberships.py`, `routines.py`, `diets.py`: `_to_entity`/`add`/`update` actualizados para traducir los 4 campos nuevos.
  - `backend/src/api/v1/schemas/memberships.py`, `routines.py`, `diets.py`: `*Create`/`*Read` actualizados con los mismos 4 campos, para que la API (aunque sus routers sigan en 501 hasta que se conecten en esta misma entrega) ya tenga el contrato correcto cuando se implementen.
  - `backend/MODELO-DATOS.md`: las 4 columnas nuevas documentadas en sus tablas correspondientes, más una nota de cabecera y una sección final referenciando esta entrada.
  - `frontend/src/types/models.ts`: los 11 puntos reflejados (detalle completo arriba).
  - `frontend/src/mocks/data.ts`: todos los registros mock afectados actualizados para seguir compilando contra los tipos nuevos (sin conectar a la API real todavía — eso es una fase posterior).
  - `frontend/src/pages/ClientDetailPage.tsx`, `DietsPage.tsx`: `.daily_calories` -> `.calories_target`. `frontend/src/pages/ProgressPage.tsx`: guard de nulabilidad agregado para `height_cm`.
  - **Verificación de cierre:** `docker compose up -d db` + `alembic upgrade head` aplican ambas migraciones (`0001` -> `0002`) sin error contra Postgres real; `\d` de las 4 tablas confirma las columnas nuevas con el tipo/nulabilidad esperado; `cd frontend && npx tsc -b --force` compila sin errores.

---

### 2026-10-10 — Módulo Auth/Roles completo (B1): hashing, JWT, casos de uso reales, autorización por rol

- **Propuesta original:** implementar el ciclo completo del módulo de autenticación (RF001, RF002) con hash de password real, JWT de sesión, casos de uso de dominio sin `NotImplementedError`, dependencias de FastAPI para autenticación/autorización, y la pantalla de Login conectada — sentando además la base de RF012/RF013 (acceso acotado por rol a entrenador/cliente) para cuando se conecten los módulos de Clientes/Rutinas/Dietas/Progreso en esta misma entrega.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **`bcrypt` directo, sin `passlib`** y **`PyJWT`**: ya decididos en la entrada de arranque de Entrega 2 (punto 3) — aquí solo se ejecutan. El hash vive en `backend/src/infrastructure/security/password.py` (factor de costo 12, el default de la librería) y el JWT en `backend/src/infrastructure/security/jwt.py`.
  - **Expiración del JWT: 8 horas.** Es un sistema de staff de gimnasio que se usa por turno de trabajo, no una sesión bancaria de alto riesgo — 8 horas cubre un turno completo sin forzar un re-login a media jornada, y sigue siendo acotado (no es un token que no expira).
  - **El dominio no genera el JWT.** `AuthenticateUserUseCase.execute` (en `application/users/use_cases.py`) solo verifica email/password/`is_active` y devuelve el `User` autenticado o lanza `InvalidCredentialsError` — emitir el token es responsabilidad exclusiva de `api/v1/routers/auth.py`, que es la única capa que debe saber que una sesión se representa como un JWT. Mismo principio aplicado a `RegisterUserUseCase` (valida unicidad de email y rol, hashea, persiste) con excepciones de dominio propias (`EmailAlreadyExistsError`, `InvalidRoleError`, `InvalidCredentialsError`, `UserNotFoundError`, nuevas en `domain/users/exceptions.py`, sin ningún import de FastAPI) que el router traduce a HTTP.
  - **No hay alta pública de usuarios.** `POST /users` queda protegido a `role="admin"` — en un sistema de staff de gimnasio no existe un formulario de "crea tu cuenta" abierto al público; las cuentas de entrenador/cliente las crea el staff administrativo. `GET /users/{id}` y `GET /users` quedan abiertos a `admin` y `entrenador` (un entrenador necesita poder consultar información básica de otros usuarios, ej. para verificar a quién le asigna una rutina); `PATCH`/`DELETE /users/{id}` quedan solo para `admin`.
  - **`require_role` es la base de RF012/RF013, no la implementación completa.** Esta dependencia solo resuelve el primer filtro (control de acceso por rol); RF012 (entrenador limitado a SUS clientes asignados) y RF013 (cliente solo lectura de lo propio) necesitan ademas un filtro por dato (no alcanza con "es entrenador", hace falta "es EL entrenador de este cliente") que se aplica caso por caso dentro de cada caso de uso cuando se conecten los módulos de Clientes/Rutinas/Dietas/Progreso en esta misma entrega — dejado como comentario explícito en `api/v1/dependencies.py`.
  - **Estrategia de aislamiento de pruebas: TRUNCATE de `users` por test, no transacción-por-test.** El código de aplicación hace `commit()` explícito dentro de los routers (`register_user`, `update_user`, `delete_user`); envolver cada test en una transacción/SAVEPOINT que se revierte al final exige el patrón de SAVEPOINT + evento `after_transaction_end` de SQLAlchemy para que esos `commit()` internos no se escapen de la transacción de prueba — complejidad que no se justifica todavía con un solo módulo de integración real (`users`). Se eligió TRUNCATE (fixture `autouse` en `backend/tests/conftest.py`) por ser más simple y suficiente para este alcance; reevaluar hacia transacción-por-test si crecen los módulos con pruebas de integración reales sobre tablas relacionadas.
  - **Emails de prueba con dominio real (`@gmail.com`), no `@algo.test`.** `email-validator` (dependencia de `EmailStr` de Pydantic) valida también que el dominio tenga registros DNS/MX reales y rechaza explícitamente TLDs reservados como `.test`/`.example`/`.invalid` (RFC 2606) con el mensaje "special-use or reserved name". Se adoptó el mismo patrón que ya usa `frontend/src/mocks/data.ts` (emails de cliente con `@gmail.com`) para los correos de prueba en `backend/tests/test_auth.py`.

- **Alternativa aplicada:**
  - Nuevo paquete `backend/src/infrastructure/security/` (`password.py`, `jwt.py`) — infraestructura pura, el dominio no lo importa directo (solo `application/`).
  - `backend/src/domain/users/exceptions.py` (nuevo): `EmailAlreadyExistsError`, `InvalidRoleError`, `InvalidCredentialsError`, `UserNotFoundError`.
  - `backend/src/application/users/use_cases.py`: `RegisterUserUseCase`, `AuthenticateUserUseCase`, `ListUsersByRoleUseCase` con lógica real (antes `NotImplementedError`).
  - `backend/src/api/v1/dependencies.py` (nuevo): `get_current_user` (decodifica `Authorization: Bearer`, 401 si falta/inválido/usuario inactivo o inexistente), `require_role(*roles)` (403 si el rol no calza).
  - `backend/src/api/v1/schemas/auth.py` (nuevo): `LoginRequest`, `TokenResponse`. `backend/src/api/v1/routers/auth.py` (nuevo): `POST /auth/login`. Montado en `backend/src/api/v1/router.py`.
  - `backend/src/api/v1/routers/users.py`: reescrito completo (autorización por endpoint detallada arriba), traduce excepciones de dominio a 409/400/401/404 en español.
  - `JWT_SECRET` agregado a `.env`, `.env.example` (raíz del repo) y `docker-compose.yml` (servicio `backend`), valor de desarrollo explícitamente marcado como inseguro/no-producción.
  - `backend/tests/conftest.py` (nuevo): fixture `client` + `_clean_users_table` (TRUNCATE autouse). `backend/tests/test_auth.py` (nuevo): 7 casos (registro exitoso, email duplicado 409, login correcto, login password incorrecto 401, login usuario inexistente 401, acceso sin token 401, acceso con rol insuficiente 403) — los 7 pasan contra Postgres real.
  - Frontend: `frontend/src/api/authStorage.ts` (nuevo, clave `smartgym_auth`), `frontend/src/api/client.ts` (nuevo, wrapper de `fetch` con `Authorization` automático y `ApiError`/`isUnauthorized`), `frontend/src/hooks/useAuth.tsx` (nuevo, `AuthProvider`/`useAuth`), montado en `frontend/src/main.tsx`. `frontend/src/pages/LoginPage.tsx` conectado a `useAuth().login`, con mensaje de error en español y navegación a `/dashboard` solo si el login fue exitoso (estructura/JSX visual intacta). `frontend/src/App.tsx`: `RequireAuth` envuelve las rutas internas (`<AppShell />`), redirige a `/login` si no hay sesión. `frontend/src/components/layout/Sidebar.tsx`: el link "Cerrar sesión" ahora llama a `logout()` además de navegar (solo la función, sin tocar estilos/estructura).
  - **Verificación de cierre:** `pytest backend/tests/test_auth.py -v` -> 7/7 PASA contra Postgres real (`docker compose up -d db` + `alembic upgrade head`). Verificación manual con `curl`: login real contra un usuario insertado a mano devuelve JWT válido; ese JWT autoriza `GET /api/v1/users` (200) y `POST /api/v1/users` (201, solo con rol admin); sin token devuelve 401; password incorrecto devuelve 401. Grep de `import`/`from` en `backend/src/domain/` confirma cero referencias a `fastapi`, `jwt` o `bcrypt`. `cd frontend && npx tsc -b --force` compila sin errores nuevos.

---

### 2026-10-10 — Entrega 2, Parte A: rediseño UX/UI del panel interno (layout de 3 zonas + paleta oliva)

- **Propuesta original:** responder al feedback de la profesora ("no tiene
  buen UI/UX, necesito ver al entrar qué puedo hacer") con una revisión
  completa contra las 10 heurísticas de Nielsen (`docs/REVISION-UX.md`),
  reestructurar `AppShell` a un layout de 3 zonas (sidebar / "qué puedo
  hacer" / "resultados"), y sustituir el sistema de color del panel por
  verde oliva como color primario (no solo acento), según el punto 4 ya
  adelantado en la entrada anterior.

- **Decisión:** aprobada y construida.

- **Por qué:**
  - El hallazgo de la profesora es literal y verificable en el código de
    Entrega 1: `DashboardPage` no tenía ningún punto de entrada a una
    acción, solo números y tablas de solo lectura (ver `docs/REVISION-UX.md`,
    "Hallazgo principal"). Un layout de 3 zonas con tarjetas de acción
    verbo-primero ("Registrar cliente", no "Clientes") es la respuesta
    directa, no una reinterpretación.
  - El oliva como PRIMARIO (no "acento en reserva") es instrucción
    explícita ya registrada en la entrada "Arranque de Entrega 2" (punto
    4) — esta entrada documenta los valores finales y su verificación de
    contraste, no reabre la decisión de fondo.
  - La landing pública (`/`, scope `.landing`) queda explícitamente FUERA
    de este cambio: es la identidad de marca real de Stronger Aragón
    (verde bosque extraído del logo, ver entrada "Identidad visual real de
    marca..."), un producto distinto del panel administrativo interno. El
    oliva de esta entrada es un sistema de diseño de UI operativa, no una
    revisión de marca — mezclar ambos habría sido incorrecto para los dos.
  - El selector de rol (`RoleSwitcher.tsx`) es mock a propósito: el proceso
    de autenticación real (JWT) se construye en paralelo a esta tarea y
    todavía no expone un rol de sesión real al frontend. El switch deja
    probar las 3 variantes del Dashboard sin bloquear el rediseño en espera
    de esa integración, y queda claramente marcado como herramienta de
    desarrollo (no es parte del producto final).

- **Alternativa aplicada:**
  - **Paleta (`frontend/src/styles/theme.css`, `:root`):** nuevas variables
    canónicas `--color-primary` (`#7C8B3A`), `--color-primary-light`
    (`#9AAC4E`), `--color-primary-dark` (`#5C6B28`), `--color-primary-soft`,
    `--color-primary-text` (`#10140A`, ink para texto sobre relleno sólido
    de primario). Se agrega `--color-info`/`--color-info-soft` (`#4C8FD1`),
    estado que no existía en el sistema anterior. `--color-success`
    (`#3FB6A0`), `--color-warning` (`#E08D3C`) y `--color-danger`
    (`#D65A4A`) se recalibran para quedar separados por HUE del primario
    oliva (~71°): éxito ~169°, alerta ~30°, error ~7°, info ~210° — mismo
    criterio que ya exigía la entrada "Extensión de la identidad visual..."
    para `--color-success` vs `--color-accent`, extendido a los 4 estados.
    `--color-accent*` se CONSERVA como alias de `--color-primary*` (no se
    borra) porque el resto del árbol de archivos (StatusPill, StatNumber,
    Tabs, ClientFormPage, y las páginas de Clientes/Membresías/Rutinas/
    Dietas/Progreso) sigue leyendo ese nombre y estaba fuera del alcance de
    esta tarea — renombrar ahí habría arriesgado romper pantallas sin
    tocarlas directamente. Contraste verificado a mano (luminancia relativa
    WCAG) para cada color nuevo contra `--color-bg`: todos ≥4.9:1 (AA texto
    normal), detalle completo en el comentario de cabecera de `theme.css`.
  - **Layout (`frontend/src/components/layout/`):** `AppShell.tsx`
    reestructurado a 3 zonas reales — sidebar (izquierda), `<Outlet/>`
    (centro), columna "Resultados" opcional (derecha, solo se renderiza si
    la pantalla activa registra contenido vía el nuevo
    `AppShellContext`/`useResultsPanel`, para no forzar la zona derecha en
    pantallas que no la construyeron todavía). Sidebar y columna de
    Resultados pasan de "reflow horizontal" (Entrega 1, no colapsaba de
    verdad en móvil) a drawers reales fuera de flujo con scrim compartido,
    por debajo de 900px y 1100px respectivamente — ver
    `docs/REVISION-UX.md`, sección "Por qué drawers".
  - **Dashboard (`DashboardPage.tsx`/`.css`):** zona centro con tarjetas de
    acción (`QuickActionCard`) filtradas por rol mock — Admin/Recepción
    (registrar cliente, cobrar, ver vencimientos), Entrenador (mis
    clientes, asignar rutina/dieta), Cliente (mi rutina/dieta/progreso/
    membresía, solo lectura). Los 4 números que antes eran el elemento
    principal bajan a un bloque secundario debajo. La zona derecha
    (alertas de membresía, notificaciones recientes, última acción para
    Admin/Entrenador; resumen de membresía/progreso/entrenador para
    Cliente) usa un `client_id` de ejemplo fijo (100, Karla Jiménez)
    mientras no exista sesión real de cliente — documentado en el propio
    código como punto de integración.
  - **Componentes nuevos (`frontend/src/components/ui/`):** `EmptyState`,
    `LoadingState`, `ErrorMessage`, `ConfirmDialog`, `Breadcrumbs`, `Toast`,
    `QuickActionCard` — listos para que trabajo posterior los conecte a
    cada módulo (ninguna pantalla existente se modificó para usarlos,
    salvo el propio Dashboard). Detalle completo de cada patrón y por qué
    en `docs/REVISION-UX.md`, sección "Patrones documentados".
  - **Nada de esto tocó** `LoginPage.tsx`, `App.tsx`, `types/models.ts`,
    `mocks/data.ts`, `src/api/` ni `src/hooks/` — reservados al trabajo
    paralelo de autenticación — ni `LandingPage.css`/el scope `.landing`.

---

### 2026-10-10 — Módulo Clientes completo (RF003, bases de RF012/RF013): casos de uso reales, autorización por rol, conexión frontend↔backend

- **Propuesta original:** implementar los 4 casos de uso de dominio del
  módulo Clientes (`RegisterClientUseCase`, `AssignTrainerToClientUseCase`,
  `UpdateClientProfileUseCase`, `DeleteClientUseCase`, todos
  `NotImplementedError`), el router `clients.py` (todo `501`), resolver la
  ambigüedad de que el formulario de alta (`ClientFormPage.tsx`) registra
  datos de `User` + `ClientProfile` sin pedir password aunque el cliente sí
  necesita poder iniciar sesión después, aplicar la invariante de
  `trainer_id` como excepción de dominio propia, definir la autorización
  fina por rol de cada endpoint, y conectar las 3 pantallas de Clientes del
  frontend a la API real.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **Password del cliente nuevo: generada por el backend, no pedida en el
    formulario.** De las dos opciones delegadas (agregar campo de password
    al formulario, o generar una temporal y mostrarla una vez al staff), se
    eligió la segunda. Razón: el formulario de alta ya está construido y en
    uso (Entrega 1) sin ese campo — agregar un campo de password ahí
    obligaría al staff de recepción a inventar/comunicar una contraseña en
    el momento del alta, que es exactamente el flujo que un sistema de
    staff de gimnasio (no un registro de autoservicio) no necesita. Generar
    una temporal con `secrets` (criptográficamente segura, no `random`),
    hashearla igual que cualquier password (`hash_password`, reutilizado de
    `infrastructure/security/password.py`) y devolverla en texto claro UNA
    SOLA VEZ en la respuesta de `POST /clients` replica el patrón real de
    "alta con contraseña temporal + cambio en el primer login" usado en
    sistemas de staff, sin inventar todavía un flujo de "cambiar mi
    password" (fuera de alcance de RF003/RF013 en esta entrega). El
    frontend (`ClientFormPage.tsx`) la muestra en el aviso de éxito al
    volver a `/clientes`, con la instrucción explícita de copiarla y
    compartirla porque no se vuelve a mostrar.
  - **`RegisterClientUseCase` orquesta `UserRepository` +
    `ClientProfileRepository` a la vez** (ya autorizado en el encargo): valida
    unicidad de email igual que `RegisterUserUseCase` (mismo
    `EmailAlreadyExistsError`), valida `trainer_id` si viene en el alta con
    la misma invariante de rol que `AssignTrainerToClientUseCase` (factorizada
    en una función compartida `_ensure_trainer_role`, para no duplicar la
    regla en dos lugares), y crea `User` (role='cliente') + `ClientProfile`
    en una sola llamada. Como ningún repositorio hace `commit()` interno
    (solo `flush()`), si cualquier paso falla antes de que el router llame
    `db.commit()`, toda la operación se revierte junta — no queda un `User`
    huérfano sin `ClientProfile`.
  - **`InvalidTrainerAssignmentError` nueva, en `domain/clients/exceptions.py`
    (nuevo archivo).** Mismo patrón que `domain/users/exceptions.py`: el
    dominio no conoce HTTP: el router la traduce a `400`. Se agrega también
    `ClientNotFoundError` para los casos de `404` (antes el esqueleto no
    tenía ninguna excepción de dominio propia en este módulo).
  - **`UpdateClientProfileUseCase` delega la reasignación de `trainer_id` en
    `AssignTrainerToClientUseCase`** en vez de duplicar la validación de rol
    — tal como pedía el docstring original del router: si el payload del
    `PATCH` trae un `trainer_id` distinto al actual, se construye y ejecuta
    `AssignTrainerToClientUseCase` internamente antes de aplicar el resto de
    campos (`phone`/`birth_date`/`address`/`emergency_contact`, con el mismo
    criterio de "campo en `None` = no cambiar" que ya usa `UserUpdate` en
    `application/users/use_cases.py`).
  - **`DeleteClientUseCase` NO borra el `User` asociado.** Solo elimina la
    fila de `client_profiles` (mismo alcance del esqueleto original, que
    declaraba esta clase dependiendo únicamente de `ClientProfileRepository`).
    La cuenta de acceso (`User`, role='cliente') queda huérfana sin perfil —
    desactivarla/eliminarla es una operación distinta (`DELETE /users/{id}`,
    módulo Users) que no se mezcla aquí. Documentado como limitación
    conocida, revisable si una entrega futura pide que "eliminar cliente"
    también desactive la cuenta.
  - **Autorización por endpoint** (detalle fino, base ya sentada por
    `require_role`/`get_current_user` del módulo Auth):
    - `POST /clients`: solo `admin` (`require_role("admin")`) — alta de
      clientes es tarea de recepción/administración, nunca autoservicio.
    - `GET /clients`: `require_role("admin", "entrenador")` bloquea `cliente`
      de entrada (403). Dentro del handler, si `current_user.role ==
      "entrenador"` se fuerza `list_by_trainer(current_user.id)` — el
      `trainer_id` de query se IGNORA para ese rol (no se usa para ver la
      cartera de otro entrenador); `admin` ve todos o filtra por el
      `trainer_id` de query si lo manda.
    - `GET /clients/me` (nuevo, no pedido por el esqueleto original):
      conveniencia para `cliente` (`require_role("cliente")`), resuelve el
      perfil propio vía `client_repository.get_by_user_id(current_user.id)`
      sin que el frontend necesite conocer el `client_id` numérico para
      consultar RF013. Se declaró ANTES de `GET /clients/{client_id}` en el
      archivo — importante porque FastAPI/Starlette resuelve rutas en
      orden de declaración y `{client_id}` sin convertidor explícito
      matchea el string `"me"` antes de que FastAPI intente convertirlo a
      `int` (declarado después habría devuelto 422 en vez del perfil).
    - `GET /clients/{client_id}`: los 3 roles pueden llegar (no hay rol
      bloqueado de entrada, el filtro es por dato) — `admin` sin
      restricción; `entrenador` solo si `profile.trainer_id ==
      current_user.id` (403 si no); `cliente` solo si `profile.user_id ==
      current_user.id` (403 si no).
    - `PATCH /clients/{client_id}`: solo `admin`
      (`require_role("admin")`). RF012 (entrenador actualiza rutinas/dietas
      de SUS clientes asignados) es de los módulos Rutinas/Dietas, no de
      este perfil — el perfil de cliente (incluida la reasignación de
      entrenador) es decisión administrativa, no del propio entrenador.
    - `DELETE /clients/{client_id}`: solo `admin`.
  - **Esquema de respuesta `ClientProfileRead` ampliado con `email`,
    `full_name` (del `User` dueño del perfil) y `trainer_name` (del `User`
    entrenador, si tiene uno asignado).** Sin esto, `ClientsListPage`
    necesitaría 2-3 llamadas extra a `GET /users/{id}` por fila solo para
    mostrar nombre/correo/entrenador en la misma tabla que lista perfiles —
    el router ya tiene ambos repositorios disponibles (`_enrich()` en
    `clients.py`) y enriquecer ahí es más simple que forzar al frontend a
    des-normalizar. `ClientProfileCreate` también cambió: ya no recibe
    `user_id` (lo crea el propio caso de uso) sino `email`/`full_name`
    directos, sin campo de password (ver decisión de arriba).
  - **`backend/tests/conftest.py` extendido** para truncar también
    `client_profiles` (antes solo truncaba `users`) — aunque
    `TRUNCATE ... CASCADE` sobre `users` ya arrastraba `client_profiles` por
    la FK, se deja explícito en el propio `TRUNCATE` para que el código
    documente que este módulo también necesita aislamiento entre tests.

- **Alternativa aplicada:**
  - `backend/src/domain/clients/exceptions.py` (nuevo): `ClientNotFoundError`,
    `InvalidTrainerAssignmentError`.
  - `backend/src/infrastructure/security/password.py`: nueva función
    `generate_temporary_password()` (módulo `secrets`, 12 caracteres
    alfanuméricos).
  - `backend/src/application/clients/use_cases.py`: los 4 casos de uso con
    lógica real (antes `NotImplementedError`), más `RegisterClientResult`
    (dataclass con `client_profile` + `temporary_password`) y la función
    compartida `_ensure_trainer_role`.
  - `backend/src/api/v1/schemas/clients.py`: `ClientProfileCreate`
    reescrito (sin `user_id`, con `email`/`full_name`, sin password);
    `ClientProfileRead` con `email`/`full_name`/`trainer_name` embebidos;
    `ClientRegisterResponse` nuevo (`client` + `temporary_password`).
  - `backend/src/api/v1/routers/clients.py`: reescrito completo (los 5
    endpoints + `GET /clients/me` nuevo), autorización detallada arriba,
    traduce excepciones de dominio a 400/403/404/409 en español.
  - `backend/tests/conftest.py`: `TRUNCATE` extendido a `client_profiles`.
  - `backend/tests/test_clients.py` (nuevo): 8 casos (alta exitosa admin,
    alta rechazada no-admin 403, listado admin ve todos, listado entrenador
    ve solo los suyos, cliente accede a su propio perfil, cliente NO accede
    al perfil de otro 403, reasignar entrenador con `trainer_id` inválido
    400, eliminar como no-admin 403) — los 8 pasan contra Postgres real.
  - Frontend: `frontend/src/types/api.ts` (nuevo) documenta las formas de
    respuesta reales del backend (`ApiClientProfile`,
    `ClientRegisterPayload`, `ClientRegisterResponse`) por separado de
    `types/models.ts` (modelo lógico original, pensado para mocks), ya que
    `ClientProfileRead` del backend embebe campos que el modelo lógico de
    14 entidades no tenía.
  - `frontend/src/pages/ClientsListPage.tsx`: conectada a `GET /clients`
    real con `LoadingState`/`ErrorMessage`/`EmptyState`; columnas
    "Cliente"/"Contacto"/"Entrenador" vienen de la API real, columnas
    "Plan"/"Membresía" siguen con `clientListRows` mock (TODO explícito en
    el código, indexado por posición ya que los ids mock no corresponden a
    los reales); 401 cierra sesión (`logout()`) y redirige a `/login`, 403
    muestra mensaje claro en español.
  - `frontend/src/pages/ClientFormPage.tsx`: sección "Datos del cliente"
    (incluido el selector de entrenador, ahora alimentado por
    `GET /users?role=entrenador` real en vez del mock `trainers` — un
    `trainer_id` mock casi nunca existe en la base real, así que mantener el
    mock ahí habría roto el alta en la práctica) conectada a `POST /clients`
    real; email duplicado (409) se muestra como error del campo correo, no
    un toast genérico; el aviso de éxito es honesto (solo confirma que el
    cliente se registró y muestra la password temporal, nunca menciona que
    el pago se registró); "Membresía y pago inicial" sigue sin conectar,
    con el hint de la tarjeta actualizado para decirlo explícitamente.
  - `frontend/src/pages/ClientDetailPage.tsx`: header + pestaña "Perfil"
    conectados a `GET /clients/{id}` real (con `LoadingState`/
    `ErrorMessage`, 404 propio, 403 con mensaje claro, 401 redirige a
    login); las 5 pestañas restantes (Membresía/Pagos/Rutina/Dieta/Progreso)
    quedan con mocks y un comentario TODO explícito cada una. No se agregó
    un botón de eliminar cliente aquí — no existía en el alcance visual
    previo y agregarlo sin que el resto del flujo de "archivar/reactivar
    cliente" esté definido habría sido inventar una acción a medias.
  - **Verificación de cierre:** `pytest backend/tests/test_clients.py -v` ->
    8/8 PASA; `pytest backend/tests/ -v` -> 19/19 PASA (incluye los 7 de
    Auth y los 4 de salud/documentación, sin regresiones). Grep de
    `import`/`from` en `backend/src/domain/` confirma cero referencias a
    `sqlalchemy`, `fastapi`, `bcrypt` o `jwt`. `cd frontend && npx tsc -b` y
    `npm run build` compilan sin errores. Verificación manual con `curl`
    contra el stack completo (`docker compose up -d db backend`): login
    admin -> `POST /clients` (201, devuelve password temporal) -> `GET
    /clients` (admin ve el cliente nuevo) -> `GET /clients/{id}` (200) ->
    login entrenador sin ese cliente asignado -> `GET /clients/{id}` del
    cliente ajeno devuelve 403 -> `GET /clients` del entrenador devuelve `[]`
    -> login del cliente con la password temporal -> `GET /clients/me`
    devuelve su propio perfil -> `GET /clients` del cliente devuelve 403.

---

### 2026-10-11 — Módulo Planes y Membresías completo (RF004): casos de uso reales, autorización por rol, conexión frontend↔backend

- **Propuesta original:** implementar `AssignMembershipUseCase` (el otro caso de uso del esqueleto, `DetectExpiringMembershipsUseCase`, es RF006 y pertenece al módulo "Vencimientos/Notificaciones", posterior a Pagos en el orden fijo — queda intencionalmente sin tocar), el CRUD de `MembershipPlan`, el router `memberships.py` (todo `501`), la autorización fina por endpoint, y conectar `MembershipsPage.tsx` + la pestaña "Membresía" de `ClientDetailPage.tsx` a la API real.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **`AssignMembershipUseCase` orquesta `ClientProfileRepository` además de los dos repositorios de Memberships** (mismo patrón ya usado por `RegisterClientUseCase` en el módulo Clientes): valida que el cliente exista (reusa `ClientNotFoundError` de `domain.clients.exceptions`, no se duplica un segundo tipo para el mismo caso real), que el plan exista (`MembershipPlanNotFoundError`, nuevo en `domain/memberships/exceptions.py`), que `status` esté en `ESTADOS_MEMBRESIA_VALIDOS` (`InvalidMembershipStatusError`), y que `end_date` sea estrictamente posterior a `start_date` (`InvalidMembershipDateRangeError`).
  - **Plan CRUD sin caso de uso dedicado:** crear/listar un plan de catálogo no tiene ninguna invariante de negocio propia (a diferencia de asignar una membresía) — el router habla directo con `MembershipPlanRepository`. Si una entrega futura agrega una regla real (ej. "no borrar un plan con membresías activas"), ahí sí amerita un caso de uso propio.
  - **Autorización:** `POST /membership-plans` solo `admin` (dato de catálogo/precio, decisión administrativa); `GET /membership-plans` cualquier rol autenticado (catálogo no sensible, útil para que entrenador/cliente vean opciones); `POST /memberships` solo `admin` (asignar/cobrar es decisión administrativa, no del entrenador ni del propio cliente); `GET /memberships` y `GET /memberships/{id}` con ownership por dato igual que `GET /clients/{id}` del módulo anterior (entrenador solo sus clientes asignados, resuelto vía `ClientProfileRepository.list_by_trainer`; cliente solo la suya, vía `get_by_user_id`); `PATCH /memberships/{id}` (cambiar status) solo `admin` — hoy cualquier cambio de estado es manual porque RF006 (detección automática) todavía no existe. `MembershipRepository` no expone `list_all`, así que "ver todo" para `admin` se resuelve agregando `list_by_client` sobre todos los `client_id` reales — suficiente para el alcance de este proyecto.
  - **No hay seed de los 3 planes reales (Básica/VIP/Premium) en ninguna migración** — la base arranca sin ningún plan creado; el frontend debe manejar bien ese catálogo vacío (resuelto con `EmptyState` + alta inline para `admin`). El seed de datos realistas (B4 del encargo) es una tarea aparte, todavía no construida.
  - **`MembershipRead` NO embebe nombre de cliente/plan** (a diferencia de `ClientProfileRead`, que sí embebe `full_name`/`trainer_name` desde el módulo Clientes) — se decidió no ampliar el schema aquí porque el frontend ya necesitaba cargar `GET /clients` y `GET /membership-plans` para otros fines (selector de plan, columna de cliente), así que combinar en memoria con un `Map` evita tanto el N+1 como un schema más acoplado de lo necesario.
  - **`MembershipPlanRead.price` llega como string** (`Decimal` de Pydantic v2 se serializa `"399.00"`, no `399`) — detectado antes de que causara un bug real de formato; el frontend convierte con `Number(plan.price)` en todos los puntos donde se usa en cálculos o `toLocaleString`.
  - **Criterio para elegir "la" membresía de un cliente cuando hay varias** (`pickCurrentMembership` en `frontend/src/utils/membership.ts`, compartido por `ClientDetailPage` y `ClientsListPage`): prioriza la que tenga `status === 'activa'`; si ninguna está activa, la de `end_date` más lejana (la más reciente/relevante del historial).
  - **Alta de membresía vive en `ClientDetailPage`, no en el formulario combinado de alta de cliente** (`ClientFormPage.tsx` sigue sin conectar su sección de membresía/pago, ver entrada del módulo Clientes) — mezclar ambos módulos ahí habría significado adelantar trabajo de Pagos fuera de orden. La pestaña "Membresía" del detalle, cuando el cliente no tiene ninguna, ofrece un `EmptyState` con la acción "Asignar membresía" (solo visible para `admin`, acorde a la autorización real del backend) con fecha de vencimiento calculada automáticamente a partir de `duration_days` del plan elegido.

- **Alternativa aplicada:**
  - Backend: `backend/src/domain/memberships/exceptions.py` (nuevo), `backend/src/application/memberships/use_cases.py` (`AssignMembershipUseCase` real, `DetectExpiringMembershipsUseCase` intencionalmente intacto), `backend/src/api/v1/routers/memberships.py` (reescrito, los 6 endpoints del esqueleto salvo `/expiring`), `backend/tests/conftest.py` (`TRUNCATE` extendido a `membership_plans`/`memberships`), `backend/tests/test_memberships.py` (nuevo, 10 casos). Resultado: `pytest tests/test_memberships.py` → 10/10 PASA; `pytest tests/` completo → 29/29 PASA, sin regresiones. Dominio verificado limpio de imports de infraestructura.
  - Frontend: `frontend/src/types/api.ts` ampliado (`ApiMembershipPlan`, `ApiMembership`, payloads de creación); `frontend/src/utils/membership.ts` (`pickCurrentMembership`); `frontend/src/pages/MembershipsPage.tsx`/`.css` reescrita (catálogo + tabla + alta de plan inline); `frontend/src/pages/ClientDetailPage.tsx`/`.css` (pestaña Membresía + asignación); `frontend/src/pages/ClientsListPage.tsx` (columna Plan/Membresía ya no usa el mock `clientListRows`, TODO cerrado). `npx tsc -b` y `npm run build` sin errores. Verificado en navegador de punta a punta: alta de plan → alta de cliente → asignación de membresía desde el detalle → reflejada correctamente en la tabla de `/membresias` y en el header/pestaña del detalle del cliente, sin errores de consola, incluyendo la verificación del `EmptyState` de catálogo vacío y de cliente sin membresía antes de crear nada.

---

### 2026-10-11 — Módulo Pagos completo (RF005): defecto de `registered_by` corregido, casos de uso reales, ownership por dato encadenado (solo backend)

- **Propuesta original:** implementar `RegisterPaymentUseCase` y `ListPaymentsByMembershipUseCase` (ambos `NotImplementedError`), el router `payments.py` (los 3 endpoints en `501`), corregir el defecto de seguridad de `PaymentCreate.registered_by`, y la autorización fina por endpoint — siguiente módulo en el orden fijo después de Planes y Membresías. Tarea delimitada a backend; la conexión del frontend a estos endpoints queda para un trabajo posterior.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **Defecto de diseño corregido, no ambigüedad: `PaymentCreate.registered_by: int` se quita del payload.** El esqueleto original dejaba que el CLIENTE HTTP mandara en el body quién registró el pago — eso permite falsificar la autoría de cualquier pago (ej. un entrenador autorizado a llamar el endpoint podría atribuir el registro a un admin distinto, o un admin podría atribuírselo a otro). No es una decisión de diseño defendible bajo ningún ángulo, así que se corrige igual que se corrigió en su momento el bug real de los endpoints `DELETE` sin `response_model` (ver entrada "Bug real en endpoints DELETE") — un defecto, no una lectura alternativa válida. El router (`register_payment`) rellena `registered_by` siempre con `current_user.id` (el admin autenticado que hace la petición vía `get_current_user`), nunca con un valor leído del body. La prueba `test_registrar_pago_ignora_registered_by_inyectado_en_el_body` confirma que aunque el test intente mandar `registered_by` de otro admin en el JSON, Pydantic lo descarta silenciosamente (campo no declarado en el schema) y la respuesta trae el id del admin que realmente autenticó la llamada.
  - **`RegisterPaymentUseCase` valida `membership_id`/`method`/`status` en el dominio, sin confiar en que Pydantic ya los tipó.** Mismo criterio que `AssignMembershipUseCase` con `ESTADOS_MEMBRESIA_VALIDOS`: la capa de transporte (`Literal` en el schema) es una primera barrera, pero el caso de uso repite la validación contra `METODOS_PAGO_VALIDOS`/`ESTADOS_PAGO_VALIDOS` del propio dominio (`domain/payments/entities.py`) — si en el futuro otro llamador invoca el caso de uso sin pasar por la API HTTP (ej. un script interno, un job batch), la regla de negocio sigue protegida igual.
  - **`MembershipNotFoundError` reusada de `domain/memberships/exceptions.py`, no duplicada.** `domain/payments/exceptions.py` (nuevo) solo agrega `InvalidPaymentMethodError`/`InvalidPaymentStatusError`, que son exclusivas de este módulo — mismo criterio ya aplicado por `AssignMembershipUseCase` reusando `ClientNotFoundError` del módulo Clientes.
  - **Ownership por dato encadenado un nivel más profundo que `memberships.py`:** el dueño real de un `Payment` no es directo — hay que resolver `Payment.membership_id` → `Membership.client_id` → `ClientProfile` para saber si pertenece al entrenador/cliente que hace la petición. Se factorizó `_resolve_own_membership_ids` en `routers/payments.py` (devuelve `None` para `admin` sin restricción, o la lista de `membership_id` propios para `entrenador`/`cliente`, encadenando `ClientProfileRepository.list_by_trainer`/`get_by_user_id` → `MembershipRepository.list_by_client`), reusada tanto por el listado como por `GET /payments/{id}` — mismo principio de "un solo lugar para la regla de ownership" que ya aplicaba `_ensure_access_to_membership` en el módulo anterior, adaptado a que aquí la comparación es contra una lista de ids (no un solo `ClientProfile`) porque un `Payment` se filtra por membresía, no por perfil directo.
  - **Autorización por endpoint:**
    - `POST /payments`: solo `admin` — registrar un pago es decisión administrativa/financiera, mismo criterio que el alta de cliente y la asignación de membresía en los módulos anteriores.
    - `GET /payments` (listado, filtro opcional `membership_id` en query) y `GET /payments/{id}`: los 3 roles pueden llegar, el filtro es por dato (ownership encadenado, ver arriba) — `admin` ve todos o filtra por `membership_id` si lo manda; `entrenador` solo pagos de membresías de sus clientes asignados (un `membership_id` de query que no sea uno de los suyos se ignora, igual que ya hacía `list_memberships`); `cliente` solo los suyos.
    - No se agregó `PATCH`/`DELETE /payments/{id}` — no estaban en el esqueleto original y no forman parte de este encargo.
  - **`PaymentRepository` (ya implementado desde el esqueleto) se usó tal cual, sin tocar** — no expone `list_all`, así que "ver todo" para `admin` se resuelve igual que en `memberships.py`: agregando `list_by_membership` sobre todos los `membership_id` reales.
  - **`backend/tests/conftest.py` no necesitó extender el `TRUNCATE`.** A diferencia de `membership_plans` (que sí necesitó truncarse explícito por no tener FK hacia la cadena `users`→`client_profiles`), `payments.membership_id` tiene `ON DELETE CASCADE` hacia `memberships.id`, que a su vez tiene `ON DELETE CASCADE` hacia `client_profiles.id` — truncar `users`/`client_profiles` con `CASCADE` ya arrastra `memberships` y, en cadena, `payments`. Verificado al correr la suite completa sin agregar la tabla al `TRUNCATE`: sin colisión de datos entre tests.

- **Alternativa aplicada:**
  - `backend/src/domain/payments/exceptions.py` (nuevo): `InvalidPaymentMethodError`, `InvalidPaymentStatusError` (reusa `MembershipNotFoundError` de `domain.memberships.exceptions`).
  - `backend/src/application/payments/use_cases.py`: `RegisterPaymentUseCase` y `ListPaymentsByMembershipUseCase` con lógica real (antes `NotImplementedError`).
  - `backend/src/api/v1/schemas/payments.py`: `PaymentCreate` sin `registered_by` (defecto corregido, documentado en el propio docstring de la clase). `PaymentRead` sin cambios (sigue devolviendo `registered_by`, ahora siempre fiel al admin autenticado).
  - `backend/src/api/v1/routers/payments.py`: reescrito completo (los 3 endpoints del esqueleto), `_resolve_own_membership_ids` compartido entre listado y detalle, traduce excepciones de dominio a 400/403/404.
  - `backend/tests/test_payments.py` (nuevo): 7 casos (registro exitoso con `registered_by` correcto, registro que ignora un `registered_by` inyectado en el body, `membership_id` inexistente 404, registro como no-admin 403, listado admin ve todos, listado entrenador ve solo los suyos, cliente accede a su propio pago pero no al de otro 403) — los 7 pasan contra Postgres real.
  - **Verificación de cierre:** `pytest backend/tests/test_payments.py -v` → 7/7 PASA; `pytest backend/tests/ -v` completo → 36/36 PASA (29 previas + 7 nuevas), sin regresiones. Grep de `import`/`from` en `backend/src/domain/` confirma cero referencias a `sqlalchemy`, `fastapi`, `bcrypt` o `jwt`. Tarea delimitada a backend — `frontend/` no se tocó; la conexión de pantallas a estos endpoints queda para un trabajo posterior.

---

### 2026-10-11 — Módulo Pagos: conexión de frontend y cierre del ciclo de alta de cliente (RF005)

- **Propuesta original:** conectar la pestaña "Pagos" de `ClientDetailPage.tsx` a la API real, y — más importante — cerrar el ciclo que quedó pendiente explícitamente desde el módulo Clientes y otra vez desde Membresías: la sección "Membresía y pago inicial" de `ClientFormPage.tsx`, con el hint "todavía no conectado a un backend real", ahora que ambos módulos (Membresías y Pagos) ya existen.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **Pestaña "Pagos" depende de que el cliente ya tenga membresía.** RF005 liga el pago a una membresía (`Payment.membership_id`), así que si el cliente no tiene ninguna, la pestaña muestra un `EmptyState` que dirige a la pestaña "Membresía" en vez de simular un estado vacío de pagos sin explicar la causa real.
  - **El plan en `ClientFormPage.tsx` es explícitamente opcional.** Se agregó una opción "Sin membresía por ahora (asignar después)", preseleccionada por default — antes el primer plan mock quedaba preseleccionado de fábrica, lo cual habría forzado una asignación no solicitada ahora que la sección sí persiste de verdad. El hint de la sección se reescribió para decir esto explícitamente ("opcional... si no eliges un plan, el cliente se registra sin membresía").
  - **Encadenamiento de 3 llamadas (`POST /clients` → `POST /memberships` → `POST /payments`) desde el frontend, sin una transacción atómica de backend que las una.** Se decidió así porque cada módulo ya expone su propio endpoint bien delimitado (alcance de cada entrega anterior) y un caso de uso compuesto en el backend habría mezclado las fronteras de los tres módulos de dominio (Users/Clients, Memberships, Payments) solo para este único flujo de UI. El costo de esta decisión es que el paso 1 (alta de cliente), si tiene éxito, nunca se revierte automáticamente si el 2 o el 3 fallan después.
  - **Mensaje de cierre honesto sobre fallos parciales.** Si el cliente se crea pero la membresía o el pago fallan, el aviso final no dice "ocurrió un error" de forma genérica (induciría a pensar que no se guardó nada) ni "todo salió bien" — construye el mensaje de forma incremental según qué pasos realmente se completaron, y dirige al admin a terminar manualmente lo que falte desde el detalle del cliente (pestaña Membresía o Pagos, según el paso que haya fallado).
  - **`addDaysIso` centralizada en `frontend/src/utils/membership.ts`.** Vivía duplicada en `ClientDetailPage.tsx` (para calcular `end_date` al asignar membresía desde el detalle); ahora también la usa `ClientFormPage.tsx` para el mismo cálculo al elegir un plan en el alta combinada — un solo lugar para la fórmula `fecha_inicio + duration_days`.

- **Alternativa aplicada:**
  - `frontend/src/types/api.ts`: `ApiPaymentMethod`, `ApiPaymentStatus`, `ApiPayment`, `PaymentCreatePayload` (mismo patrón que los tipos de Membresías; `amount` tipado `string` porque el backend serializa el `Decimal` así, igual que `MembershipPlanRead.price`).
  - `frontend/src/pages/ClientDetailPage.tsx`/`.css`: pestaña "Pagos" conectada (historial real + alta de pago solo para `admin`, con el mismo patrón de validación en línea del resto del proyecto).
  - `frontend/src/pages/ClientFormPage.tsx`: sección de membresía/pago conectada completa, selector de plan alimentado por `GET /membership-plans` real (ya no mock), opción "sin membresía" explícita, manejo de fallo parcial como se describe arriba.
  - **Verificación de cierre (en navegador, stack real vía `docker compose`):** alta de cliente CON plan (VIP) → confirmado que se crearon los 3 registros reales (cliente, membresía activa, pago) y que el aviso de éxito los menciona los tres; alta de cliente SIN plan → confirmado que no se intenta crear membresía/pago de más; pago adicional registrado desde la pestaña "Pagos" de un cliente con historial existente → reflejado correctamente en la tabla. Sin errores en consola del navegador en ningún caso (pestaña nueva, sin ruido de ejecuciones anteriores).

---

### 2026-10-11 — Módulo Vencimientos/Notificaciones completo (RF006, solo backend): `DetectExpiringMembershipsUseCase`, trigger manual sin scheduler, deduplicación heurística de "por vencer"

- **Propuesta original:** implementar `DetectExpiringMembershipsUseCase` (dejado intencionalmente sin terminar en el módulo Planes y Membresías), `NotifyUserUseCase`/`ListUserNotificationsUseCase` del módulo Notifications (sin tocar `RecordAuditEventUseCase`, que pertenece al módulo Bitácora, el último en el orden fijo), y los 4 endpoints correspondientes (`POST /memberships/detect-expiring` nuevo, `GET /memberships/expiring`, `GET /notifications/users/{user_id}`, `POST /notifications/{notification_id}/read`). Siguiente módulo en el orden fijo después de Pagos. Tarea delimitada a backend.

- **Decisión:** aprobada y construida.

- **Por qué / detalle de cada sub-decisión:**
  - **Sin scheduler real (decisión ya anticipada, aquí solo se ejecuta).** Este stack escolar no tiene job runner/cron. En un despliegue real, `DetectExpiringMembershipsUseCase` correría como un job diario; aquí se expone como una acción que el `admin` dispara manualmente vía `POST /memberships/detect-expiring`. Documentado en el propio docstring de la clase para que quede explícito en el código, no solo aquí.
  - **"Por vencer" sigue sin persistirse como status, respetando el principio ya documentado en `frontend/src/utils/membership.ts`.** El único status que se persiste por una transición real es `"vencida"` (membresía `activa` con `end_date` ya pasada). Una membresía "por vencer" (activa, `end_date` dentro de la ventana `days_ahead`) nunca cambia su `status` — sigue `"activa"`, y "por vencer" se sigue calculando al vuelo a partir de `end_date` vs. la fecha actual.
  - **Idempotencia asimétrica entre los dos casos, y por qué:**
    - Caso "vencida": idempotente de forma natural. La consulta subyacente filtra por `status == "activa"`; en cuanto una membresía pasa a `"vencida"`, deja de aparecer en corridas futuras. Cero lógica de deduplicación adicional.
    - Caso "por vencer": NO es idempotente por sí solo (la membresía sigue `"activa"` y seguiría apareciendo en cada corrida mientras esté dentro de la ventana), así que se deduplica a mano: antes de notificar, se revisa si ya existe una `Notification` tipo `membresia_por_vencer`, no leída, para ese usuario, creada dentro de los últimos `days_ahead` días. Esta deduplicación es deliberadamente heurística (por `type + user_id + ventana de tiempo`, NO por un vínculo directo a la membresía) porque `Notification` no tiene `membership_id` en su esquema actual — agregar esa columna ahora habría significado tocar el modelo de datos para un módulo que ya no está en el backlog de alineación (B0). Limitación conocida y aceptada para el alcance de esta entrega: dos membresías distintas por vencer del mismo usuario en la misma ventana solo generarían una notificación combinada, no diferenciada. Si una entrega futura necesita trazabilidad 1:1, el camino correcto es agregar `Notification.membership_id` (nullable, ya que `pago_registrado`/`rutina_asignada`/etc. no la necesitan).
  - **`NotifyUserUseCase` se usa por composición dentro de `DetectExpiringMembershipsUseCase`, no se llama directo desde un endpoint HTTP.** No se pidió un `POST /notifications` genérico en esta entrega — el único productor real de notificaciones hoy es la detección de vencimientos. `DetectExpiringMembershipsUseCase` recibe un `NotifyUserUseCase` ya construido (no el repositorio crudo) para que la validación de `type` contra `TIPOS_NOTIFICACION_VALIDOS` (nueva, `domain/notifications/exceptions.py` → `InvalidNotificationTypeError`) se aplique en un solo lugar, mismo criterio defensivo que ya usan `AssignMembershipUseCase`/`RegisterPaymentUseCase` sobre sus propios enums-por-CHECK (el schema Pydantic ya tipa `type` como `Literal`, pero el dominio no confía ciegamente en la capa de transporte).
  - **Una sola consulta al repositorio (`list_expiring_before(cutoff)`, ya existía en la interfaz desde el esqueleto) cubre ambos casos.** `cutoff = hoy + days_ahead` trae tanto las ya vencidas (`end_date < hoy`) como las por vencer (`hoy <= end_date <= cutoff`); el caso de uso separa ambos grupos en Python en vez de pedir dos queries. Resultado equivalente, una sola llamada a infraestructura.
  - **`GET /memberships/expiring` es de solo lectura y usa EXACTAMENTE el criterio de `frontend/src/utils/membership.ts`** (`status == "vencida"` ya persistido, O `status == "activa"` con `end_date` dentro de `days_ahead`) — por diseño, esto significa que una membresía `activa` con `end_date` ya pasado pero que *nunca* pasó por `POST /memberships/detect-expiring` (ni por un `PATCH` manual) NO aparece aquí como vencida: el endpoint lee el status tal como está persistido, no recalcula "vencida" de forma independiente. Esto es consistente con que el frontend tampoco lo hace — es una limitación conocida y heredada a propósito del criterio ya aprobado, no un bug nuevo introducido aquí.
  - **Ownership de `GET /memberships/expiring`:** se decidió permitir también a `cliente` (ve solo su propia membresía), no restringir a `admin`/`entrenador`. Aunque un cliente en la práctica solo tiene una membresía y el endpoint le aporta poco, ya puede ver el mismo dato (incluido si está vencida/por vencer, vía `getMembershipDisplayStatus` en su propio cliente de frontend) a través de `GET /memberships` y `GET /memberships/{id}` — bloquear específicamente este endpoint para `cliente` habría sido una inconsistencia arbitraria frente a esos dos, que ya usan el mismo patrón de ownership por dato.
  - **Ownership de `POST /memberships/detect-expiring`:** solo `admin`, igual que `PATCH /memberships/{id}` — es una acción que muta datos (cambia `status`, crea `Notification`), nunca algo que un `entrenador`/`cliente` dispara "en su propio nombre".
  - **Ownership de `GET /notifications/users/{user_id}` y `POST /notifications/{notification_id}/read`:** el propio usuario puede ver/marcar sus notificaciones; `admin` puede ver/marcar las de cualquiera (soporte). Cualquier otro caso → 403 (ver/marcar); 404 si la notificación no existe (marcar).
  - **Sin caso de uso dedicado para "marcar como leída".** Es un toggle simple de `is_read` sin ninguna invariante de negocio propia — mismo criterio ya aplicado al alta/listado de `MembershipPlan` en `routers/memberships.py` (sin caso de uso dedicado cuando no hay regla real que proteger). El router llama directo a `NotificationRepository.get_by_id`/`mark_as_read`.
  - **`backend/tests/conftest.py` no necesitó extender el `TRUNCATE` a `notifications`, a diferencia de lo anticipado.** Se verificó el modelo real (`infrastructure/db/models/notifications.py`): `notifications.user_id` SÍ tiene FK directa hacia `users.id` con `ON DELETE CASCADE` — distinto del caso de `membership_plans` (que no tiene ninguna FK hacia la cadena `users`→`client_profiles`). `TRUNCATE ... CASCADE` sobre `users` ya arrastra `notifications` automáticamente (Postgres cascada el `TRUNCATE` sobre cualquier tabla con FK hacia una tabla truncada, sin importar su regla de `ON DELETE`). Documentado en el propio `conftest.py`; verificado corriendo la suite completa dos veces seguidas sin colisiones de datos.

- **Alternativa aplicada:**
  - `backend/src/domain/notifications/exceptions.py` (nuevo): `InvalidNotificationTypeError`, `NotificationNotFoundError`.
  - `backend/src/application/notifications/use_cases.py`: `NotifyUserUseCase` y `ListUserNotificationsUseCase` con lógica real; `RecordAuditEventUseCase` sin tocar (`NotImplementedError`, módulo Bitácora).
  - `backend/src/application/memberships/use_cases.py`: `DetectExpiringMembershipsUseCase` con lógica real (recibe `MembershipRepository`, `ClientProfileRepository` y `NotifyUserUseCase`).
  - `backend/src/api/v1/routers/memberships.py`: `_resolve_memberships_for_user` factorizado de `list_memberships` (reusado también por `/expiring`); nuevo `POST /memberships/detect-expiring` y `GET /memberships/expiring` implementado (ambos declarados antes de `/{membership_id}`, mismo motivo ya documentado para rutas estáticas vs. parametrizadas).
  - `backend/src/api/v1/routers/notifications.py`: `GET /notifications/users/{user_id}` y `POST /notifications/{notification_id}/read` implementados; `audit_router`/`GET /audit-logs` sin tocar (501, módulo Bitácora).
  - `backend/tests/conftest.py`: comentario nuevo documentando por qué `notifications` NO necesitó agregarse al `TRUNCATE` explícito (cascada automática vía FK).
  - `backend/tests/test_notifications.py` (nuevo): 7 casos (detección marca vencida + notifica al usuario correcto; detección de por-vencer notifica sin cambiar status; detección repetida de por-vencer no duplica; `POST /detect-expiring` como no-admin → 403; `GET /expiring` refleja vencidas/por-vencer sin depender del POST; `GET /notifications/users/{id}` de otro usuario sin ser admin → 403; marcar notificación como leída) — los 7 pasan contra Postgres real.
  - **Verificación de cierre:** `pytest backend/tests/test_notifications.py -v` → 7/7 PASA; `pytest backend/tests/ -v` completo → 43/43 PASA (36 previas + 7 nuevas), sin regresiones. Grep de `import`/`from` en `backend/src/domain/` confirma cero referencias a `sqlalchemy`, `fastapi`, `bcrypt` o `jwt` (las únicas coincidencias de texto son docstrings que mencionan esas palabras, no imports reales). Prueba manual con `httpx` dentro del contenedor `backend` (sin `curl` disponible en la imagen): se creó una membresía con `end_date` 5 días en el pasado, se corrió `POST /memberships/detect-expiring` como admin, y se confirmó tanto el cambio de `status` a `"vencida"` en la respuesta como la `Notification` tipo `membresia_vencida` generada para el `user_id` correcto vía `GET /notifications/users/{id}`. Tarea delimitada a backend — `frontend/` no se tocó.

---
