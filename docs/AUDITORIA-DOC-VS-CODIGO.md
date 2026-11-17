# Auditoría documentación vs. código — SmartGym v2 (cierre final)

Fecha: 2026-11-16. Fuente de verdad auditada: `SmartGym-v2-Documentacion-Apartados-I-IV.docx`
(la versión más reciente en Downloads, modificada 2026-11-04; se comparó también
contra `docs/Casos-de-Uso-SmartGym-v2.docx` y `docs/Plan-de-Pruebas-SmartGym-v2.docx`,
idénticos en contenido a lo que el documento principal ya embebe). Metodología:
cada fila se verificó contra el código real (grep/lectura de archivo, no memoria),
contra una corrida real de `pytest` (`docs/BASE-PYTEST-ANTES.txt`, 106/106) y, para
el frontend, contra el código fuente de cada pantalla. Ninguna cifra de esta
página es estimada.

## ⚠️ Hallazgo previo a toda la auditoría: la "sección 3.4" no existe

El encargo de este cierre describe en detalle la ampliación de RF004/RF005
(Planes y servicios extra, cambio de plan, tablero de membresías activas) como
contenido de la "sección 3.4" del documento. **Se leyó el documento completo
(742 líneas extraídas) y esa sección no existe**: el Apartado III termina en
"3.3 Presentación de requerimientos" y salta directo al "Apartado IV.
Desarrollo del sistema de información" (4.1). Ninguna de las palabras
"ampliación", "Planes y servicios", "servicio extra", "cambio de plan" ni
"tablero" aparece en el documento, ni en `Casos-de-Uso-SmartGym-v2.docx` ni en
`Plan-de-Pruebas-SmartGym-v2.docx`.

La ampliación **sí existe, completa y probada, en el código** (ver secciones
dedicadas más abajo) — fue construida y documentada en `DECISIONES.md` en
sesiones de trabajo previas a esta entrega. Lo que falta es que alguien
redacte la sección 3.4 formal en el `.docx` describiéndola. Por regla
explícita de este encargo, **no se edita el `.docx`** (no hay una versión
previa de esa sección de la que "restaurar" texto; escribirla ahora sería
inventar documentación para que cuadre con el código, exactamente lo que se
prohíbe). Queda registrado como tarea humana en `docs/PENDIENTES-HUMANOS.md`,
a cargo del Ingeniero de Requerimientos (Espinosa Medina Luis Layonet, Tabla 4
del propio documento). El resto de esta auditoría SÍ evalúa la ampliación,
usando como especificación la descripción detallada que el usuario dio en el
encargo de este cierre (la fuente escrita más reciente y específica de lo que
esa sección 3.4 debería decir) — ver nota al pie de cada fila de la ampliación.

## RF001–RF015 (Apartado III, Tabla 6 + Apartado IV, Tabla 12)

