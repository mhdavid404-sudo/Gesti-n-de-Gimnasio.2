# Resultados de pruebas — Reporte completo (SmartGym v2)

Fecha de esta corrida: **2026-11-22**. Todos los números de este documento
salen de ejecutar algo real ahora mismo (`docker compose exec backend
pytest -v`, consulta directa a la base de datos y al esquema OpenAPI en
vivo) — ninguno es estimado ni copiado de memoria. Este documento no
reemplaza a `docs/RESULTADOS-FINALES.md`/`docs/RESULTADOS-ENTREGA-3.md`
(que siguen siendo la fuente histórica de CP01–CP76); los extiende con el
mapeo 1:1 completo de las 139 pruebas reales del código, incluidas las que
nunca tuvieron un número de CP asignado.

## 1. Resultado de la corrida de `pytest -v`

Corrida iniciada **2026-11-22 23:36:42** (hora del contenedor), comando
`docker compose exec backend pytest -v`. Salida completa (las 139 líneas
`PASSED` individuales) en el caso de prueba correspondiente de la sección
3; aquí el encabezado y el resumen final, literales:

```
============================= test session starts ==============================
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.7.0 -- /usr/local/bin/python3.13
cachedir: .pytest_cache
rootdir: /app
plugins: anyio-4.16.0
collecting ... collected 139 items

[... 139 líneas "tests/archivo.py::test_nombre PASSED [ N%]", una por cada
fila de la tabla de la sección 3 -- todas en verde, ninguna omitida ni
marcada xfail/skip ...]

=============================== warnings summary ===============================
../usr/local/lib/python3.13/site-packages/starlette/testclient.py:40
  /usr/local/lib/python3.13/site-packages/starlette/testclient.py:40: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = typing.Callable[[], typing.ContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 139 passed, 1 warning in 413.96s (0:06:53) ==================
```

**139/139 pruebas automatizadas en verde, 0 fallos.** Mismo número que la
corrida anterior (`docs/RESULTADOS-FINALES.md`, 2026-11-18) — la
separación de "Contacto de emergencia" en nombre/teléfono (migración
`0007`, ver abajo) no agregó pruebas nuevas: los 10 archivos que usaban
ese campo como dato de relleno al registrar un cliente de prueba se
actualizaron para pasar los dos campos nuevos, pero ninguna prueba
existente asertaba sobre el valor de ese campo, así que el conteo total
no cambió.

## 2. Migraciones aplicadas (`0001` a `0007`)

Estado real verificado en la base de desarrollo: `alembic current` →
`0007 (head)`. Tabla actual: **19 tablas de dominio** (más
`alembic_version`, que no es una tabla de negocio) — confirmado con
`\dt` contra Postgres real.

| Migración | Fecha | Qué hace | Tablas / columnas que cambia |
|---|---|---|---|
| `0001_initial_schema` | 2026-09-12 | Esquema inicial completo, escrito a mano (sin BD viva todavía en ese momento) | Crea las 14 tablas originales: `users`, `client_profiles`, `membership_plans`, `memberships`, `payments`, `exercises`, `routines`, `routine_exercises`, `routine_assignments`, `diet_plans`, `diet_assignments`, `body_progress`, `notifications`, `audit_logs` |
| `0002_backlog_alineacion_modelo` | 2026-10-10 | Resuelve 4 de las 11 inconsistencias del backlog backend↔frontend que sí requerían cambio real de esquema (las otras 7 eran solo de `frontend/types/models.ts`) | Agrega columnas: `membership_plans.benefits` (JSON), `exercises.equipment` (VARCHAR 100), `routine_assignments.notes` (TEXT), `diet_assignments.notes` (TEXT) |
| `0003_planes_y_servicios_extra` | 2026-11-04 | Entrega 3 Fase 2: catálogo de servicios extra contratables además del plan | Agrega `membership_plans.is_active`; crea 4 tablas nuevas: `services`, `plan_services` (puente N:M), `membership_services` (contratación con `price_at_purchase` congelado), `payment_items` (desglose de pago) → 18 tablas |
| `0004_cambio_de_plan` | 2026-11-04 | Cambio de plan de membresía y su efecto sobre extras ya contratados | Sin tablas/columnas nuevas: amplía 2 `CHECK` existentes — `membership_services.status` admite `'cancelado_por_cambio_de_plan'` (y la columna se ensancha a VARCHAR(40) para que quepa el valor), `notifications.type` admite `'plan_cambiado'` |
| `0005_renovar_y_deshacer` | 2026-11-18 | BUG-12: "Renovar" pasa a cobrar en la misma operación atómica, con ventana de 7 días, y se agrega "Deshacer renovación" | `payments.status` admite `'anulado'` (CHECK ampliado); crea tabla nueva `membership_renewals` (historial de renovaciones, pago asociado, quién/cuándo la deshizo) → 19 tablas |
| `0006_editar_eliminar_rutinas_dietas` | 2026-11-18 | Editar/eliminar rutinas y planes de dieta (y corregir/quitar sus asignaciones) sin perder historial | Agrega `routines.is_active` y `diet_plans.is_active` (ambas booleanas, default `true`) — sin tablas nuevas |
| `0007_contacto_emergencia_separado` | 2026-11-22 | Revierte el arbitraje de 2026-09-12: el contacto de emergencia vuelve a ser dos campos, no uno de texto libre | Agrega `client_profiles.emergency_contact_name` (VARCHAR 255) y `client_profiles.emergency_contact_phone` (VARCHAR 30); migra los datos existentes partiendo el valor anterior por el primer "-"; elimina `client_profiles.emergency_contact` — sin tablas nuevas |


## 3. Tabla completa de casos de prueba (CP01–CP129, 139 pruebas)

Una fila por cada función `def test_...` real en `backend/tests/`.
CP01–CP76 son los ya documentados en `docs/RESULTADOS-FINALES.md`/
`docs/RESULTADOS-ENTREGA-3.md` (mismo número). CP77–CP129 son 53 CP
nuevos, asignados en este cierre a pruebas que ya existían en el código
sin ningún CP formal en la documentación.

## test_health.py — Salud del servicio

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP77 | Salud del servicio | Sin RF formal (infraestructura) | El endpoint de health check responde OK (extiende verificación básica de arranque, sin CP original) | Backend arriba, sin BD necesaria | `GET /health` | 200, body `{"status":"ok"}` | Igual | Aprobó | `test_health.py::test_health_check_ok` |
| CP78 | Documentación API | RF014 (extiende CP17) | El JSON de OpenAPI se sirve y contiene `paths` | Backend arriba | `GET /openapi.json` | 200, `"paths"` presente en el body | Igual | Aprobó | `test_health.py::test_openapi_schema_is_served` |

## test_cp17_documentacion_api.py — Documentación de la API

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP17 | Documentación API | RF014 | `/docs` muestra la interfaz Swagger | Backend arriba | `GET /docs` | 200, `content-type: text/html`, el HTML contiene `swagger-ui` | Igual | Aprobó | `test_cp17_documentacion_api.py::test_docs_endpoint_serves_swagger_ui` |
| CP79 | Documentación API | RF001-RF015 (extiende CP17) | El esquema OpenAPI documenta endpoints de los 11 módulos reales (users, clients, membership-plans, memberships, payments, exercises, routines, diets, progress, notifications, audit-logs) | Backend arriba | `GET /openapi.json` | 200, cada prefijo de módulo tiene al menos un path documentado | Igual | Aprobó | `test_cp17_documentacion_api.py::test_openapi_schema_lists_endpoints_from_every_module` |

## test_auth.py — Auth/Roles (RF001, RF002)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP80 | Auth/Roles | RF001 (extiende CP01-03) | Alta de usuario nuevo como admin autenticado | Admin sembrado y autenticado | `POST /users` con email/password/full_name/role="entrenador" | 201; body trae el usuario sin `password`/`password_hash` | Igual | Aprobó | `test_auth.py::test_registro_exitoso` |
| CP81 | Auth/Roles | RF001 (extiende CP01-03) | Alta con email ya usado por otra cuenta falla | Admin autenticado; un usuario ya creado con ese email | Repetir `POST /users` con el mismo email | 409, detalle menciona "email" | Igual | Aprobó | `test_auth.py::test_registro_con_email_duplicado_devuelve_409` |
| CP01 | Auth/Roles | RF001 | Login con credenciales válidas devuelve token | Usuario sembrado con password conocido | `POST /auth/login` con email/password correctos | 200; `token_type=bearer`, `access_token` largo, `user.email`/`user.role` correctos | Igual | Aprobó | `test_auth.py::test_login_con_credenciales_correctas_devuelve_token` |
| CP02 | Auth/Roles | RF001 | Login con password incorrecto falla | Usuario sembrado | `POST /auth/login` con password equivocado | 401 | Igual | Aprobó | `test_auth.py::test_login_con_password_incorrecto_devuelve_401` |
| CP82 | Auth/Roles | RF001 (extiende CP02) | Login con usuario inexistente falla | Ninguna (email nunca sembrado) | `POST /auth/login` con email que no existe | 401 | Igual | Aprobó | `test_auth.py::test_login_con_usuario_inexistente_devuelve_401` |
| CP83 | Auth/Roles | RF002 (extiende CP03) | Ruta protegida sin token rechaza el acceso | Ninguna | `GET /users` sin header `Authorization` | 401 | Igual | Aprobó | `test_auth.py::test_acceso_sin_token_a_ruta_protegida_devuelve_401` |
| CP03 | Auth/Roles | RF002 | Rol insuficiente no puede dar de alta usuarios | Cliente sembrado y autenticado | `POST /users` con JWT de rol `cliente` | 403 | Igual | Aprobó | `test_auth.py::test_acceso_con_rol_insuficiente_devuelve_403` |

