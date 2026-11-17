# Matriz de trazabilidad real — RF → HU → CU → código → CP → resultado

Fecha: 2026-11-16. Cada fila se verificó contra el código real (no contra
la Tabla 10 del documento de memoria) y contra una corrida real de `pytest`.
Resultado real en `docs/RESULTADOS-FINALES.md`.

| RF | HU | CU | Archivo de código (backend) | Archivo de código (frontend) | CP | Resultado |
|---|---|---|---|---|---|---|
| RF001 | HU01 | CU01 | `api/v1/routers/auth.py` | `pages/LoginPage.tsx` | CP01, CP02 (+ `test_auth.py`) | Pasó |
| RF002 | HU02 | CU02 | `api/v1/dependencies.py::require_role` | `components/layout/Sidebar.tsx` | CP03 | Pasó |
| RF003 | HU03 | CU03, CU04 | `api/v1/routers/clients.py`, `application/clients/use_cases.py` | `pages/ClientsListPage.tsx`, `ClientFormPage.tsx`, `ClientDetailPage.tsx` | CP04, CP05, CP06 (+ `test_clients.py`) | Pasó |
| RF004 | HU04 | CU05 | `api/v1/routers/memberships.py`, `application/memberships/use_cases.py` | `pages/ClientDetailPage.tsx` (asignar/renovar/cambiar plan), `MembershipsPage.tsx` (tablero) | CP07 (+ `test_memberships.py`, CP29-36, CP37-46) | Pasó |
| RF005 | HU05 | CU06 | `api/v1/routers/payments.py`, `application/payments/use_cases.py` | `pages/ClientDetailPage.tsx` (pestaña Pagos) | CP08 (+ `test_payments.py`, CP27-28) | Pasó |
| RF006 | HU06 | CU07 | `application/memberships/use_cases.py::DetectExpiringMembershipsUseCase`, `infrastructure/scheduler.py` | `pages/MembershipsPage.tsx` ("Revisar vencimientos ahora"), alertas del Dashboard | CP09 (+ `test_notifications.py`, `test_scheduler.py`) | Pasó |
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

## Modelo de datos (18 tablas)

Ver `docs/diagrama-entidad-relacion.svg` y `backend/MODELO-DATOS.md` para el
detalle completo de columnas/constraints de cada una de las 18 tablas.