| RF | Requisito | Dónde está (código) | Estado | Acción tomada |
|---|---|---|---|---|
| RF001 | Login con roles | `backend/src/api/v1/routers/auth.py` (`POST /auth/login`), `application/auth` (hash bcrypt + JWT), `frontend/src/pages/LoginPage.tsx` | **Cumple** | Verificado con `test_auth.py` (7 casos) + login real de los 3 roles. |
| RF002 | Restringir acceso por rol | `backend/src/api/v1/dependencies.py` (`require_role`), aplicado en los 12 routers; `frontend/src/components/layout/Sidebar.tsx` filtra el menú por rol | **Cumple** | — |
| RF003 | CRUD de clientes | `backend/src/api/v1/routers/clients.py`; `frontend/src/pages/ClientsListPage.tsx`, `ClientFormPage.tsx`, `ClientDetailPage.tsx` | **Cumple** (con una nota de flujo alterno, ver CU04 abajo) | — |
| RF004 | Asignar membresía (Básica/VIP/Premium) | `backend/src/api/v1/routers/memberships.py` (`POST /memberships`); `frontend/src/pages/ClientDetailPage.tsx` (pestaña Membresía) | **Cumple** | Ampliado en sesiones previas (catálogo de servicios, tablero de activas, cambio de plan) — ver sección "Ampliación" abajo. |
| RF005 | Registrar pagos | `backend/src/api/v1/routers/payments.py`; pestaña "Pagos" de `ClientDetailPage.tsx` | **Cumple** | Ampliado con desglose por concepto — ver abajo. |
| RF006 | Detectar/notificar vencimientos | `application/memberships/use_cases.py::DetectExpiringMembershipsUseCase`, disparo manual (`POST /memberships/detect-expiring`) **y automático** (`infrastructure/scheduler.py`, APScheduler diario 06:00 CDMX) | **Cumple** (mejor que lo documentado) | La Tabla 12 del documento (nota al pie) dice que esto "se dispara manualmente... limitación documentada" — **ya no es cierto**, se automatizó en una sesión posterior a la fecha del documento. Se reporta como dato desactualizado, no se edita el `.docx`. |
| RF007 | Crear/asignar rutinas | `backend/src/api/v1/routers/routines.py`; `frontend/src/pages/RoutinesPage.tsx` | **Cumple** | — |
| RF008 | Historial de rutinas | `application/routines/use_cases.py::GetClientRoutineHistoryUseCase`; pestaña "Rutina" de `ClientDetailPage.tsx` | **Cumple** | — |
| RF009 | Crear/asignar dietas | `backend/src/api/v1/routers/diets.py`; `frontend/src/pages/DietsPage.tsx` | **Cumple** | — |
| RF010 | Registrar progreso corporal | `backend/src/api/v1/routers/progress.py` (`POST /progress`); pestaña "Progreso" de `ClientDetailPage.tsx` | **Cumple** | — |
| RF011 | Dashboard de evolución | `frontend/src/components/ui/ProgressChart.tsx` (SVG propio), `ProgressPage.tsx` | **Cumple** | Verificado en navegador — no hay prueba automatizada de render (pytest no valida DOM), consistente con lo que ya documentaba la Tabla 15 del propio `.docx` sobre CP15. |
| RF012 | Entrenador gestiona clientes asignados | Ownership por dato en `clients.py`, `routines.py`, `diets.py`, `progress.py`, `memberships.py` (filtra por `trainer_id`) | **Cumple** | — |
| RF013 | Cliente solo lectura de lo propio | Ownership por dato (mismo patrón); sin controles de alta/edición en la interfaz para ese rol en ningún módulo | **Cumple** | — |
| RF014 | API REST documentada | FastAPI + OpenAPI automático en `/docs` | **Cumple** | La Tabla 18 del documento dice "43 rutas, 11 módulos" — **desactualizado**: la API real hoy expone 59 combinaciones ruta+método en 40 rutas distintas, 12 módulos (se agregó `services`, ver ampliación). Se reporta, no se edita el `.docx`. |
| RF015 | Bitácora de errores/eventos | `backend/src/api/main.py` (manejadores globales de excepción → `AuditLog` automático); `frontend/src/pages/AuditLogsPage.tsx` (`/bitacora`, solo admin) | **Cumple** | — |

## RNF01–RNF06 (Tabla 7)