## test_clients.py — Clientes (RF003)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP04 | Clientes | RF003 | Alta exitosa de cliente como admin | Admin autenticado | `POST /clients` con datos completos | 201; `client.email`/`full_name`/`trainer_id` correctos; `temporary_password` de 12 caracteres | Igual | Aprobó | `test_clients.py::test_alta_exitosa_de_cliente_como_admin` |
| CP84 | Clientes | RF003 (extiende CP04) | Alta de cliente rechazada para rol no-admin | Entrenador autenticado | `POST /clients` con JWT de entrenador | 403 | Igual | Aprobó | `test_clients.py::test_alta_rechazada_para_rol_no_admin_devuelve_403` |
| CP85 | Clientes | RF003 (extiende RF012/013) | Admin ve el listado completo de clientes | Admin autenticado; 2 clientes registrados (uno con entrenador, otro sin) | `GET /clients` | 200; 2 elementos | Igual | Aprobó | `test_clients.py::test_listado_como_admin_ve_todos` |
| CP86 | Clientes | RF012 (extiende CP04) | Entrenador ve solo sus clientes asignados en el listado | 2 entrenadores, 1 cliente por cada uno | `GET /clients` con JWT del entrenador A | 200; 1 elemento, el del entrenador A | Igual | Aprobó | `test_clients.py::test_listado_como_entrenador_ve_solo_los_suyos` |
| CP16 | Clientes | RF013 | Cliente accede a su propio perfil | Cliente registrado, password temporal conocida | `GET /clients/{id}` con JWT propio | 200; email correcto | Igual | Aprobó | `test_clients.py::test_cliente_accede_a_su_propio_perfil` |
| CP16 | Clientes | RF013 | Cliente NO accede al perfil de otro cliente | 2 clientes registrados | `GET /clients/{id_del_otro}` con JWT propio | 403 | Igual | Aprobó | `test_clients.py::test_cliente_no_accede_al_perfil_de_otro_devuelve_403` |
| CP87 | Clientes | RF003/RF012 (extiende CU04) | Reasignar `trainer_id` a un usuario que no tiene rol entrenador falla | Admin autenticado; un usuario rol `cliente` existente; cliente de prueba registrado | `PATCH /clients/{id}` con `trainer_id` = id de un usuario rol cliente | 400; detalle menciona "entrenador" | Igual | Aprobó | `test_clients.py::test_reasignar_entrenador_con_trainer_id_invalido_falla` |
| CP05 | Clientes | RF003 | Editar un campo de un cliente existente como admin | Admin autenticado; cliente registrado | `PATCH /clients/{id}` con `phone`/`address` nuevos | 200; cambios reflejados; persisten en un `GET` posterior | Igual | Aprobó | `test_clients.py::test_editar_cliente_como_admin_actualiza_datos` |
| CP05 | Clientes | RF003 | Editar cliente como no-admin falla sin cambiar nada | Entrenador autenticado; cliente registrado | `PATCH /clients/{id}` con JWT de entrenador | 403; el `GET` posterior confirma que el teléfono original no cambió | Igual | Aprobó | `test_clients.py::test_editar_cliente_como_no_admin_devuelve_403` |
| CP88 | Clientes | RF003 (ampliación 2026-11-18, sin CP formal) | Editar nombre y correo de la cuenta del cliente como admin | Admin autenticado; cliente registrado con password temporal conocida | `PATCH /clients/{id}` con `full_name`/`email` nuevos | 200; cambia en la respuesta; queda `AuditLog` `action="editar_cuenta_cliente"` con ambos valores; login funciona con el correo nuevo y falla con el viejo | Igual | Aprobó | `test_clients.py::test_editar_nombre_y_correo_de_cliente_como_admin` |
| CP89 | Clientes | RF003 (ampliación 2026-11-18, sin CP formal) | Editar correo a uno ya usado por otra cuenta falla sin cambiar nada | Admin autenticado; 2 clientes registrados | `PATCH /clients/{id_2}` con el email del cliente 1 | 409; detalle menciona "email"; el cliente 2 conserva su correo original | Igual | Aprobó | `test_clients.py::test_editar_cliente_con_correo_repetido_devuelve_409` |
| CP90 | Clientes | RF003 (extiende CP06) | Eliminar cliente como no-admin falla | Entrenador autenticado; cliente registrado | `DELETE /clients/{id}` con JWT de entrenador | 403 | Igual | Aprobó | `test_clients.py::test_eliminar_cliente_como_no_admin_devuelve_403` |
| CP06 | Clientes | RF003 | Eliminar un cliente existente como admin | Admin autenticado; cliente registrado | `DELETE /clients/{id}` | 204; el id ya no aparece en `GET /clients` | Igual | Aprobó | `test_clients.py::test_eliminar_cliente_como_admin_elimina_correctamente` |

## test_memberships.py — Membresías (RF004)

