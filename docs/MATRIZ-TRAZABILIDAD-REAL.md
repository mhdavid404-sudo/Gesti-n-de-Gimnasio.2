# Matriz de trazabilidad real — RF → HU → CU → código → CP → resultado

Fecha: 2026-11-16. Cada fila se verificó contra el código real (no contra
la Tabla 10 del documento de memoria) y contra una corrida real de `pytest`.
Resultado real en `docs/RESULTADOS-FINALES.md`.

| RF | HU | CU | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|---|---|
| RF001 | HU01 | CU01 | `api/v1/routers/auth.py` | `pages/LoginPage.tsx` | CP01, CP02 (+ `test_auth.py`) | Pasó |
| RF002 | HU02 | CU02 | `api/v1/dependencies.py::require_role` | `components/layout/Sidebar.tsx` | CP03 | Pasó |
| RF003 | HU03 | CU03, CU04 | `api/v1/routers/clients.py`, `application/clients/use_cases.py` | `pages/ClientsListPage.tsx`, `ClientFormPage.tsx`, `ClientDetailPage.tsx` | CP04, CP05, CP06 (+ `test_clients.py`) | Pasó |
| RF004 | HU04 | CU05 | `api/v1/routers/memberships.py`, `application/memberships/use_cases.py` | `pages/ClientDetailPage.tsx` (asignar/renovar/cambiar plan), `MembershipsPage.tsx` (tablero) | CP07 (+ `test_memberships.py`, CP29-36, CP37-46, CP53-59 de BUG-12) | Pasó |
| RF005 | HU05 | CU06 | `api/v1/routers/payments.py`, `application/payments/use_cases.py` | `pages/ClientDetailPage.tsx` (pestaña Pagos) | CP08 (+ `test_payments.py`, CP27-28, CP55/CP59 de BUG-12) | Pasó |
| RF006 | HU06 | CU07 | `application/memberships/use_cases.py::DetectExpiringMembershipsUseCase`, `infrastructure/scheduler.py` | `pages/MembershipsPage.tsx` ("Revisar vencimientos ahora"), alertas del Dashboard | CP09 (+ `test_notifications.py`, `test_scheduler.py`; BUG-12 reusa el mismo umbral de 7 días de "por vencer" para la ventana de renovación) | Pasó |
| RF007 | HU07 | CU08 | `api/v1/routers/routines.py::create_routine` | `pages/RoutinesPage.tsx` | CP10 (+ `test_routines.py`) | Pasó |
| RF008 | HU08 | CU09 | `application/routines/use_cases.py::GetClientRoutineHistoryUseCase` | `pages/ClientDetailPage.tsx` (pestaña Rutina) | CP11 | Pasó |
| RF009 | HU09 | CU10 | `api/v1/routers/diets.py` | `pages/DietsPage.tsx` | CP13 (+ `test_diets.py`) | Pasó |
| RF010 | HU10 | CU11 | `api/v1/routers/progress.py::register_progress` | `pages/ClientDetailPage.tsx` (pestaña Progreso) | CP14 (+ `test_progress.py`) | Pasó |
| RF011 | HU11 | CU12 | `application/progress/use_cases.py::GetClientProgressTimelineUseCase` | `components/ui/ProgressChart.tsx`, `pages/ProgressPage.tsx` | CP15 | Pasó (verificación manual, sin prueba de render) |
| RF012 | HU12 | CU13 | ownership por `trainer_id` en `clients.py`/`routines.py`/`diets.py` | `pages/ClientDetailPage.tsx` (edición de entrenador) | CP12 | Pasó |
| RF013 | HU13 | CU14 | ownership por dato (los 5 routers) | sin controles de edición para rol `cliente` en ninguna pantalla | CP16 | Pasó |
| RF014 | HU14 | CU15 | `api/main.py` (FastAPI/OpenAPI) | — | CP17 (+ `test_cp17_documentacion_api.py`) | Pasó |
| RF015 | HU15 | — | `api/main.py` (manejadores globales) | `pages/AuditLogsPage.tsx` | CP18 (+ `test_audit_logs.py`) | Pasó |