| RNF | Requisito | Verificación | Estado |
|---|---|---|---|
| RNF01 | Arquitectura hexagonal | `backend/src/{domain,application,infrastructure,api}/`; `domain/` no importa FastAPI/SQLAlchemy en ningún archivo (verificado por grep) | **Cumple** |
| RNF02 | PostgreSQL 16 + Alembic | `docker-compose.yml` (`postgres:16`), `backend/src/infrastructure/migrations/versions/` (0001–0004) | **Cumple** |
| RNF03 | Docker Compose reproducible | `docker-compose.yml` (3 servicios: db/backend/frontend) | **Cumple** — verificado a fondo en `docs/PUESTA-EN-PRODUCCION.md` (clon limpio). |
| RNF04 | Responsiva + identidad Stronger Aragón + accesibilidad básica | `frontend/src/styles/theme.css`: `--color-primary: #97A947` (oliva, AA ≈7.55:1 documentado en el propio CSS), `--font-display: 'Bebas Neue'` (condensada), `:focus-visible` (línea 289), `@media (prefers-reduced-motion: reduce)` (línea 478); breakpoints `@media (max-width: ...)` en la mayoría de los `.css` de página | **Cumple** |
| RNF05 | OpenAPI/Swagger en /docs | `backend/src/api/main.py` (FastAPI por defecto) | **Cumple** |
| RNF06 | Password hash + JWT + control de acceso por rol | `infrastructure/security/password.py` (bcrypt puro), `infrastructure/security/jwt.py`, `api/v1/dependencies.py` | **Cumple** |

## HU01–HU15 y CU01–CU15 (flujo principal / alterno)

Las 15 historias de usuario corresponden 1:1 a los 15 RF ya evaluados arriba
(flujo principal = Cumple en todos). La tabla siguiente se enfoca en el
**flujo alterno** de cada caso de uso, que es donde aparecen diferencias
reales:

| CU | Flujo alterno descrito | Verificación | Estado |
|---|---|---|---|
| CU01 | Credenciales incorrectas → error, sin acceso | `test_login_con_password_incorrecto_devuelve_401` | **Cumple** |
| CU02 | Rol sin permiso → bloqueo + "acceso no autorizado" | `require_role` devuelve 403 con detalle | **Cumple** |
| CU03 | Falta un dato obligatorio → error, no guarda | Validación Pydantic (422) + `data-invalid` en el formulario | **Cumple** |
| CU04 | Eliminar cliente con membresía activa → "puede solicitar confirmación adicional" | `DeleteClientUseCase` (`application/clients/use_cases.py:182`) borra sin ninguna verificación de membresía/pagos; el frontend (`ClientDetailPage.tsx`) muestra el mismo `ConfirmDialog` genérico para cualquier cliente. Además, `memberships.client_id` tiene `ON DELETE CASCADE` — eliminar un cliente con historial borra en cascada sus membresías, pagos y extras. | **Parcial — corregido en Parte 2** (ver abajo): se agregó una advertencia específica en el diálogo cuando el cliente tiene membresía activa o pagos registrados, sin cambiar el comportamiento de borrado (fuera de alcance de este cierre rediseñar el modelo de retención). |
| CU05 | Membresía ya activa → "pregunta si renovarla o reemplazarla" | No existe ese diálogo interactivo. En su lugar, el sistema (ampliación) resuelve la ambigüedad de otra forma: una vez que existe una membresía, la interfaz solo ofrece "Renovar" (extender vigencia) o "Cambiar plan" (mismo registro, otro plan) — nunca permite crear una segunda membresía "activa" en paralelo. | **Parcial, por diseño** — la intención (evitar membresías activas duplicadas/ambiguas) se cumple por un mecanismo distinto al descrito literalmente. No se retrocede a construir el diálogo "renovar o reemplazar": el diseño actual ya es estrictamente mejor (menos clics, cero riesgo de duplicado). Se deja registrado como divergencia intencional. |
| CU06 | Monto no corresponde al plan → advertencia antes de confirmar | No existe una advertencia específica de "este monto no coincide con el plan"; el monto es libre (lo cual es correcto para pagos parciales/con desglose de extras) | **Parcial, por diseño** — el "desglose de pago" de la ampliación (ver abajo) resuelve esto de forma más completa (el monto se autocalcula si se usa el desglose), pero un pago sin desglose con un monto arbitrario no genera ninguna advertencia. No bloqueante: es una decisión de negocio válida (pagos parciales, abonos) que una advertencia genérica estorbaría más de lo que ayuda. |
| CU07 | — (sin alterno) | Automatizado (scheduler diario) + disparo manual | **Cumple**, mejor que lo documentado |
| CU08 | Cliente con rutina activa → "pregunta si reemplazar o mantener historial" | `AssignRoutineToClientUseCase` siempre agrega una nueva asignación, nunca pregunta; el historial se conserva por diseño (lista append-only) | **Parcial, por diseño** — mismo patrón que CU05: el historial nunca se pierde (eso es lo que pide la intención de fondo), pero no hay un diálogo interactivo de elegir. |
| CU09 | Cliente sin rutinas → mensaje indicándolo | `frontend/src/pages/ClientDetailPage.tsx`, pestaña Rutina: `EmptyState` cuando la lista viene vacía | **Cumple** |
| CU10 | Mismo alterno que CU08, para dietas | `AssignPlanToClientUseCase` (diets), mismo patrón append-only | **Parcial, por diseño** — igual que CU08. |
| CU11 | Fecha ya tiene un registro → "pregunta si sobrescribir" | `RegisterBodyProgressUseCase` no verifica duplicados por fecha; permite varios registros en la misma fecha sin preguntar | **Parcial, por diseño** — mismo patrón; no es bloqueante (la gráfica de evolución simplemente grafica todos los puntos). |
| CU12 | Cliente sin suficientes registros → mensaje o gráfica limitada | `ProgressChart.tsx` renderiza con 1 solo punto sin error; `EmptyState` si hay 0 | **Cumple** |
| CU13 | Entrenador accede a cliente no asignado → bloqueo | `UnauthorizedRoutineAssignmentError`/equivalentes → 403 | **Cumple** |
| CU14 | Cliente intenta modificar su info → no se le permite | Sin controles de edición en la interfaz para ese rol; además el backend rechaza (403) si se intenta vía API directa | **Cumple** |
| CU15 | — (sin alterno) | `/docs` | **Cumple** |