Precondición adicional compartida: casi todas requieren un plan creado (`POST /membership-plans`) y, cuando aplica, un cliente registrado y/o una membresía ya asignada (`POST /memberships`).

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP91 | Membresías | RF004 (extiende CP07) | Crear plan de membresía como admin | Admin autenticado | `POST /membership-plans` con name/price/duration_days/benefits | 201; campos reflejados | Igual | Aprobó | `test_memberships.py::test_crear_plan_como_admin` |
| CP92 | Membresías | RF004 (extiende CP07) | Crear plan como no-admin falla | Entrenador autenticado | `POST /membership-plans` con JWT de entrenador | 403 | Igual | Aprobó | `test_memberships.py::test_crear_plan_como_no_admin_devuelve_403` |
| CP93 | Membresías | RF004 | Listar planes como cualquier rol autenticado | Un plan creado; cliente autenticado | `GET /membership-plans` con JWT de cliente | 200; incluye el plan creado | Igual | Aprobó | `test_memberships.py::test_listar_planes_como_cualquier_rol_autenticado` |
| CP94 | Membresías | RF004 (landing pública) | Listar planes sin autenticación es público | Un plan creado | `GET /membership-plans` sin header `Authorization` | 200; incluye el plan | Igual | Aprobó | `test_memberships.py::test_listar_planes_sin_autenticacion_es_publico` |
| CP07 | Membresías | RF004 | Asignar membresía exitosa | Plan y cliente creados | `POST /memberships` con client_id/plan_id/fechas/status="activa" | 201; `client_id`/`plan_id`/`status` correctos | Igual | Aprobó | `test_memberships.py::test_asignar_membresia_exitosa` |
| CP95 | Membresías | RF004 (extiende CP07) | Asignar membresía con `plan_id` inexistente falla | Cliente creado | `POST /memberships` con `plan_id=999999` | 404; detalle incluye "999999" | Igual | Aprobó | `test_memberships.py::test_asignar_membresia_con_plan_inexistente_falla` |
| CP96 | Membresías | RF004 (extiende CP07) | Asignar membresía con `end_date <= start_date` falla | Plan y cliente creados | `POST /memberships` con `end_date` anterior a `start_date` | 400 | Igual | Aprobó | `test_memberships.py::test_asignar_membresia_con_fechas_invalidas_falla` |
| CP97 | Membresías | RF004 | Listado de membresías como admin ve todas | 2 membresías asignadas a 2 clientes distintos | `GET /memberships` como admin | 200; 2 elementos | Igual | Aprobó | `test_memberships.py::test_listado_de_membresias_como_admin_ve_todas` |
| CP98 | Membresías | RF012 | Listado de membresías como entrenador ve solo las de sus clientes | 2 entrenadores, 1 cliente+membresía cada uno | `GET /memberships` con JWT del entrenador A | 200; 1 elemento, el de su cliente | Igual | Aprobó | `test_memberships.py::test_listado_de_membresias_como_entrenador_ve_solo_las_de_sus_clientes` |
| CP16 | Membresías | RF013 | Cliente accede a su propia membresía pero no a la de otro | 2 clientes, cada uno con membresía propia | `GET /memberships/{id}` propia (200) y ajena (403) | 200 / 403 respectivamente | Igual | Aprobó | `test_memberships.py::test_cliente_accede_a_su_propia_membresia_pero_no_a_la_de_otro` |
| CP99 | Membresías | RF004 | Cambiar `status` de una membresía como no-admin falla | Entrenador autenticado; membresía de su cliente | `PATCH /memberships/{id}` con `status="cancelada"`, JWT de entrenador | 403 | Igual | Aprobó | `test_memberships.py::test_cambio_de_status_como_no_admin_devuelve_403` |
| CP29 | Membresías | RF004 (ajuste UX, tablero) | Tablero de membresías activas como admin: indicadores + tabla | 2 membresías (una vence en 3 días, otra en 20) + 1 pago registrado | `GET /memberships/board` | 200; `total_active=2`, `expiring_soon=1`, `monthly_revenue=399.00`, fila de la que vence en 3 días marca `expiring_soon=true`/`days_remaining=3` | Igual | Aprobó | `test_memberships.py::test_tablero_de_membresias_activas_como_admin` |
| CP30 | Membresías | RF012 (tablero) | Tablero como entrenador ve solo sus clientes, sin ingresos | 2 entrenadores, 1 cliente+membresía cada uno | `GET /memberships/board` con JWT de entrenador A | 200; `total_active=1`, `monthly_revenue=null`, 1 fila (su cliente) | Igual | Aprobó | `test_memberships.py::test_tablero_como_entrenador_ve_solo_sus_clientes_y_sin_ingresos` |
| CP31 | Membresías | RF013 (tablero) | Tablero como cliente no tiene acceso | Cliente autenticado | `GET /memberships/board` con JWT de cliente | 403 | Igual | Aprobó | `test_memberships.py::test_tablero_como_cliente_devuelve_403` |
| CP32 | Membresías | RF004 (tablero) | Filtros por plan y por nombre acotan la tabla sin afectar los indicadores | 2 clientes con planes distintos | `GET /memberships/board?plan_id=X` y `?q=ana` | Indicadores (`total_active`) sin filtrar; `items` sí filtrados a 1 fila cada vez | Igual | Aprobó | `test_memberships.py::test_tablero_filtra_por_plan_y_por_nombre_sin_afectar_indicadores` |
| CP33 | Membresías | RF004 (BUG-12) | Renovar dentro de la ventana extiende la vigencia y cobra | Membresía que vence en 3 días | `POST /memberships/{id}/renew` con `method="efectivo"` | 200; `end_date` nuevo = vieja + duración del plan; pago `completado` por el precio del plan; `renewal.reversed_at=null` | Igual | Aprobó | `test_memberships.py::test_renovar_membresia_extiende_la_vigencia_y_cobra` |
| CP34 | Membresías | RF004 (BUG-12) | Renovar una membresía vencida la reactiva desde hoy | Membresía con `status="vencida"`, vencida hace 10 días | `POST /memberships/{id}/renew` con `method="tarjeta"` | 200; `status="activa"`; `end_date` = hoy + duración del plan; `renewal.previous_status="vencida"` | Igual | Aprobó | `test_memberships.py::test_renovar_membresia_vencida_la_reactiva_desde_hoy` |
| CP53 | Membresías | RF004 (BUG-12) | Renovar fuera de la ventana de 7 días falla y no cambia nada | Membresía que vence en 30 días | `POST /memberships/{id}/renew` | 409; detalle menciona el plazo/"7"; `end_date` sin cambios; sin pagos creados | Igual | Aprobó | `test_memberships.py::test_renovar_fuera_de_la_ventana_devuelve_409_y_no_cambia_nada` |
| CP54 | Membresías | RF004 (BUG-12) | Renovar dos veces seguidas (doble clic): la segunda falla | Membresía recién renovada una vez | Segunda llamada inmediata a `POST /memberships/{id}/renew` | 409 en la segunda; solo 1 pago total | Igual | Aprobó | `test_memberships.py::test_renovar_dos_veces_seguidas_la_segunda_falla` |
| CP35 | Membresías | RF004/RF012 (BUG-12) | Renovar como no-admin falla | Entrenador autenticado; membresía de su cliente | `POST /memberships/{id}/renew` con JWT de entrenador | 403 | Igual | Aprobó | `test_memberships.py::test_renovar_membresia_como_no_admin_devuelve_403` |
| CP36 | Membresías | RF004 (BUG-12) | Renovar una membresía inexistente falla | Admin autenticado | `POST /memberships/999999/renew` | 404 | Igual | Aprobó | `test_memberships.py::test_renovar_membresia_inexistente_falla` |
| CP55 | Membresías | RF004/RF015 (BUG-12) | Deshacer una renovación restaura la fecha anterior y anula el pago | Membresía recién renovada | `POST /memberships/renewals/{id}/undo` con `reason` | 200; `end_date` vuelve a la original; pago pasa a `status="anulado"` (no se borra); `renewal.reversed_at`/`reversed_reason` llenos; `AuditLog` trae `renovar_membresia` y `deshacer_renovacion_membresia` | Igual | Aprobó | `test_memberships.py::test_deshacer_renovacion_restaura_fecha_y_anula_pago` |
| CP56 | Membresías | RF004 (BUG-12) | Deshacer una renovación ya deshecha falla | Renovación ya deshecha una vez | Segundo `POST .../undo` sobre el mismo `renewal_id` | 409 | Igual | Aprobó | `test_memberships.py::test_deshacer_renovacion_ya_deshecha_devuelve_409` |
| CP57 | Membresías | RF004 (BUG-12) | Deshacer con una renovación posterior ya aplicada falla | Primera renovación + segunda renovación posterior (simulada con fecha forzada) | `POST .../undo` sobre la primera renovación | 409 | Igual | Aprobó | `test_memberships.py::test_deshacer_renovacion_con_renovacion_posterior_devuelve_409` |
| CP58 | Membresías | RF004/RF012 (BUG-12) | Deshacer como no-admin falla | Entrenador autenticado; renovación existente | `POST .../undo` con JWT de entrenador | 403 | Igual | Aprobó | `test_memberships.py::test_deshacer_renovacion_como_no_admin_devuelve_403` |
| CP59 | Membresías | RF004 (BUG-12) | Un pago anulado no cuenta en los ingresos del mes | Renovación hecha y luego deshecha | `GET /memberships/board` antes y después de deshacer | `monthly_revenue` baja de `399.00` a `0` tras deshacer | Igual | Aprobó | `test_memberships.py::test_pago_anulado_no_cuenta_en_ingresos_del_mes` |

## test_payments.py — Pagos (RF005)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP08 | Pagos | RF005 | Registrar pago exitoso como admin | Plan, cliente y membresía creados | `POST /payments` con membership_id/amount/method/status | 201; `registered_by` = id del admin autenticado | Igual | Aprobó | `test_payments.py::test_registrar_pago_exitoso_como_admin` |
| CP100 | Pagos | RF005 (defecto corregido, extiende CP08) | El body no puede falsificar `registered_by` | Otro admin existente | `POST /payments` inyectando `registered_by` de otro admin en el JSON | 201; `registered_by` = admin que autenticó la llamada, no el inyectado | Igual | Aprobó | `test_payments.py::test_registrar_pago_ignora_registered_by_inyectado_en_el_body` |
| CP101 | Pagos | RF005 (extiende CP08) | Registrar pago con `membership_id` inexistente falla | Admin autenticado | `POST /payments` con `membership_id=999999` | 404; detalle incluye "999999" | Igual | Aprobó | `test_payments.py::test_registrar_pago_con_membership_id_inexistente_falla` |
| CP102 | Pagos | RF005/RF012 (extiende CP08) | Registrar pago como no-admin falla | Entrenador autenticado; membresía existente | `POST /payments` con JWT de entrenador | 403 | Igual | Aprobó | `test_payments.py::test_registrar_pago_como_no_admin_devuelve_403` |
| CP103 | Pagos | RF005 | Listado de pagos como admin ve todos | 2 pagos de 2 clientes distintos | `GET /payments` como admin | 200; 2 elementos | Igual | Aprobó | `test_payments.py::test_listado_de_pagos_como_admin_ve_todos` |
| CP104 | Pagos | RF012 | Listado de pagos como entrenador ve solo los de sus clientes | 2 entrenadores, 1 pago por cliente de cada uno | `GET /payments` con JWT del entrenador A | 200; 1 elemento, el de su cliente | Igual | Aprobó | `test_payments.py::test_listado_de_pagos_como_entrenador_ve_solo_los_de_sus_clientes` |
| CP16 | Pagos | RF013 | Cliente accede a su propio pago pero no al de otro | 2 clientes, cada uno con su pago | `GET /payments/{id}` propio (200) y ajeno (403) | 200 / 403 | Igual | Aprobó | `test_payments.py::test_cliente_accede_a_su_propio_pago_pero_no_al_de_otro` |
| CP27 | Pagos | RF005 (Fase 2) | Desglose de pago cuya suma no coincide con `amount` falla | Plan/cliente/membresía creados | `POST /payments` con `items` que no suman el `amount` | 400 | Igual | Aprobó | `test_payments.py::test_registrar_pago_con_desglose_que_no_coincide_con_el_monto_falla` |
| CP28 | Pagos | RF005 (Fase 2) | Desglose de pago exitoso guarda cada línea | Plan, servicio y membresía creados | `POST /payments` con `items` (plan + servicio) que sí suman el monto | 201; `items` con 2 conceptos (`plan`,`servicio`); persisten en un `GET` posterior | Igual | Aprobó | `test_payments.py::test_registrar_pago_con_desglose_exitoso_guarda_items` |