## Ampliación de RF004/RF005 (sin ID formal en el documento — ver hallazgo de la sección 3.4)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| Catálogo de servicios + qué incluye cada plan | `api/v1/routers/memberships.py::services_router`, `domain/memberships/entities.py::Service/PlanService` | `pages/PlanesServiciosPage.tsx` | CP19-26 (`test_services.py`) | Pasó |
| Desglose de pago por concepto | `api/v1/routers/payments.py`, `domain/payments/entities.py::PaymentItem` | `pages/ClientDetailPage.tsx` (pestaña Pagos) | CP27-28 (`test_payments.py`) | Pasó |
| Tablero de membresías activas | `api/v1/routers/memberships.py::get_active_memberships_board` | `pages/MembershipsPage.tsx` | CP29-36 (`test_memberships.py`) | Pasó |
| Cambio de plan (cancela extras incluidos, conserva el resto, atómico) | `application/memberships/use_cases.py::ChangeMembershipPlanUseCase` | `pages/ClientDetailPage.tsx` (botón "Cambiar plan") | CP37-46 (`test_change_plan.py`) | Pasó |

## Ampliación de RF001/RF003 (restablecimiento de contraseña + edición de datos de cliente, 2026-11-18 — sin ID formal en el documento)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| Restablecer contraseña (admin, sin pedir la anterior) | `api/v1/routers/users.py::reset_user_password`, `application/users/use_cases.py::ResetUserPasswordUseCase` | `pages/ClientDetailPage.tsx` (botón "Generar contraseña" desde 2026-11-22, antes "Restablecer contraseña"; el mismo botón en `pages/UsersPage.tsx` conserva el nombre "Restablecer contraseña"), pestaña Perfil | CP47-49 (`test_users.py`) | Pasó |
| Editar datos de cliente desde la ficha (teléfono, dirección, fecha de nacimiento, nombre de contacto de emergencia, teléfono de contacto de emergencia, entrenador) | `api/v1/routers/clients.py::update_client` (endpoint ya existía desde Entrega 2; solo faltaba la pantalla) | `pages/ClientDetailPage.tsx` (botón "Editar datos", pestaña Perfil) | CP05 (+ `test_editar_cliente_como_no_admin_devuelve_403`) | Pasó |

## Ampliación de RF001 (pantalla "Usuarios": alta, activar/desactivar admin/entrenador, 2026-11-18 — sin ID formal en el documento)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| Alta de admin/entrenador con registro en Bitácora | `api/v1/routers/users.py::register_user`, `application/users/use_cases.py::RegisterUserUseCase` (`POST /users` ya existía desde Entrega 2; el registro en `AuditLog` es nuevo) | `pages/UsersPage.tsx` (botón "+ Nuevo usuario") | CP50 (`test_users.py`) | Pasó |
| Activar/desactivar una cuenta, con autodesactivación bloqueada | `api/v1/routers/users.py::update_user` (`PATCH /users/{id}` ya existía; el chequeo de autodesactivación y el registro en `AuditLog` son nuevos) | `pages/UsersPage.tsx` (botón "Activar"/"Desactivar" por fila) | CP51, CP52 (`test_users.py`) | Pasó |
| Protección de ruta de "Usuarios" (solo admin, `entrenador`/`cliente` bloqueados incluso por URL directa) | chequeo de rol en el cliente, no en `GET /users` (ver `DECISIONES.md` para por qué no se angostó ese endpoint compartido) | `pages/UsersPage.tsx` | — (verificado en navegador, sin CP de pytest -- es un chequeo puramente de frontend) | Pasó |

## Editar/eliminar rutinas y dietas (amplía RF007/RF009/RF012, 2026-11-18 — sin ID formal en el documento)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| Editar/eliminar rutina (se desactiva en vez de borrar si tiene asignaciones) | `api/v1/routers/routines.py` (`PATCH`/`DELETE /routines/{id}`), `application/routines/use_cases.py::UpdateRoutineUseCase`/`DeleteOrDeactivateRoutineUseCase` | `pages/RoutinesPage.tsx` (botones "Editar"/"Eliminar") | CP60-64 (`test_routines.py`) | Pasó |
| Editar/eliminar plan de dieta (mismo criterio) | `api/v1/routers/diets.py` (`PATCH`/`DELETE /diets/plans/{id}`), `application/diets/use_cases.py::UpdateDietPlanUseCase`/`DeleteOrDeactivateDietPlanUseCase` | `pages/DietsPage.tsx` (botones "Editar"/"Eliminar") | CP69-73 (`test_diets.py`) | Pasó |
| Corregir/quitar una asignación de rutina o dieta sin perder la bitácora | `api/v1/routers/{routines,diets}.py` (`PATCH` ampliado + `DELETE` nuevo de asignación) | `pages/{RoutinesPage,DietsPage}.tsx`, `pages/ClientDetailPage.tsx` (botones "Corregir"/"Quitar") | CP65-68, CP74-76 (`test_routines.py`, `test_diets.py`) | Pasó |