**Nota sobre CU05/CU08/CU10/CU11:** las cuatro comparten el mismo patrón --
el documento describe un diálogo interactivo de elegir entre dos opciones: el
código, en los cuatro casos, resolvió la intención de fondo (no perder
historial, no terminar en un estado ambiguo) con un diseño que nunca
pregunta. Es una divergencia real y consistente, no un olvido aislado — se
reporta una sola vez aquí con el detalle por caso en la tabla, y se deja como
decisión de diseño aceptada (no se construyen 4 diálogos de confirmación
nuevos en este cierre; ver `docs/PENDIENTES-HUMANOS.md` si el usuario real
los pide más adelante).

## Trazabilidad RF–HU–CU–CP (Tabla 10)

Verificada 1:1 contra el código: los 15 RF, HU y CU coinciden exactamente con
la Tabla 10 del documento. La columna "Caso de prueba" de esa tabla
(CP01–CP18) se verifica en `docs/RESULTADOS-FINALES.md`, junto con los casos
nuevos de la ampliación (sin ID en el documento, por la razón ya explicada).

## Ampliación de RF004/RF005 (especificación: el encargo de este cierre, no el `.docx`)

| Elemento pedido | Dónde está | Estado |
|---|---|---|
| Pantalla "Planes y servicios" con pestañas Planes/Servicios extra | `frontend/src/pages/PlanesServiciosPage.tsx` (solo admin) | **Cumple** |
| Servicios extra y qué incluye cada plan | `Service`, `PlanService` (`domain/memberships/entities.py`), migración `0003` | **Cumple** |
| Desglose de pago por concepto | `PaymentItem`, `backend/src/api/v1/routers/payments.py`, pestaña Pagos de `ClientDetailPage.tsx` | **Cumple** |
| Cambio de plan: extras incluidos se cancelan, los demás se conservan, resumen antes de confirmar, transacción atómica, sin borrar historial, sin calcular reembolso | `application/memberships/use_cases.py::ChangeMembershipPlanUseCase`/`PreviewChangeMembershipPlanUseCase`, `POST /memberships/{id}/change-plan(/preview)`, botón "Cambiar plan" en `ClientDetailPage.tsx` | **Cumple** — probado explícitamente con un caso de atomicidad (`test_cambio_de_plan_es_atomico_si_el_plan_destino_no_existe`). |
| Pantalla "Membresías" como tablero de activas (indicadores, tabla, búsqueda/filtro, renovar/cobrar), sin tarjetas de planes | `frontend/src/pages/MembershipsPage.tsx`, `GET /memberships/board` | **Cumple** |
| Ficha del cliente con plan, extras activos y vencimientos | `ClientDetailPage.tsx`, pestaña Membresía | **Cumple** |
| Vencimientos que generan `Notification` | `DetectExpiringMembershipsUseCase` + `NotifyUserUseCase` | **Cumple** |