## test_services.py — Planes y servicios extra (RF004/RF005, Fase 2)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP19 | Planes y servicios | RF004 | Eliminar un plan CON membresías contratadas lo desactiva | Plan con una membresía asignada | `DELETE /membership-plans/{id}` | 200; `is_active=false`; sigue listado en el catálogo público | Igual | Aprobó | `test_services.py::test_eliminar_plan_con_membresias_lo_desactiva` |
| CP20 | Planes y servicios | RF004 | Eliminar un plan SIN membresías lo elimina de verdad | Plan sin contrataciones | `DELETE /membership-plans/{id}` | 200; desaparece del catálogo | Igual | Aprobó | `test_services.py::test_eliminar_plan_sin_membresias_lo_elimina` |
| CP21 | Planes y servicios | RF005 | Eliminar un servicio CON contrataciones lo desactiva | Servicio contratado por un cliente | `DELETE /services/{id}` | 200; `is_active=false` | Igual | Aprobó | `test_services.py::test_eliminar_servicio_con_contrataciones_lo_desactiva` |
| CP22 | Planes y servicios | RF005 | Eliminar un servicio SIN contrataciones lo elimina de verdad | Servicio sin contrataciones | `DELETE /services/{id}` | 200; desaparece del catálogo | Igual | Aprobó | `test_services.py::test_eliminar_servicio_sin_contrataciones_lo_elimina` |
| CP23 | Planes y servicios | RF005 | Cambiar el precio de un servicio no afecta lo ya contratado | Servicio contratado a precio $450 | `PATCH /services/{id}` sube el precio a $600 | `price_at_purchase` de la contratación existente sigue en $450 | Igual | Aprobó | `test_services.py::test_cambio_de_precio_de_servicio_no_afecta_lo_ya_contratado` |
| CP24 | Planes y servicios | RF005 | Contratar un servicio ya incluido en el plan falla | Servicio incluido en el plan del cliente | `POST /memberships/{id}/services` con ese servicio | 409 | Igual | Aprobó | `test_services.py::test_contratar_servicio_ya_incluido_en_el_plan_falla` |
| CP25 | Planes y servicios | RF004/RF005 | Alta/edición/eliminación de catálogo como no-admin falla | Entrenador autenticado; plan y servicio existentes | 6 llamadas (crear/editar/eliminar plan y servicio) con JWT de entrenador | Las 6 devuelven 403 | Igual | Aprobó | `test_services.py::test_catalogo_de_planes_y_servicios_como_no_admin_devuelve_403` |
| CP26 | Planes y servicios | RF005 | `GET /memberships/{id}/services` oculta `price_at_purchase` al entrenador | Servicio contratado; cliente con entrenador asignado | `GET` con JWT admin/entrenador/cliente | Admin y cliente ven `price_at_purchase`; entrenador no | Igual | Aprobó | `test_services.py::test_entrenador_ve_extras_sin_precio_admin_y_cliente_si` |

## test_change_plan.py — Cambio de plan (RF004/RF005)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP37 | Cambio de plan | RF004/RF005 | Subir de plan cancela el extra ya incluido en el nuevo | Membresía con extra contratado que el plan nuevo incluye | `POST /memberships/{id}/change-plan` | 200; extra cancelado (`cancelado_por_cambio_de_plan`, `end_date=hoy`); `plan_id` actualizado | Igual | Aprobó | `test_change_plan.py::test_subir_de_plan_cancela_el_extra_ya_incluido_en_el_nuevo` |
| CP38 | Cambio de plan | RF004/RF005 | Subir de plan conserva extras no incluidos en el nuevo | Extra contratado que ningún plan incluye | `POST /memberships/{id}/change-plan` | 200; `kept_extras` con ese extra; sigue `status="activa"` | Igual | Aprobó | `test_change_plan.py::test_subir_de_plan_conserva_extras_no_incluidos` |
| CP39 | Cambio de plan | RF004/RF005 | Bajar de plan no agrega ni cobra los servicios que se dejan de incluir | Membresía Premium con servicio incluido; bajar a Básica (no lo incluye) | `POST /memberships/{id}/change-plan` | 200; `newly_contractable_services` lista el servicio; no se crea ninguna `MembershipService` | Igual | Aprobó | `test_change_plan.py::test_bajar_de_plan_no_agrega_ni_cobra_los_servicios_que_se_dejan_de_incluir` |
| CP40 | Cambio de plan | RF004/RF005 | El historial de pagos y extras no se borra tras el cambio | Pago y extra existentes antes del cambio | `POST /memberships/{id}/change-plan` | El pago sigue consultable igual; el extra cancelado sigue existiendo | Igual | Aprobó | `test_change_plan.py::test_historial_de_pagos_y_extras_no_se_borra` |
| CP41 | Cambio de plan | RF004/RF005 | Cambio de plan es atómico si el plan destino no existe | Membresía con extra contratado | `POST /memberships/{id}/change-plan` con `new_plan_id=999999` | 404; ni el plan ni el extra cambiaron | Igual | Aprobó | `test_change_plan.py::test_cambio_de_plan_es_atomico_si_el_plan_destino_no_existe` |
| CP42 | Cambio de plan | RF004/RF012/RF013 | Entrenador y cliente no pueden cambiar ni previsualizar el plan | Membresía de un cliente con entrenador asignado | `POST .../change-plan/preview` y `POST .../change-plan` con JWT de entrenador/cliente | 403 en ambos casos, para ambos roles; el plan no cambió | Igual | Aprobó | `test_change_plan.py::test_entrenador_y_cliente_no_pueden_cambiar_ni_previsualizar_el_plan` |
| CP43 | Cambio de plan | RF004/RF005 | Previsualizar no persiste ningún cambio | Membresía con extra contratado | `POST /memberships/{id}/change-plan/preview` | 200 con el resultado simulado; el plan y el extra en BD siguen sin cambios | Igual | Aprobó | `test_change_plan.py::test_preview_no_persiste_nada` |
| CP44 | Cambio de plan | RF004/RF006/RF015 | Confirmar genera auditoría y notifica al cliente | Membresía sin extras, con `notes` en el payload | `POST /memberships/{id}/change-plan` con `notes` | 200; `AuditLog` `action="cambio_de_plan"` con las notas; `Notification` tipo `plan_cambiado` al cliente | Igual | Aprobó | `test_change_plan.py::test_confirmar_genera_auditoria_y_notifica_al_cliente` |
| CP45 | Cambio de plan | RF004/RF005 | Cambiar al mismo plan ya asignado falla | Membresía con plan X | `POST /memberships/{id}/change-plan/preview` con `new_plan_id` = el mismo | 400 | Igual | Aprobó | `test_change_plan.py::test_cambiar_al_mismo_plan_falla` |
| CP46 | Cambio de plan | RF004/RF005 | Cambiar a un plan desactivado falla | Un plan desactivado (con contratación previa) | `POST .../change-plan/preview` apuntando al plan desactivado | 400 | Igual | Aprobó | `test_change_plan.py::test_cambiar_a_un_plan_desactivado_falla` |

## test_notifications.py — Vencimientos/Notificaciones (RF006)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP09 | Vencimientos | RF006 | Detectar una membresía vencida genera notificación al usuario correcto | Membresía con `end_date` pasada | `POST /memberships/detect-expiring` | 200; membresía pasa a `status="vencida"`; `Notification` tipo `membresia_vencida` para el cliente | Igual | Aprobó | `test_notifications.py::test_deteccion_marca_membresia_vencida_y_notifica_al_usuario_correcto` |
| CP105 | Vencimientos | RF006 (extiende CP09) | Detectar membresía por vencer notifica sin cambiar el status | Membresía que vence en 3 días | `POST /memberships/detect-expiring` | 200; sigue `status="activa"`; 1 `Notification` tipo `membresia_por_vencer` | Igual | Aprobó | `test_notifications.py::test_deteccion_de_membresia_por_vencer_notifica_sin_cambiar_status` |
| CP106 | Vencimientos | RF006 (extiende CP09) | Correr la detección dos veces no duplica la notificación | Membresía por vencer | 2 llamadas seguidas a `POST /memberships/detect-expiring` | Sigue habiendo solo 1 `Notification` tipo `membresia_por_vencer` | Igual | Aprobó | `test_notifications.py::test_deteccion_repetida_de_por_vencer_no_duplica_la_notificacion` |
| CP107 | Vencimientos | RF006/RF012 (extiende CP09) | Detectar vencimientos como no-admin falla | Entrenador autenticado | `POST /memberships/detect-expiring` con JWT de entrenador | 403 | Igual | Aprobó | `test_notifications.py::test_detect_expiring_como_no_admin_devuelve_403` |
| CP108 | Vencimientos | RF006 (extiende CP09) | `GET /memberships/expiring` refleja vencidas/por vencer sin correr el POST antes | 3 membresías: vencida, por vencer y sana | `GET /memberships/expiring` | Incluye la vencida y la por vencer; excluye la sana | Igual | Aprobó | `test_notifications.py::test_get_expiring_refleja_vencidas_y_por_vencer_sin_correr_el_post_antes` |
| CP16 | Vencimientos | RF013 | Consultar notificaciones de otro usuario sin ser admin falla | 2 clientes, cada uno con sus notificaciones | `GET /notifications/users/{id}` propio (200), ajeno (403), y como admin (200) | Los 3 resultados como arriba | Igual | Aprobó | `test_notifications.py::test_get_notifications_de_otro_usuario_sin_ser_admin_devuelve_403` |
| CP109 | Vencimientos | RF006 | Marcar una notificación como leída | Notificación generada por detección previa | `POST /notifications/{id}/read` | 200; `is_read` pasa de `false` a `true` | Igual | Aprobó | `test_notifications.py::test_marcar_notificacion_como_leida` |

