# Estado actual del sistema — SmartGym v2 (Entrega 3, cierre)

Fecha de la auditoría de arranque: 2026-11-04. Fecha de cierre (Fase 1+2+3
completas): 2026-11-04. Verificado contra el código real (no contra
documentación anterior) y contra una corrida limpia de `pytest` (ver abajo).
Este archivo documenta el estado FINAL; el detalle del recorrido (qué se
encontró en la auditoría y cómo se resolvió cada punto) vive en
`DECISIONES.md` y en `docs/RESULTADOS-ENTREGA-3.md`.

## Resultado de pytest (real, no estimado — cierre de Entrega 3)

```
docker compose exec backend pytest -q
88 passed, 1 warning in 255.18s (0:04:15)
```

88/88 casos automatizados en verde, 0 fallos, al cierre de la Entrega 3
(partía de 75/75 en la auditoría de arranque; ver desglose completo y los
10 casos nuevos de Fase 2 en `docs/RESULTADOS-ENTREGA-3.md`).

| Archivo | Casos |
|---|---|
| test_auth.py | 7 |
| test_clients.py | 10 |
| test_memberships.py | 11 |
| test_payments.py | 9 |
| test_services.py | 8 |
| test_notifications.py | 7 |
| test_scheduler.py | 2 |
| test_routines.py | 10 |
| test_diets.py | 8 |
| test_progress.py | 7 |
| test_audit_logs.py | 5 |
| test_cp17_documentacion_api.py | 2 |
| test_health.py | 2 |
| **Total** | **88** |

## Tabla RF001–RF015

| RF | Backend | Front conectado a la API | Prueba | Estado |
|---|---|---|---|---|
| RF001/002 — Login, roles | Completo (JWT, bcrypt, `require_role`) | Completo (`LoginPage`, sesión real) | 7 casos (`test_auth.py`) | **Completo** |
| RF003 — Clientes (CRUD) | Completo (`POST/GET/PATCH/DELETE /clients`) | Completo (listado, alta, edición, detalle, confirmación de borrado) | 10 casos (`test_clients.py`) | **Completo** |
| RF004 — Membresías + Planes y servicios extra (Fase 2) | Completo, incluye catálogo de servicios, inclusión por plan y contratación de extras con precio congelado | Completo (`MembershipsPage`, `PlanesServiciosPage`, extras en `ClientDetailPage`) | 11 + 8 casos (`test_memberships.py`, `test_services.py`) | **Completo** |
| RF005 — Pagos + desglose (Fase 2) | Completo, incluye desglose plan/extras por línea | Completo (pestaña "Pagos" en `ClientDetailPage`, con desglose opcional) | 9 casos (`test_payments.py`) | **Completo** |
| RF006 — Vencimientos y notificaciones | Completo, con detección automática diaria (APScheduler, 06:00 CDMX) además del disparo manual | Completo (alertas, notificaciones) | 7 + 2 casos (`test_notifications.py`, `test_scheduler.py`) | **Completo** |
| RF007/008/012 — Rutinas | Completo | Completo (`RoutinesPage`, `ClientDetailPage`) | 10 casos (`test_routines.py`) | **Completo** |
| RF009 — Dietas | Completo | Completo (`DietsPage`, `ClientDetailPage`) | 8 casos (`test_diets.py`) | **Completo** |
| RF010/011 — Progreso corporal | Completo | Completo (`ProgressPage`, `ClientDetailPage`) | 7 casos (`test_progress.py`) | **Completo** |
| RF013 — Cliente solo lectura | Completo (ownership por dato en cada router) | Completo (sin controles de alta/edición en ningún módulo para ese rol) | cubierto dentro de cada archivo de pruebas anterior | **Completo** |
| RF014 — API documentada | Completo (`/docs`) | — | 2 casos (`test_cp17_documentacion_api.py`) | **Completo** |
| RF015 — Bitácora (AuditLog) | Completo (registro automático vía manejador de excepciones global) | Completo (`/bitacora`, solo admin) | 5 casos (`test_audit_logs.py`) | **Completo** |

## Hallazgos de la auditoría de arranque — todos cerrados

Los 7 hallazgos originales de la auditoría de arranque (mocks en Dashboard y
Landing, `ConfirmDialog` sin conectar, falta de automatización de
vencimientos, falta de script de seed, `backend/README.md` desactualizado,
verificación del rol "Recepcionista") se resolvieron en Fase 1 — ver el
detalle de diseño y verificación de cada uno en `DECISIONES.md`, entrada
"Arranque de Entrega 3: auditoría y Fase 1". Ninguno sigue abierto.

## Fase 2 — Planes y servicios extra (amplía RF004/RF005)

Catálogo de servicios (`Service`), qué servicios incluye cada plan
(`PlanService`), contratación de extras con precio congelado
(`MembershipService.price_at_purchase`) y desglose de pago por línea
(`PaymentItem`) — backend y frontend completos, ver `DECISIONES.md` (dos
entradas: backend y frontend) para el diseño y las 4 ambigüedades resueltas.
Verificado en navegador con datos reales del seed (catálogo, inclusión por
plan, extras contratados, desglose de pago) — ver
`docs/RESULTADOS-ENTREGA-3.md`.

## Backlog heredado

- **11 inconsistencias de alineación de modelo backend↔frontend (Entrega 1):** resueltas al arranque de Entrega 2 vía migración aditiva `0002_backlog_alineacion_modelo` (ver `DECISIONES.md`, "Resolución del backlog de alineación de modelo (B0)"). Cerrado, no reabierto.
- **BUG-01 a BUG-07:** todos corregidos y verificados en su momento (ver `DECISIONES.md` y `docs/RESULTADOS-ENTREGA-2.md` si existe, o la bitácora de bugs del documento de entrega). Ninguno sigue abierto.
- **0 bugs nuevos** encontrados durante la Entrega 3 (ver `docs/RESULTADOS-ENTREGA-3.md`).

## Estado de cierre

Fase 0 (auditoría), Fase 1 (pendientes RF001-RF015), Fase 2 (Planes y
servicios extra) y Fase 3 (pruebas CP19-28 y documentación) completas. 88/88
pruebas automatizadas en verde. No hay RF en estado "Parcial" o "Pendiente".
