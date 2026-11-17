# Estado actual del sistema — SmartGym v2 (cierre final, 23 nov 2026)

Fecha de la auditoría de arranque: 2026-11-04. Fecha de cierre final
(auditoría completa documentación-vs-código, pruebas, despliegue y
evidencias): 2026-11-16. Verificado contra el código real (no contra
documentación anterior) y contra una corrida limpia de `pytest` (ver abajo).
Este archivo documenta el estado FINAL; el detalle del recorrido vive en
`DECISIONES.md`, `docs/AUDITORIA-DOC-VS-CODIGO.md`,
`docs/RESULTADOS-FINALES.md` y `docs/PUESTA-EN-PRODUCCION.md`.

## Resultado de pytest (real, no estimado — cierre de Entrega 3)

```
docker compose exec backend pytest -q
106 passed, 1 warning in 303.25s (0:05:03)
```

106/106 casos automatizados en verde, 0 fallos, al cierre de la Entrega 3
(partía de 75/75 en la auditoría de arranque; ver desglose completo en
`docs/RESULTADOS-ENTREGA-3.md`).

| Archivo | Casos |
|---|---|
| test_auth.py | 7 |
| test_clients.py | 10 |
| test_memberships.py | 19 |
| test_payments.py | 9 |
| test_services.py | 8 |
| test_change_plan.py | 10 |
| test_notifications.py | 7 |
| test_scheduler.py | 2 |
| test_routines.py | 10 |
| test_diets.py | 8 |
| test_progress.py | 7 |
| test_audit_logs.py | 5 |
| test_cp17_documentacion_api.py | 2 |
| test_health.py | 2 |
| **Total** | **106** |

## Tabla RF001–RF015

| RF | Backend | Front conectado a la API | Prueba | Estado |
|---|---|---|---|---|
| RF001/002 — Login, roles | Completo (JWT, bcrypt, `require_role`) | Completo (`LoginPage`, sesión real) | 7 casos (`test_auth.py`) | **Completo** |
| RF003 — Clientes (CRUD) | Completo (`POST/GET/PATCH/DELETE /clients`) | Completo (listado, alta, edición, detalle, confirmación de borrado) | 10 casos (`test_clients.py`) | **Completo** |
| RF004 — Membresías + Planes y servicios extra (Fase 2) | Completo, incluye catálogo de servicios, inclusión por plan, contratación de extras con precio congelado, tablero de membresías activas (`GET /memberships/board`), renovación (`POST /memberships/{id}/renew`) y cambio de plan con cancelación automática de extras incluidos (`POST /memberships/{id}/change-plan`) | Completo (`MembershipsPage` = tablero operativo de activas; `PlanesServiciosPage` = único lugar con el catálogo; extras + "Cambiar plan" en `ClientDetailPage`) | 19 + 8 + 10 casos (`test_memberships.py`, `test_services.py`, `test_change_plan.py`) | **Completo** |
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

## Ajuste de UX: "Membresías" pasa de catálogo a tablero operativo

La pantalla "Membresías" dejó de mostrar las tarjetas de planes (duplicaban
el catálogo, que ahora vive SOLO en "Planes y servicios") y pasó a ser un
tablero de membresías ACTIVAS: indicadores (total activas, por vencer en 7
días, ingresos del mes -- solo Admin), tabla con cliente/plan/extras
activos/fechas/días restantes resaltando lo próximo a vencer, búsqueda por
nombre y filtro por plan, y acciones por fila (ver ficha, renovar, cobrar).
`cliente` no accede a este tablero (403): sigue viendo su propia membresía
en la misma ruta. Backend nuevo: `GET /memberships/board` (con filtros,
indicadores sin filtrar) y `POST /memberships/{id}/renew`. Ver
`DECISIONES.md`, entrada "Ajuste de UX: Membresías pasa a tablero de
activas".

## Cambio de plan: efecto en servicios extra (amplía RF004/RF005)

Al cambiar el plan de un cliente, los extras activos que el plan nuevo ya
incluye se cancelan automáticamente (`status =
"cancelado_por_cambio_de_plan"`, dejan de cobrarse); los que no incluye se
conservan; los servicios que el plan viejo traía y el nuevo no (bajada de
plan) pasan a "contratables" pero nunca se agregan ni se cobran solos.
Flujo en dos pasos (previsualizar sin guardar, confirmar en una sola
transacción atómica), con `AuditLog` + `Notification` al cliente. El
entrenador deja de ver un extra cancelado. Botón "Cambiar plan" (solo
Admin) en la ficha del cliente, pestaña Membresía. Reembolso/saldo a favor
queda **pendiente de validar con el cliente real** -- por default no se
calcula ningún prorrateo, solo se informa el monto ya pagado y un campo
"Notas" para el acuerdo. Ver `DECISIONES.md`, entrada "Cambio de plan:
efecto en servicios extra".

## Cierre final (23 de noviembre de 2026)

Auditoría completa documentación-vs-código (`docs/AUDITORIA-DOC-VS-CODIGO.md`),
resultados finales de pruebas (`docs/RESULTADOS-FINALES.md`), verificación
de despliegue desde un clon limpio (`docs/PUESTA-EN-PRODUCCION.md`), matriz
de trazabilidad real (`docs/MATRIZ-TRAZABILIDAD-REAL.md`), ERD actualizado
de 18 tablas (`docs/diagrama-entidad-relacion.svg`), capturas por rol
(`docs/capturas/`), ramas remotas revisadas sin fusionar nada
(`docs/RAMAS-PENDIENTES.md`) y pendientes que requieren una persona
(`docs/PENDIENTES-HUMANOS.md`). Hallazgo principal: la sección 3.4 de la
ampliación de RF004/RF005 no existe en el `.docx` fuente -- no se editó el
documento, se reportó (ver `docs/AUDITORIA-DOC-VS-CODIGO.md` y
`docs/PENDIENTES-HUMANOS.md`). El repositorio se limpió de nombres de
agentes/"Claude" (código, comentarios y documentos de planeación interna).

## Backlog heredado

- **11 inconsistencias de alineación de modelo backend↔frontend (Entrega 1):** resueltas al arranque de Entrega 2 vía migración aditiva `0002_backlog_alineacion_modelo` (ver `DECISIONES.md`, "Resolución del backlog de alineación de modelo (B0)"). Cerrado, no reabierto.
- **BUG-01 a BUG-07:** todos corregidos y verificados en su momento (ver `DECISIONES.md` y `docs/RESULTADOS-ENTREGA-2.md` si existe, o la bitácora de bugs del documento de entrega). Ninguno sigue abierto.
- **BUG-08 a BUG-10:** encontrados y corregidos durante la implementación del cambio de plan (ver `docs/RESULTADOS-ENTREGA-3.md` para el detalle de repro/corrección). Ninguno sigue abierto.
- **BUG-11:** encontrado y corregido durante este cierre final, al agregar la advertencia específica de CU04 (ver `docs/RESULTADOS-FINALES.md`). No sigue abierto.

## Estado de cierre

Fase 0 (auditoría), Fase 1 (pendientes RF001-RF015), Fase 2 (Planes y
servicios extra), Fase 3 (pruebas CP19-28 y documentación), el ajuste de UX
de Membresías, el cambio de plan y el cierre final (auditoría completa,
despliegue verificado, evidencias) completos. 106/106 pruebas automatizadas
en verde. No hay RF en estado "Parcial" o "Pendiente". Los únicos pendientes
reales requieren una persona, no código -- ver `docs/PENDIENTES-HUMANOS.md`.