## test_scheduler.py — Automatización diaria (RF006)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP110 | Vencimientos | RF006 (extiende CP09) | `start_scheduler()` registra el job diario a las 06:00 | Ninguna | Llamar `start_scheduler()`, inspeccionar el trigger cron del job | El job existe; `hour=6`, `minute=0` | Igual | Aprobó | `test_scheduler.py::test_start_scheduler_registra_el_job_diario` |
| CP111 | Vencimientos | RF006 (extiende CP09) | La función que ejecuta el job diario transiciona y notifica igual que el endpoint manual | Membresía vencida (fecha pasada) | Llamar `run_daily_expiring_detection()` directo (sin pasar por HTTP) | Membresía pasa a `vencida`; se genera `Notification` tipo `membresia_vencida` | Igual | Aprobó | `test_scheduler.py::test_run_daily_expiring_detection_transiciona_y_notifica` |

## test_routines.py — Rutinas (RF007/RF008/RF012/RF013)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP10 | Rutinas | RF007 | Crear rutina como entrenador registra el `created_by` correcto | Entrenador autenticado | `POST /routines` con name/description | 201; `created_by` = id del entrenador | Igual | Aprobó | `test_routines.py::test_crear_rutina_como_entrenador_devuelve_created_by_correcto` |
| CP112 | Rutinas | RF007 (defecto corregido, extiende CP10) | El body no puede falsificar `created_by` | Otro usuario admin existente | `POST /routines` inyectando `created_by` de otro usuario | 201; `created_by` = quien autenticó la llamada | Igual | Aprobó | `test_routines.py::test_crear_rutina_ignora_created_by_inyectado_en_el_body` |
| CP113 | Rutinas | RF007/RF013 (extiende CP10) | Crear rutina como cliente falla | Cliente autenticado | `POST /routines` con JWT de cliente | 403 | Igual | Aprobó | `test_routines.py::test_crear_rutina_como_cliente_devuelve_403` |
| CP114 | Rutinas | RF007 | Agregar ejercicio a una rutina inexistente falla | Ejercicio del catálogo creado | `POST /routines/999999/exercises` | 404 | Igual | Aprobó | `test_routines.py::test_agregar_ejercicio_a_rutina_inexistente_devuelve_404` |
| CP115 | Rutinas | RF007 | Agregar un ejercicio inexistente a una rutina falla | Rutina creada | `POST /routines/{id}/exercises` con `exercise_id=999999` | 404 | Igual | Aprobó | `test_routines.py::test_agregar_ejercicio_inexistente_a_rutina_devuelve_404` |
| CP116 | Rutinas | RF008/RF012 (extiende CP11/12) | Asignar rutina a cliente propio como entrenador | Cliente asignado a ese entrenador; rutina creada | `POST /routines/assignments` | 201; `assigned_by` = id del entrenador | Igual | Aprobó | `test_routines.py::test_asignar_rutina_a_cliente_propio_como_entrenador_devuelve_201` |
| CP117 | Rutinas | RF012 (extiende CP11/12) | Asignar rutina a cliente ajeno como entrenador falla | Cliente asignado a OTRO entrenador | `POST /routines/assignments` | 403 | Igual | Aprobó | `test_routines.py::test_asignar_rutina_a_cliente_ajeno_como_entrenador_devuelve_403` |
| CP11 | Rutinas | RF008/RF013 | Consultar historial de rutinas: cliente ve lo propio, no lo ajeno | 2 clientes, cada uno con una rutina asignada | `GET /routines/assignments/clients/{id}` propio (200) y ajeno (403) | 200 (1 elemento) / 403 | Igual | Aprobó | `test_routines.py::test_historial_como_cliente_ve_lo_propio_pero_no_lo_de_otro` |
| CP12 | Rutinas | RF012 | `PATCH` de asignación como entrenador dueño funciona | Asignación creada por ese mismo entrenador | `PATCH /routines/assignments/{id}` con status/notes | 200; cambios reflejados | Igual | Aprobó | `test_routines.py::test_patch_assignment_como_entrenador_dueno_devuelve_200` |
| CP118 | Rutinas | RF012 (extiende CP12) | `PATCH` de asignación como entrenador que NO es dueño falla | Asignación creada por OTRO entrenador | `PATCH /routines/assignments/{id}` con JWT del otro entrenador | 403 | Igual | Aprobó | `test_routines.py::test_patch_assignment_como_entrenador_no_dueno_devuelve_403` |
| CP60 | Rutinas | RF007 (ampliación 2026-11-18) | Editar rutina como admin actualiza nombre/descripción y queda en bitácora | Rutina creada | `PATCH /routines/{id}` con name/description nuevos | 200; cambios reflejados; `AuditLog action="editar_rutina"` | Igual | Aprobó | `test_routines.py::test_editar_rutina_como_admin_actualiza_datos` |
| CP61 | Rutinas | RF007/RF012 | Editar rutina ajena como entrenador falla | Rutina creada por OTRO entrenador | `PATCH /routines/{id}` | 403 | Igual | Aprobó | `test_routines.py::test_editar_rutina_ajena_como_entrenador_devuelve_403` |
| CP62 | Rutinas | RF007 | Eliminar rutina SIN asignaciones la borra de verdad | Rutina sin asignaciones | `DELETE /routines/{id}` | 200; `deleted=true`, `routine=null`; desaparece del catálogo | Igual | Aprobó | `test_routines.py::test_eliminar_rutina_sin_asignaciones_borra_de_verdad` |
| CP63 | Rutinas | RF007 | Eliminar rutina CON asignaciones la desactiva, conserva historial | Rutina con una asignación existente | `DELETE /routines/{id}` | 200; `deleted=false`; `routine.is_active=false`; sigue consultable | Igual | Aprobó | `test_routines.py::test_eliminar_rutina_con_asignaciones_la_desactiva` |
| CP64 | Rutinas | RF007/RF013 | Eliminar rutina como cliente falla | Cliente autenticado; rutina existente | `DELETE /routines/{id}` con JWT de cliente | 403 | Igual | Aprobó | `test_routines.py::test_eliminar_rutina_como_cliente_devuelve_403` |
| CP65 | Rutinas | RF012/RF015 | Corregir una asignación (rutina/fecha) como entrenador dueño | Asignación propia; otra rutina disponible | `PATCH /routines/assignments/{id}` con `routine_id`/`assigned_date` nuevos | 200; `routine_id` actualizado; `AuditLog action="editar_asignacion_rutina"` | Igual | Aprobó | `test_routines.py::test_corregir_asignacion_rutina_como_entrenador_dueno_actualiza_y_registra_bitacora` |
| CP66 | Rutinas | RF012/RF015 | Eliminar una asignación borra la fila pero la bitácora sobrevive | Asignación existente | `DELETE /routines/assignments/{id}` | 204; desaparece del historial; `AuditLog action="eliminar_asignacion_rutina"` sigue existiendo | Igual | Aprobó | `test_routines.py::test_eliminar_asignacion_rutina_borra_la_fila_pero_bitacora_sobrevive` |
| CP67 | Rutinas | RF012 | Eliminar una asignación como entrenador no dueño falla | Asignación de OTRO entrenador | `DELETE /routines/assignments/{id}` | 403 | Igual | Aprobó | `test_routines.py::test_eliminar_asignacion_rutina_como_entrenador_no_dueno_devuelve_403` |
| CP68 | Rutinas | RF012 | Editar una asignación ya "completada" nunca la elimina | Asignación marcada `completada` | `PATCH` de nuevo (solo `notes`) sobre la misma asignación | 200; la fila sigue existiendo, con `status="completada"` y la nota nueva | Igual | Aprobó | `test_routines.py::test_editar_asignacion_completada_no_la_elimina` |