Migración `0006_editar_eliminar_rutinas_dietas`: agrega `is_active` a
`routines` y `diet_plans` (mismo patrón que `0003` en `membership_plans`/
`services`). Ver `DECISIONES.md`, entrada "Editar/eliminar rutinas y
dietas", y BUG-13/BUG-14 (corregidos durante esta ampliación).

## Separación de contacto de emergencia en nombre/teléfono (migración 0007, 2026-11-22 — sin ID formal en el documento)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| `ClientProfile.emergency_contact` (texto libre) se divide en `emergency_contact_name`/`emergency_contact_phone` | `domain/clients/entities.py`, `infrastructure/db/models/clients.py`, `api/v1/schemas/clients.py`, `application/clients/use_cases.py`, migración `0007_contacto_emergencia_separado` (migra los datos existentes partiendo por el primer "-") | `pages/ClientFormPage.tsx` (alta) y `pages/ClientDetailPage.tsx` (editar/ver perfil): dos campos en vez de uno | Reversión del arbitraje de 2026-09-12 — sin CP propio: ningún caso existente asertaba sobre el valor de este campo, solo se actualizaron los 10 fixtures que lo usaban como dato de relleno (`test_clients.py`, `test_change_plan.py`, `test_diets.py`, `test_memberships.py`, `test_notifications.py`, `test_payments.py`, `test_progress.py`, `test_routines.py`, `test_scheduler.py`, `test_services.py`) | Pasó (139/139, sin cambio en el número de casos) |

Ver `DECISIONES.md`, entrada "Separación de contacto de emergencia en
nombre/teléfono".

## BUG-12 — renovar + cobrar atómico, ventana de 7 días, deshacer (2026-11-18 — sin ID formal en el documento)

| Elemento | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|
| "Renovar" cobra el pago en la misma operación atómica (antes eran dos acciones separadas) | `application/memberships/use_cases.py::RenewAndChargeMembershipUseCase`, `api/v1/routers/memberships.py::renew_membership` | `pages/MembershipsPage.tsx`, `pages/ClientDetailPage.tsx` (pestaña Membresía) | CP53 (+ CP15-18 ampliados) | Pasó |
| Ventana de 7 días (o ya vencida) para poder renovar; doble clic rechazado | `application/memberships/exceptions.py::MembershipRenewalWindowError` | botón "Renovar" deshabilitado con explicación en ambas pantallas | CP53, CP54 | Pasó |
| Deshacer la última renovación (anula el pago, restaura la fecha, pide motivo) | `application/memberships/use_cases.py::UndoMembershipRenewalUseCase`, tabla nueva `membership_renewals` (migración `0005`) | `pages/ClientDetailPage.tsx` (botón "Deshacer renovación") | CP55-58 | Pasó |
| Un pago anulado no cuenta en ingresos/totales | `api/v1/routers/memberships.py::get_active_memberships_board` (excluye `status == 'anulado'`) | `pages/DashboardPage.tsx` (`monthIncome`) | CP59 | Pasó |

## Modelo de datos (19 tablas: 14 de la migración `0001` + 4 de `0003` + `membership_renewals` de `0005`/BUG-12)

Ver `docs/diagrama-entidad-relacion.svg` (desactualizado: sigue en 18
tablas y migraciones `0001-0004`, pendiente de regenerar) y
`backend/MODELO-DATOS.md` para el detalle completo de columnas/
constraints. Migraciones aplicadas: `0001` a `0007` (ver
`docs/RESULTADOS-PRUEBAS-COMPLETO.md` para el detalle de cada una).