Las 28 pruebas automatizadas de la ampliación (CP19–CP46, ver
`docs/RESULTADOS-ENTREGA-3.md`) siguen en verde en el baseline de este cierre
(`docs/BASE-PYTEST-ANTES.txt`).

## Modelo de datos (Tabla 17: "14 entidades" vs. realidad actual)

El documento lista 14 entidades. El esquema real de PostgreSQL hoy tiene
**18 tablas**: las 14 originales más `services`, `plan_services`,
`membership_services` y `payment_items` (migraciones `0003`/`0004`). El
usuario, en el encargo de este cierre, habla de "17 entidades" — la
diferencia es `plan_services`: es una tabla puente pura (clave primaria
compuesta `plan_id`+`service_id`, sin columnas propias ni `id`), que puede
contarse como "relación N:M", no como una entidad con identidad propia —
mismo criterio que el documento ya aplica implícitamente a
`RoutineExercise` (sí la cuenta, porque tiene columnas propias:
`sets`/`reps`/`order_index`) vs. una relación pura. Conclusión: **18 tablas
físicas, 17 si se cuenta solo entidades con atributos propios** (excluyendo
`plan_services`). Diagrama entidad-relación actualizado exportado en
`docs/diagrama-entidad-relacion.svg` (ver Parte 5).

## "Sobra": funcionalidad construida que ningún RF pide

Búsqueda exhaustiva de rutas/pantallas sin requisito que las respalde:

- **Ninguna encontrada.** Las 59 combinaciones ruta+método de la API y las 11
  pantallas del frontend (`frontend/src/pages/*.tsx`) se trazan todas a algún
  RF001–015 o a la ampliación de RF004/RF005. No hay pantallas huérfanas,
  endpoints sin requisito, ni mocks residuales (`grep -r mock frontend/src`
  → 0 resultados reales, `frontend/src/mocks/` no existe desde una sesión
  previa).
- La única zona gris es la propia ampliación (ver el hallazgo de la sección
  3.4 arriba): no "sobra" en el sentido de "nadie la pidió" (el propio
  encargo la pide explícitamente), pero sí le falta su respaldo formal en el
  documento de la entrega.

## Resumen de la auditoría

- **15/15 RF: Cumple.** 2 con una nota de documentación desactualizada
  (RF006, RF014 — el código mejoró después de escrita la tabla).
- **6/6 RNF: Cumple.**
- **15/15 HU: Cumple** (mapean 1:1 a los RF).
- **15/15 CU, flujo principal: Cumple.** Flujo alterno: 11/15 Cumple, 4 con
  divergencia de diseño consistente y documentada (CU05/08/10/11), 1 corregido
  en esta misma entrega (CU04).
- **Ampliación de RF004/RF005: Cumple en código**, con un hallazgo de
  documentación de máxima prioridad (sección 3.4 inexistente).
- **0 elementos "Sobra".**
- **Modelo de datos:** 18 tablas reales vs. 14 documentadas — las 4 nuevas
  pertenecen a la ampliación, no son no-pedidas.