## test_diets.py — Dietas (RF009/RF012/RF013)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP119 | Dietas | RF009 (extiende CP13) | Crear plan de dieta como entrenador registra el `created_by` correcto | Entrenador autenticado | `POST /diets/plans` con name/description/calories_target | 201; `created_by` correcto | Igual | Aprobó | `test_diets.py::test_crear_plan_como_entrenador_devuelve_created_by_correcto` |
| CP120 | Dietas | RF009 (defecto corregido, extiende CP13) | El body no puede falsificar `created_by` | Otro usuario existente | `POST /diets/plans` inyectando `created_by` ajeno | 201; `created_by` = quien autenticó | Igual | Aprobó | `test_diets.py::test_crear_plan_ignora_created_by_inyectado_en_el_body` |
| CP121 | Dietas | RF009/RF013 (extiende CP13) | Crear plan como cliente falla | Cliente autenticado | `POST /diets/plans` con JWT de cliente | 403 | Igual | Aprobó | `test_diets.py::test_crear_plan_como_cliente_devuelve_403` |
| CP13 | Dietas | RF009 | Crear y asignar plan de dieta a cliente propio como entrenador | Cliente asignado a ese entrenador; plan creado | `POST /diets/assignments` | 201; `assigned_by` correcto | Igual | Aprobó | `test_diets.py::test_asignar_plan_a_cliente_propio_como_entrenador_devuelve_201` |
| CP122 | Dietas | RF012 (extiende CP13) | Asignar plan a cliente ajeno como entrenador falla | Cliente de OTRO entrenador | `POST /diets/assignments` | 403 | Igual | Aprobó | `test_diets.py::test_asignar_plan_a_cliente_ajeno_como_entrenador_devuelve_403` |
| CP16 | Dietas | RF009/RF013 | Consultar historial de dietas: cliente ve lo propio, no lo ajeno | 2 clientes con plan asignado cada uno | `GET /diets/assignments/clients/{id}` propio (200) y ajeno (403) | 200 (1 elemento) / 403 | Igual | Aprobó | `test_diets.py::test_historial_como_cliente_ve_lo_propio_pero_no_lo_de_otro` |
| CP123 | Dietas | RF012 (extiende CP13) | `PATCH` de asignación como entrenador dueño funciona | Asignación creada por ese entrenador | `PATCH /diets/assignments/{id}` con status/notes | 200; cambios reflejados | Igual | Aprobó | `test_diets.py::test_patch_assignment_como_entrenador_dueno_devuelve_200` |
| CP124 | Dietas | RF012 (extiende CP13) | `PATCH` de asignación como entrenador no dueño falla | Asignación de otro entrenador | `PATCH /diets/assignments/{id}` | 403 | Igual | Aprobó | `test_diets.py::test_patch_assignment_como_entrenador_no_dueno_devuelve_403` |
| CP69 | Dietas | RF009 (ampliación 2026-11-18) | Editar plan de dieta como admin, queda en bitácora | Plan creado | `PATCH /diets/plans/{id}` con name/calories_target nuevos | 200; cambios reflejados; `AuditLog action="editar_dieta"` | Igual | Aprobó | `test_diets.py::test_editar_plan_como_admin_actualiza_datos` |
| CP70 | Dietas | RF009/RF012 | Editar plan ajeno como entrenador falla | Plan creado por otro entrenador | `PATCH /diets/plans/{id}` | 403 | Igual | Aprobó | `test_diets.py::test_editar_plan_ajeno_como_entrenador_devuelve_403` |
| CP71 | Dietas | RF009 | Eliminar plan SIN asignaciones lo borra de verdad | Plan sin asignaciones | `DELETE /diets/plans/{id}` | 200; `deleted=true`; desaparece del catálogo | Igual | Aprobó | `test_diets.py::test_eliminar_plan_sin_asignaciones_borra_de_verdad` |
| CP72 | Dietas | RF009 | Eliminar plan CON asignaciones lo desactiva, conserva historial | Plan con asignación existente | `DELETE /diets/plans/{id}` | 200; `deleted=false`; `is_active=false` | Igual | Aprobó | `test_diets.py::test_eliminar_plan_con_asignaciones_lo_desactiva` |
| CP73 | Dietas | RF009/RF013 | Eliminar plan como cliente falla | Cliente autenticado | `DELETE /diets/plans/{id}` con JWT de cliente | 403 | Igual | Aprobó | `test_diets.py::test_eliminar_plan_como_cliente_devuelve_403` |
| CP74 | Dietas | RF012/RF015 | Corregir una asignación (plan/fecha) como entrenador dueño | Asignación propia; otro plan disponible | `PATCH /diets/assignments/{id}` con `diet_plan_id`/`assigned_date` nuevos | 200; `diet_plan_id` actualizado; `AuditLog action="editar_asignacion_dieta"` | Igual | Aprobó | `test_diets.py::test_corregir_asignacion_dieta_como_entrenador_dueno_actualiza_y_registra_bitacora` |
| CP75 | Dietas | RF012/RF015 | Eliminar una asignación borra la fila, la bitácora sobrevive | Asignación existente | `DELETE /diets/assignments/{id}` | 204; desaparece del historial; `AuditLog action="eliminar_asignacion_dieta"` persiste | Igual | Aprobó | `test_diets.py::test_eliminar_asignacion_dieta_borra_la_fila_pero_bitacora_sobrevive` |
| CP76 | Dietas | RF012 | Eliminar una asignación como entrenador no dueño falla | Asignación de otro entrenador | `DELETE /diets/assignments/{id}` | 403 | Igual | Aprobó | `test_diets.py::test_eliminar_asignacion_dieta_como_entrenador_no_dueno_devuelve_403` |

## test_progress.py — Progreso corporal (RF010/RF011)

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP14 | Progreso | RF010 | Registrar progreso corporal como admin | Cliente registrado | `POST /progress` con client_id/record_date/weight_kg/waist_cm | 201; `client_id`/`waist_cm` correctos | Igual | Aprobó | `test_progress.py::test_registrar_progreso_como_admin_devuelve_201` |
| CP125 | Progreso | RF012 (extiende CP14) | Registrar progreso para cliente ajeno como entrenador falla | Cliente asignado a OTRO entrenador | `POST /progress` | 403 | Igual | Aprobó | `test_progress.py::test_registrar_progreso_para_cliente_ajeno_como_entrenador_devuelve_403` |
| CP126 | Progreso | RF010 (extiende CP14) | Registrar progreso para cliente inexistente falla | Admin autenticado | `POST /progress` con `client_id=999999` | 404 | Igual | Aprobó | `test_progress.py::test_registrar_progreso_para_cliente_inexistente_devuelve_404` |
| CP127 | Progreso | RF010/RF013 (extiende CP14) | Registrar progreso como cliente falla (no tiene esa acción) | Cliente autenticado | `POST /progress` con JWT de cliente | 403 | Igual | Aprobó | `test_progress.py::test_registrar_progreso_como_cliente_devuelve_403` |
| CP128 | Progreso | RF011 | Timeline de progreso como admin ve cualquiera | Registro de progreso existente | `GET /progress/clients/{id}` como admin | 200; 1 elemento | Igual | Aprobó | `test_progress.py::test_timeline_como_admin_ve_cualquiera` |
| CP129 | Progreso | RF011/RF012 | Timeline como entrenador ve solo sus clientes | 2 entrenadores, 1 registro por cliente de cada uno | `GET /progress/clients/{id}` propio (200) y ajeno (403) | 200 (1) / 403 | Igual | Aprobó | `test_progress.py::test_timeline_como_entrenador_ve_solo_sus_clientes` |
| CP16 | Progreso | RF011/RF013 | Timeline como cliente ve lo propio, no lo ajeno | 2 clientes con registro cada uno | `GET /progress/clients/{id}` propio (200) y ajeno (403) | 200 (1) / 403 | Igual | Aprobó | `test_progress.py::test_timeline_como_cliente_ve_lo_propio_pero_no_lo_de_otro` |

## test_audit_logs.py — Bitácora (RF015)

Todas bajo **CP18** ("provocar un error controlado, consultar el log, el error queda registrado").

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP18 | Bitácora | RF015 | Un 401 de login inválido queda registrado automáticamente | Admin sembrado | `POST /auth/login` con password incorrecto, luego `GET /audit-logs` | La entrada existe, `details` contiene "401", `created_at` presente | Igual | Aprobó | `test_audit_logs.py::test_error_de_login_invalido_queda_registrado_en_bitacora` |
| CP18 | Bitácora | RF015 | Un 422 de validación queda registrado con detalle | Admin autenticado | `POST /users` con payload inválido (email mal formado, etc.) | La entrada existe, `details` contiene "422" | Igual | Aprobó | `test_audit_logs.py::test_error_de_validacion_queda_registrado_con_detalle` |
| CP18 | Bitácora | RF015 | Un 403 queda asociado al usuario que lo provocó | Cliente autenticado | `POST /users` con JWT de cliente (403) | La entrada tiene `user_id` del cliente, `details` contiene "403" | Igual | Aprobó | `test_audit_logs.py::test_error_403_queda_asociado_al_usuario_que_lo_provoco` |
| CP18 | Bitácora | RF015 | Consultar la bitácora como no-admin falla | Cliente autenticado | `GET /audit-logs` con JWT de cliente | 403 | Igual | Aprobó | `test_audit_logs.py::test_consultar_bitacora_como_no_admin_devuelve_403` |
| CP18 | Bitácora | RF015 | Una petición exitosa (2xx) no genera entrada de bitácora | Admin autenticado | `GET /notifications/users/{id}` (200), comparar conteo de bitácora antes/después | El conteo de entradas no cambia | Igual | Aprobó | `test_audit_logs.py::test_peticion_exitosa_no_genera_entrada_de_bitacora` |

## test_users.py — Ampliación de RF001 (pantalla "Usuarios")

