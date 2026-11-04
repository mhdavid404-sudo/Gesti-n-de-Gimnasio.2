# Estado actual del sistema — SmartGym v2 (auditoría de arranque, Entrega 3)

Fecha de la auditoría: 2026-11-04. Verificado contra el código real (no contra
documentación anterior) y contra una corrida limpia de `pytest` (ver abajo).

## Resultado de pytest (real, no estimado)

```
docker compose exec backend pytest tests/ -v
================== 75 passed, 1 warning in 249.20s (0:04:09) ===================
```

75/75 casos automatizados en verde, 0 fallos, al cierre de la auditoría.

| Archivo | Casos |
|---|---|
| test_auth.py | 7 |
| test_clients.py | 10 |
| test_memberships.py | 10 |
| test_payments.py | 7 |
| test_notifications.py | 7 |
| test_routines.py | 10 |
| test_diets.py | 8 |
| test_progress.py | 7 |
| test_audit_logs.py | 5 |
| test_cp17_documentacion_api.py | 2 |
| test_health.py | 2 |
| **Total** | **75** |

## Tabla RF001–RF015

| RF | Backend | Front conectado a la API | Prueba | Estado |
|---|---|---|---|---|
| RF001/002 — Login, roles | Completo (JWT, bcrypt, `require_role`) | Completo (`LoginPage`, sesión real) | 7 casos (`test_auth.py`) | **Completo** |
| RF003 — Clientes (CRUD) | Completo (`POST/GET/PATCH/DELETE /clients`) | Completo (listado, alta, edición, detalle) salvo un hueco de UX (ver abajo) | 10 casos (`test_clients.py`) | **Parcial** — falta confirmación antes de eliminar en la interfaz |
| RF004 — Membresías | Completo | Completo (`MembershipsPage`) | 10 casos (`test_memberships.py`) | **Completo** (se amplía en Fase 2 sin romper lo existente) |
| RF005 — Pagos | Completo | Completo (pestaña "Pagos" en `ClientDetailPage`) | 7 casos (`test_payments.py`) | **Completo** (se amplía en Fase 2 con desglose) |
| RF006 — Vencimientos y notificaciones | Completo, pero el detector solo se dispara a mano (`POST /memberships/detect-expiring`, solo admin) | Completo (alertas, notificaciones) | 7 casos (`test_notifications.py`) | **Parcial** — falta automatización diaria real |
| RF007/008/012 — Rutinas | Completo | Completo (`RoutinesPage`, `ClientDetailPage`) | 10 casos (`test_routines.py`) | **Completo** |
| RF009 — Dietas | Completo | Completo (`DietsPage`, `ClientDetailPage`) | 8 casos (`test_diets.py`) | **Completo** |
| RF010/011 — Progreso corporal | Completo | Completo (`ProgressPage`, `ClientDetailPage`) | 7 casos (`test_progress.py`) | **Completo** |
| RF013 — Cliente solo lectura | Completo (ownership por dato en cada router) | Completo (sin controles de alta/edición en ningún módulo para ese rol) | cubierto dentro de cada archivo de pruebas anterior | **Completo** |
| RF014 — API documentada | Completo (`/docs`) | — | 2 casos (`test_cp17_documentacion_api.py`) | **Completo** |
| RF015 — Bitácora (AuditLog) | Completo (registro automático vía manejador de excepciones global) | Completo (`/bitacora`, solo admin) | 5 casos (`test_audit_logs.py`) | **Completo** |

## Hallazgos adicionales (no ligados a un único RF)

1. **`DashboardPage.tsx` sigue importando datos mock** (`auditLogs`, `clients`, `payments` de `mocks/data`) para 3 cifras del bloque "En números"/"Última acción registrada" (clientes activos, ingresos del mes, última acción). El resto del Dashboard ya usa la API real. — **Parcial**, se corrige en Fase 1.
2. **`LandingPage.tsx` (página pública) sigue usando el catálogo mock de planes** (`membershipPlans`). El catálogo interno real ya existe (`GET /membership-plans`), pero ese endpoint exige sesión, así que la landing pública no puede consumirlo tal cual. — **Parcial**, se corrige en Fase 1 (se vuelve público el listado, que no es información sensible).
3. **`ConfirmDialog` existe pero nunca se usa.** Ninguna pantalla del panel borra nada todavía con confirmación — es el motivo exacto por el que RF003 queda "Parcial" arriba.
4. **No existe infraestructura de automatización** (scheduler/cron) para el detector de vencimientos (RF006) — documentado como limitación conocida desde Entrega 2. Se resuelve en Fase 1 con un job diario en proceso (APScheduler).
5. **No existe script de seed oficial.** Las cuentas/datos de demostración usadas hasta ahora se crearon a mano vía API en cada sesión — y se pierden cada vez que corre la suite de pytest completa (TRUNCATE). Pendiente desde Entrega 2, se resuelve en Fase 1.
6. **`backend/README.md` desactualizado**: sigue fechado "Entrega 1" y menciona nombres de integrantes-agente ("Royer", "Leo", "Cofi") en secciones técnicas — contradice la regla de no mencionar nombres de agentes en código/docs. No existe un `README.md` en la raíz del repo. Se corrige en Fase 3.
7. **Rol "Recepcionista"**: verificado — no existe en el modelo de datos (`ck_users_role` solo permite `admin`/`entrenador`/`cliente`), no existe en el frontend (login, `RoleSwitcher`, formularios), no existe en ningún seed. Las únicas menciones del repo están en `SMARTGYM-V2-BRIEF.md` y `docs/REVISION-UX.md`, como parte de la narrativa del negocio real (el gimnasio *tenía* recepcionistas antes de digitalizarse) — no describen un rol del sistema. **No requiere cambios de código.**

## Backlog heredado

- **11 inconsistencias de alineación de modelo backend↔frontend (Entrega 1):** resueltas al arranque de Entrega 2 vía migración aditiva `0002_backlog_alineacion_modelo` (ver `DECISIONES.md`, "Resolución del backlog de alineación de modelo (B0)"). Cerrado, no reabierto.
- **BUG-01 a BUG-07:** todos corregidos y verificados en su momento (ver `DECISIONES.md` y `docs/RESULTADOS-ENTREGA-2.md` si existe, o la bitácora de bugs del documento de entrega). Ninguno sigue abierto.

## Qué sigue

Fase 1 de esta corrida cierra los puntos 1–5 de arriba (los únicos RF/hallazgos "Parcial" o "Pendiente" reales). Fase 2 amplía RF004/RF005 con Planes y servicios extra. Fase 3 agrega CP19+ y cierra documentación (este archivo se actualiza al final con el estado definitivo).