| ID | Módulo | RF/HU/CU relacionado | Descripción (qué se prueba) | Precondiciones | Pasos / entrada | Resultado esperado | Resultado obtenido | Estado (Aprobó/Falló) | Archivo y función de prueba (pytest) |
|---|---|---|---|---|---|---|---|---|---|
| CP47 | Usuarios | Ampliación de RF001 | Admin restablece la contraseña de otro usuario | Entrenador sembrado con password conocida | `POST /users/{id}/reset-password` | 200; temporal de 12 caracteres; password anterior ya no sirve, la nueva sí; `AuditLog action="restablecer_password"` | Igual | Aprobó | `test_users.py::test_restablecer_password_como_admin_funciona_y_queda_en_bitacora` |
| CP48 | Usuarios | Ampliación de RF001 | Restablecer contraseña como rol no-admin falla | Entrenador autenticado; cliente objetivo | `POST /users/{id}/reset-password` con JWT de entrenador | 403; password del objetivo sin cambios | Igual | Aprobó | `test_users.py::test_restablecer_password_como_no_admin_devuelve_403` |
| CP49 | Usuarios | Ampliación de RF001 | Restablecer contraseña de un usuario inexistente falla | Admin autenticado | `POST /users/999999/reset-password` | 404 | Igual | Aprobó | `test_users.py::test_restablecer_password_de_usuario_inexistente_devuelve_404` |
| CP50 | Usuarios | Ampliación de RF001 | Alta de usuario como admin queda registrada en bitácora | Admin autenticado | `POST /users` con role="entrenador" | 201; `AuditLog action="crear_usuario"` con el rol en los detalles | Igual | Aprobó | `test_users.py::test_alta_de_usuario_como_admin_queda_en_bitacora` |
| CP51 | Usuarios | Ampliación de RF001 | Desactivar y reactivar a otro usuario, ambas acciones quedan en bitácora | Entrenador sembrado | `PATCH /users/{id}` con `is_active=false` y luego `true` | 200 en ambas; login falla mientras desactivado, funciona reactivado; `AuditLog` con `desactivar_usuario` y `activar_usuario` | Igual | Aprobó | `test_users.py::test_desactivar_y_reactivar_usuario_como_admin_queda_en_bitacora` |
| CP52 | Usuarios | Ampliación de RF001 | Un admin no puede desactivarse a sí mismo | Admin autenticado | `PATCH /users/{id_propio}` con `is_active=false` | 400; sigue pudiendo iniciar sesión | Igual | Aprobó | `test_users.py::test_admin_no_puede_desactivarse_a_si_mismo` |



## 4. Bugs registrados (`BUG-01` a `BUG-14`)

**Nota de transparencia:** `BUG-01` a `BUG-03` (Entrega 1) y el reparto
exacto de `BUG-04` a `BUG-07` (Entrega 2) solo existen, con ese nivel de
detalle, en la Tabla 20 del documento de entrega (`.docx`, fuera de este
repositorio) — no hay un archivo Markdown en `docs/` ni en `DECISIONES.md`
que los desglose uno por uno (se verificó buscando en los dos `.docx` que
sí están en el repo, `Plan-de-Pruebas-SmartGym-v2.docx` y
`Casos-de-Uso-SmartGym-v2.docx`: ninguno de los dos contiene la cadena
"BUG-0"). Para esos 7 se da aquí la mejor reconstrucción posible a partir
de `docs/ESTADO-ACTUAL.md` y `DECISIONES.md` — agrupada, no caso por
caso — en vez de inventar una causa/solución específica que no está
verificada en ningún archivo. De `BUG-08` en adelante sí hay repro/causa/
solución exactas en `docs/RESULTADOS-ENTREGA-3.md` y
`docs/RESULTADOS-FINALES.md`.

| Bug | Falla | Severidad | Causa | Solución | Estado |
|---|---|---|---|---|---|
| BUG-01–BUG-03 | 3 bugs de infraestructura/rutas de la Entrega 1 (detalle exacto solo en la Tabla 20 del `.docx` de entrega, no replicado en este repo) | Baja (no bloquearon el cierre de Entrega 1) | No documentado en Markdown en este repositorio | No documentado en Markdown en este repositorio | Corregido (confirmado en `docs/ESTADO-ACTUAL.md`: "todos corregidos y verificados en su momento... ninguno sigue abierto") |
| BUG-04 | Autoría inyectable: `PaymentCreate.registered_by` lo decidía el cliente HTTP, permitiendo falsificar quién registró un pago | Alta (seguridad/integridad de datos financieros) | El esqueleto original dejaba que el body mandara `registered_by` en vez de tomarlo del JWT | Se quita del payload; el router siempre usa `current_user.id`. Prueba de regresión: `test_registrar_pago_ignora_registered_by_inyectado_en_el_body` | Corregido (DECISIONES.md, "Módulo Pagos completo") |
| BUG-05 | Mismo defecto en Rutinas: `RoutineCreate.created_by`/`RoutineAssignmentCreate.assigned_by` inyectables | Alta | Mismo patrón que BUG-04, copiado al esqueleto de Rutinas | Mismo fix: se quitan del payload, el router usa `current_user.id`. Prueba: `test_crear_rutina_ignora_created_by_inyectado_en_el_body` | Corregido (DECISIONES.md, "Módulo Ejercicios y Rutinas completo") |
| BUG-06 | Mismo defecto en Dietas: `DietPlanCreate.created_by`/`DietAssignmentCreate.assigned_by` inyectables | Alta | Mismo patrón, copiado al esqueleto de Dietas | Mismo fix. Prueba: `test_crear_plan_ignora_created_by_inyectado_en_el_body` | Corregido (DECISIONES.md, "Módulo Dietas completo") |
| BUG-07 | (a) El rol Cliente veía el link "Clientes" en el Sidebar y llegaba a una pantalla de error 403 en vez de nunca ver la opción; (b) loop de render infinito en `useResultsPanel` | Media (UX, no de seguridad: el backend ya rechazaba correctamente con 403) | (a) `Sidebar.tsx` no filtraba los links por rol; (b) dependencias mal declaradas en el hook | (a) Se agrega una lista `roles?` opcional por item de navegación; (b) se corrigen las dependencias del hook | Corregido (DECISIONES.md, línea sobre "Tabla 20... BUG-04 a BUG-07") |
| BUG-08 | `POST /memberships/{id}/change-plan` con un extra a cancelar → `500 Internal Server Error` (`StringDataRightTruncation`) | Alta (caía el request completo) | `membership_services.status` era `VARCHAR(20)` y `"cancelado_por_cambio_de_plan"` tiene 29 caracteres | Columna ensanchada a `VARCHAR(40)` en la migración `0004`, antes de ampliar el `CHECK` | Corregido |
| BUG-09 | Tras corregir BUG-08, `GET /memberships/{id}/services` y `GET /notifications/users/{id}` devolvían `500` al serializar el status/tipo nuevo | Alta | Los `Literal` de Pydantic (`MembershipServiceStatus`, `NotificationType`) no incluían los valores nuevos | Ambos `Literal` ampliados (backend) y sus espejos en `frontend/src/types/api.ts` | Corregido |
| BUG-10 | `ClientDetailPage.tsx` calculaba qué servicios bloquean una nueva contratación / se ofrecen en el desglose de pago sobre TODOS los extras del cliente, sin filtrar por `status` | Media (bug latente, nunca antes alcanzable) | Faltaba filtrar por `status === 'activa'` | `activeContractedServices` (filtrado), usado en ambos lugares | Corregido |
| BUG-11 | Una membresía activa con estado calculado "por vencer" no disparaba la advertencia específica de CU04 al eliminar un cliente | Media (UX, advertencia de seguridad faltante) | `ClientDetailPage.tsx` comparaba contra `getMembershipDisplayStatus()` en vez de `membership.status` (el dato real, que sigue siendo `"activa"`) | Se compara ahora contra `membership.status === 'activa'` directamente | Corregido, verificado en navegador (commit `139d20d`) |
| BUG-12 | En el tablero de Membresías, "Renovar" estaba disponible siempre y cada clic sumaba otro periodo sin límite y sin ningún pago asociado; sin forma de deshacer | Alta (integridad financiera — membresías gratis, pagos faltantes) | `RenewMembershipUseCase` (Entrega 3) se diseñó a propósito sin ventana ni pago — esa decisión de diseño resultó ser el defecto real en uso | `RenewAndChargeMembershipUseCase` (renueva y cobra atómico, ventana de 7 días) + `UndoMembershipRenewalUseCase` (deshace la última renovación, anula el pago sin borrarlo) | Corregido, 7 pruebas nuevas (CP53-CP59) |
| BUG-13 | `PATCH /routines/assignments/{id}`/`PATCH /diets/assignments/{id}` con `routine_id`/`diet_plan_id` nuevo devolvía 200 pero el id seguía siendo el viejo | Alta (la corrección de "error de dedo" no corregía nada) | Ambos repositorios (desde Entrega 2) solo escribían `status`/`notes` en el modelo — nunca `routine_id`/`assigned_date`/`diet_plan_id` | Ambos repositorios ahora persisten también esos campos | Corregido, delatado por `test_corregir_asignacion_*` |
| BUG-14 | El contenedor Docker del backend quedaba caído (`AssertionError: Status code 204 must not have a response body`) al agregar los `DELETE` nuevos de asignación | Alta (tumbaba el backend completo en producción/Docker real) | Faltaba `response_model=None` en los dos `DELETE` (204) nuevos; `fastapi==0.115.0` (el pin real) lo exige, una versión más nueva del entorno de desarrollo local no, así que `pytest` local pasaba sin detectarlo | Se agrega `response_model=None` (mismo patrón que `DELETE /clients/{id}`) | Corregido, confirmado con `docker logs` contra el contenedor real |

**14 bugs en total, 14 cerrados, 0 abiertos.**

## 5. Cambios de la API desde el 16 de noviembre de 2026

Estado real actual (consultado ahora mismo contra `GET /openapi.json` en
vivo): **44 rutas distintas, 68 combinaciones ruta+método, 13 prefijos de
router** (`users`, `clients`, `membership-plans`, `memberships`,
`payments`, `exercises`, `routines`, `diets`, `progress`, `notifications`,
`audit-logs`, `services`) **+ `/health`**. `docs/PENDIENTES-HUMANOS.md`
(fechado 2026-11-16) citaba "59 combinaciones ruta+método en 12 módulos"
como la realidad de ese momento — la diferencia (68 − 59 = 9) coincide
con los endpoints nuevos listados abajo.

### Endpoints nuevos desde el 16 de noviembre

| Endpoint | Agregado en | Para qué |
|---|---|---|
| `POST /memberships/renewals/{renewal_id}/undo` | BUG-12 (migración `0005`) | Deshacer la última renovación de una membresía |
| `GET /memberships/{membership_id}/renewals` | BUG-12 (migración `0005`) | Historial de renovaciones (de ahí sale si hay algo que deshacer) |
| `POST /users/{user_id}/reset-password` | Restablecimiento de contraseña (2026-11-18) | Admin genera una contraseña temporal para cualquier usuario |
| `PATCH /routines/{routine_id}` | Editar/eliminar rutinas y dietas (migración `0006`) | Editar nombre/descripción de una rutina |
| `DELETE /routines/{routine_id}` | Migración `0006` | Eliminar (o desactivar si tiene asignaciones) una rutina |
| `DELETE /routines/assignments/{assignment_id}` | Migración `0006` | Quitar una asignación de rutina sin perder la bitácora |
| `PATCH /diets/plans/{diet_plan_id}` | Migración `0006` | Editar nombre/descripción/calorías de un plan de dieta |
| `DELETE /diets/plans/{diet_plan_id}` | Migración `0006` | Eliminar (o desactivar) un plan de dieta |
| `DELETE /diets/assignments/{assignment_id}` | Migración `0006` | Quitar una asignación de dieta sin perder la bitácora |

### Endpoints existentes con comportamiento o payload modificado

| Endpoint | Qué cambió |
|---|---|
| `POST /memberships/{membership_id}/renew` | Antes solo extendía `end_date` sin cobrar ni límite de fecha (BUG-12). Ahora exige `method` en el body, cobra un `Payment` en la misma operación atómica, y solo funciona dentro de una ventana de 7 días (o membresía ya vencida) |
| `PATCH /routines/assignments/{assignment_id}` | Antes solo aceptaba `status`/`notes` (BUG-13: el `routine_id`/`assigned_date` nuevos se ignoraban silenciosamente). Ahora persiste también `routine_id`/`assigned_date` |
| `PATCH /diets/assignments/{assignment_id}` | Mismo cambio, lado Dietas: ahora persiste también `diet_plan_id`/`assigned_date` |
| `POST /clients` | El payload cambia `emergency_contact: string` por `emergency_contact_name`/`emergency_contact_phone` (migración `0007`, hoy) |
| `PATCH /clients/{client_id}` | Mismo cambio de payload (`emergency_contact_name`/`emergency_contact_phone`); además, desde el 2026-11-18 también acepta `full_name`/`email` para editar la cuenta dueña del perfil (antes solo tocaba `ClientProfile`) |
| `POST /users` | Sin cambio de payload/ruta — pero desde el 2026-11-18 el alta queda registrada en `AuditLog` (antes no) |
| `PATCH /users/{user_id}` | Sin cambio de payload/ruta — pero desde el 2026-11-18 valida que un admin no pueda desactivarse a sí mismo, y activar/desactivar queda en `AuditLog` |


## 6. Totales

- **Pruebas automatizadas: 139/139 en verde, 0 fallos** (corrida real,
  2026-11-22 23:36:42, ver sección 1).
- **Casos de prueba (CP): 129 distintos** (CP01–CP129; ver desglose por
  módulo abajo — reusa los 76 ya oficiales en `docs/RESULTADOS-FINALES.md`
  + 53 nuevos asignados en este cierre para pruebas que ya existían en el
  código sin CP formal).
- **Hash del último commit antes de este cierre:** `7a414b9`
  ("feat(progreso): eje Y con valores redondos y guías tipo plano
  cartesiano"). Este documento, junto con el resto de cambios pendientes
  (botón "Generar contraseña", tablas/tarjetas verdes, separación de
  contacto de emergencia, y las correcciones de esta sección), se
  commitea inmediatamente después — ver el commit siguiente a este hash
  en `git log`.

## 7. Verificación cruzada con la documentación existente

Se revisaron `docs/MATRIZ-TRAZABILIDAD-REAL.md`, `docs/RESULTADOS-FINALES.md`,
`docs/MANUAL-USUARIO.md` y `DECISIONES.md`. Se encontraron y corrigieron
estas inconsistencias (ya aplicadas en el repo, no son solo un reporte):

| Archivo | Qué decía | Qué dice ahora | Por qué |
|---|---|---|---|
| `docs/MANUAL-USUARIO.md` | "...terminando en la migración `0004`" | "...terminando en la migración `0007`" | Van 3 migraciones más desde que se escribió esa línea (`0005` BUG-12, `0006` editar/eliminar rutinas y dietas, `0007` contacto de emergencia) |
| `docs/MANUAL-USUARIO.md` | Botón **"Restablecer contraseña"** en la ficha del cliente (texto y una captura) | Botón **"Generar contraseña"** en la ficha del cliente; se aclara que en la pantalla **Usuarios** el botón que hace lo mismo conserva el nombre **"Restablecer contraseña"** | El botón se renombró solo en `ClientDetailPage.tsx`, no en `UsersPage.tsx` — las dos pantallas ya NO dicen lo mismo, y el manual decía que sí |
| `docs/MANUAL-USUARIO.md` | "contacto de emergencia" como un solo campo en el alta y la edición | "nombre de contacto de emergencia" y "teléfono de contacto de emergencia" como dos campos | Migración `0007` (hoy) |
| `docs/MATRIZ-TRAZABILIDAD-REAL.md` | No tenía ninguna sección para "editar/eliminar rutinas y dietas" (migración `0006`, CP60-76) | Se agregó la sección completa, igual que las demás ampliaciones sin ID formal | Omisión real: la matriz saltaba de "Usuarios" (CP50-52) directo a "BUG-12" (CP53-59), sin mencionar nunca CP60-76 ni la migración `0006` |
| `docs/MATRIZ-TRAZABILIDAD-REAL.md` | No mencionaba la separación de contacto de emergencia | Se agregó una sección nueva | Cambio de hoy, no podía estar antes |
| `docs/MATRIZ-TRAZABILIDAD-REAL.md` | "Modelo de datos (18 tablas → 19 con `membership_renewals`, BUG-12)" — título habla de una transición, cuerpo dice "18 tablas" | "Modelo de datos (19 tablas...)", y se marca `docs/diagrama-entidad-relacion.svg` como desactualizado | Ya no es una transición: son 19 tablas de forma estable desde la migración `0005`; el diagrama ERD (.svg) sigue dibujando 18 tablas y migraciones `0001-0004` — **no se regeneró en esta sesión** (es un archivo SVG grande, regenerarlo a mano es alto riesgo/bajo beneficio para este cierre; queda señalado como pendiente) |

**No se encontró ninguna prueba cuyo nombre o aserciones contradigan la
descripción oficial de su CP** en `docs/RESULTADOS-FINALES.md` /
`docs/RESULTADOS-ENTREGA-3.md` — las 76 descripciones ya documentadas
coinciden con lo que el código realmente hace.

**Limitación reconocida (no corregida, señalada):** `docs/diagrama-entidad-relacion.svg`
sigue mostrando el esquema de 18 tablas / migraciones `0001-0004`.
Regenerarlo requiere el script que lo generó originalmente (mencionado en
`DECISIONES.md` pero no ubicado en este repo) o redibujarlo a mano,
ninguna de las dos cabía en el alcance de este cierre — queda como
pendiente explícito.

**Supuesto señalado (no un hecho verificado):** la Tabla original dice
"CP16: 7 pruebas de ownership por dato" sin listar cuáles. Se reconstruyó
por eliminación (sección 3) — es la asignación más consistente posible,
pero no está confirmada palabra por palabra contra el documento fuente
original (que no está en este repositorio).
