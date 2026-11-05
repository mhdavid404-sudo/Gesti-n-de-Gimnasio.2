# Resultados de pruebas — Entrega 3

Fecha de cierre: 2026-11-05. Todos los números de esta página salen de una
corrida real de `pytest` (nunca estimados o inventados) y de verificación
manual en navegador sobre datos reales del script de seed (`backend/seed.py`).

## Resultado real de pytest

```
docker compose exec backend pytest -q
106 passed, 1 warning in 303.25s (0:05:03)
```

106/106 casos automatizados en verde, 0 fallos, al cierre de la Entrega 3.
(Partía de 75/75 en la auditoría de arranque — Fase 1 agregó 3 casos
[`test_scheduler.py` ×2, `test_memberships.py::test_listar_planes_sin_autenticacion_es_publico`
×1], Fase 2 agregó 10 [CP19-28], el ajuste de UX de Membresías agregó 8
[CP29-36], el cambio de plan agregó 10 más [CP37-46]:
75 + 3 + 10 + 8 + 10 = 106.)

> Nota de proceso: correr dos invocaciones de `pytest` en paralelo contra la
> misma base de desarrollo genera fallos cruzados (`TRUNCATE` de aislamiento
> de una corrida pisa a la otra a mitad de prueba) — no es una regresión del
> código. Esta entrega se corrió siempre una invocación a la vez.

| Archivo | Casos | Módulo / RF |
|---|---|---|
| test_auth.py | 7 | RF001/002 — Login, roles |
| test_clients.py | 10 | RF003 — Clientes |
| test_memberships.py | 19 | RF004 — Membresías (11 Entrega 2 + CP29-36 tablero/renovar) |
| test_payments.py | 9 | RF005 — Pagos (7 Entrega 2 + CP27-28 desglose) |
| test_services.py | 8 | RF004/RF005 Fase 2 — Planes y servicios extra (CP19-26) |
| test_change_plan.py | 10 | RF004/RF005 — Cambio de plan (CP37-46) |
| test_notifications.py | 7 | RF006 — Vencimientos y notificaciones |
| test_scheduler.py | 2 | RF006 — Automatización diaria (Fase 1) |
| test_routines.py | 10 | RF007/008/012 — Rutinas |
| test_diets.py | 8 | RF009 — Dietas |
| test_progress.py | 7 | RF010/011 — Progreso corporal |
| test_audit_logs.py | 5 | RF015 — Bitácora |
| test_cp17_documentacion_api.py | 2 | RF014 — Documentación de la API |
| test_health.py | 2 | Salud del servicio |
| **Total** | **106** | |

## CP19–CP28 — Casos nuevos de Fase 2 (Planes y servicios extra)

| CP | Caso | Archivo | Resultado |
|---|---|---|---|
| CP19 | Eliminar un plan CON membresías contratadas → se desactiva (`is_active=False`), no se borra | `test_services.py` | Pasó |
| CP20 | Eliminar un plan SIN membresías → se elimina de verdad | `test_services.py` | Pasó |
| CP21 | Eliminar un servicio CON contrataciones → se desactiva | `test_services.py` | Pasó |
| CP22 | Eliminar un servicio SIN contrataciones → se elimina de verdad | `test_services.py` | Pasó |
| CP23 | Cambiar el precio de un servicio después de contratado no afecta `price_at_purchase` ya congelado | `test_services.py` | Pasó |
| CP24 | Contratar un servicio ya incluido en el plan del cliente → 409 | `test_services.py` | Pasó |
| CP25 | Alta/edición/eliminación de catálogo (planes y servicios) como no-admin → 403 | `test_services.py` | Pasó |
| CP26 | `GET /memberships/{id}/services`: entrenador ve la lista sin `price_at_purchase`; admin/cliente sí la ven | `test_services.py` | Pasó |
| CP27 | Desglose de pago (`items`) cuya suma no coincide con `amount` → 400 | `test_payments.py` | Pasó |
| CP28 | Desglose de pago exitoso → cada línea se guarda y se devuelve en `items` | `test_payments.py` | Pasó |

## CP29–CP36 — Tablero de membresías activas + renovar (ajuste de UX)

| CP | Caso | Archivo | Resultado |
|---|---|---|---|
| CP29 | Tablero como admin: indicadores (total activas, por vencer en 7 días, ingresos del mes) + tabla | `test_memberships.py` | Pasó |
| CP30 | Tablero como entrenador: solo sus clientes asignados, `monthly_revenue` siempre `null` | `test_memberships.py` | Pasó |
| CP31 | Tablero como cliente → 403 (no accede, consulta su propia membresía en `GET /memberships`) | `test_memberships.py` | Pasó |
| CP32 | Filtros por plan y por nombre acotan la tabla sin afectar los indicadores (totales) | `test_memberships.py` | Pasó |
| CP33 | Renovar una membresía vigente extiende `end_date` desde la vigencia actual | `test_memberships.py` | Pasó |
| CP34 | Renovar una membresía vencida la reactiva (`status="activa"`) desde hoy | `test_memberships.py` | Pasó |
| CP35 | Renovar como no-admin → 403 | `test_memberships.py` | Pasó |
| CP36 | Renovar una membresía inexistente → 404 | `test_memberships.py` | Pasó |

## CP37–CP46 — Cambio de plan: efecto en servicios extra

| CP | Caso | Archivo | Resultado |
|---|---|---|---|
| CP37 | Subir de plan con un extra incluido en el plan nuevo: el extra queda cancelado y no se cobra | `test_change_plan.py` | Pasó |
| CP38 | Subir de plan con un extra NO incluido en el plan nuevo: se conserva | `test_change_plan.py` | Pasó |
| CP39 | Bajar de plan: los servicios que se dejan de incluir no se agregan ni se cobran solos | `test_change_plan.py` | Pasó |
| CP40 | El historial de pagos y de extras no se borra tras el cambio | `test_change_plan.py` | Pasó |
| CP41 | Atomicidad: plan destino inexistente → 404, ni el plan ni los extras cambian | `test_change_plan.py` | Pasó |
| CP42 | Entrenador y Cliente no pueden previsualizar ni confirmar un cambio de plan → 403 | `test_change_plan.py` | Pasó |
| CP43 | Previsualizar no persiste nada | `test_change_plan.py` | Pasó |
| CP44 | Confirmar genera un `AuditLog` (incluye las notas) y una `Notification` al cliente | `test_change_plan.py` | Pasó |
| CP45 | Cambiar al mismo plan ya asignado → 400 | `test_change_plan.py` | Pasó |
| CP46 | Cambiar a un plan desactivado → 400 | `test_change_plan.py` | Pasó |

## CP01–CP18 — Casos heredados (Entregas 1/2)

Cubren Auth/roles, Clientes, Membresías (sin la extensión de Fase 2), Pagos
(sin desglose), Vencimientos/notificaciones, Rutinas, Dietas, Progreso,
Bitácora y documentación de la API — ver `docs/Plan-de-Pruebas-SmartGym-v2.docx`
para el enunciado original de cada caso y la tabla de archivos arriba para su
ubicación real en el código. Los 75 casos automatizados de esta familia
siguen en verde sin ningún cambio tras la Fase 2 (ver corrida completa
arriba) — la ampliación de Memberships/Pagos no rompió ningún caso
existente.

## Verificación manual (navegador, sobre datos reales del seed)

No automatizada por pytest (verificación de interfaz, no de API):

1. Login como `admin@demo.com` → pantalla "Planes y servicios" muestra los 3
   planes reales del seed (Básica $399, VIP $649, Premium $999).
2. Expandir el plan Básica → checklist de servicios incluidos marca
   correctamente "Casillero individual" (único servicio incluido en ese
   plan según el seed).
3. Pestaña "Servicios extra" → los 6 servicios del seed aparecen con precio,
   periodo de facturación y estado "Activa".
4. Ficha del cliente demo (`cliente@demo.com`), pestaña Membresía →
   "Servicios incluidos en el plan" muestra "Casillero individual";
   "Extras contratados" muestra "Entrenador asignado ($450)", el extra
   sembrado por `seed.py`.
5. Pestaña Pagos → registrar un pago nuevo marcando el desglose (Plan $399 +
   Entrenador asignado $450): el monto se auto-calcula a $849, el pago se
   guarda y el historial muestra el desglose textual correcto.
6. Botón "Cambiar plan" (ficha del cliente demo, pestaña Membresía) →
   seleccionar Premium → "Ver resumen" muestra "Básica ($399) → Premium
   ($999) +$600 / mes" y "Se cancelarán por estar incluidos en el nuevo
   plan: Entrenador asignado — ya pagado: $450". Con una nota en "Notas" →
   "Confirmar cambio" → toast "Plan cambiado a 'Premium'.", el plan y sus
   beneficios se actualizan al instante, y "Extras contratados" muestra
   "Entrenador asignado" con el pill "Cancelado (cambio de plan)" y
   `end_date` en la fecha de hoy.
7. Pestaña Pagos del mismo cliente → el desglose ya solo ofrece "Plan
   Premium — $999", "Entrenador asignado" desapareció de la lista
   cobrable (confirma el fix de BUG-10).
8. Login como `entrenador@demo.com` → misma ficha, pestaña Membresía →
   "Extras contratados: Sin extras contratados." (el extra cancelado ya no
   le aparece) y sin botón "Cambiar plan" (admin-only).

Resultado: los 8 pasos funcionaron sin errores en la primera corrida.

## Reporte de "textos con traducciones raras" ("AVIONES", "PERSONAJE", "DE
PRIMERA CALIDAD", "ANUNCIO", "Cajero compartido")

Búsqueda exhaustiva (`grep` case-insensitive de las 5 cadenas reportadas en
todo el repositorio, incluido `backend/seed.py`) + verificación en vivo en
el navegador (landing pública, tablero de membresías, encabezado con
avatar). **Ninguna de las 5 existe en el código ni en lo renderizado**: el
avatar ya muestra las iniciales reales del usuario (`Topbar.tsx`), el seed
ya dice "Casillero compartido", y los nombres de plan ya son
"Básica"/"VIP"/"Premium" en todas las pantallas. No se fabricó ningún
cambio sobre texto que no existe -- ver `DECISIONES.md`, entrada "Ajuste de
UX: Membresías pasa a tablero de activas", punto 6.

## Bugs encontrados en esta entrega

BUG-01 a BUG-07 (de entregas anteriores) siguen cerrados — ver
`DECISIONES.md`. Ni la Fase 2 ni el ajuste de UX de Membresías introdujeron
ningún defecto. La implementación del cambio de plan sí encontró 3 bugs
reales, los 3 corregidos antes del cierre:

| Bug | Repro | Corrección | Estado |
|---|---|---|---|
| BUG-08 | `POST /memberships/{id}/change-plan` con un extra a cancelar → `500 Internal Server Error` (`StringDataRightTruncation`): `membership_services.status` era `VARCHAR(20)`, y `"cancelado_por_cambio_de_plan"` tiene 29 caracteres | Columna ensanchada a `VARCHAR(40)` en la migración `0004`, antes de ampliar el `CHECK` | Corregido |
| BUG-09 | Tras corregir BUG-08, `GET /memberships/{id}/services` y `GET /notifications/users/{id}` devolvían `500` al serializar un registro con el status/tipo nuevo: los `Literal` de Pydantic (`MembershipServiceStatus`, `NotificationType`) no incluían los valores nuevos | Ambos `Literal` ampliados (backend) y sus espejos en `frontend/src/types/api.ts` | Corregido |
| BUG-10 | Bug preexistente (latente, nunca antes alcanzable): `ClientDetailPage.tsx` calculaba qué servicios bloquean una nueva contratación / se ofrecen en el desglose de pago sobre TODOS los extras del cliente, sin filtrar por `status` -- un extra cancelado por cambio de plan habría bloqueado recontratar ese servicio para siempre y habría seguido ofreciéndose (mal) en el desglose de pago | `activeContractedServices` (filtrado a `status === 'activa'`), usado en ambos lugares | Corregido |

Los 3 se encontraron durante la verificación manual vía `curl` (antes de
escribir las pruebas automatizadas) y quedan cubiertos por
`test_change_plan.py` (BUG-08/09, indirectamente -- cualquier aserción
sobre el status nuevo habría fallado con el bug presente) y por revisión
de código (BUG-10, no tiene cobertura automatizada de frontend en este
proyecto).

## Resumen

- **106/106 pruebas automatizadas en verde** (0 fallos) al cierre de la
  Entrega 3.
- **28 casos nuevos en total**: CP19–CP28 (Fase 2, Planes y servicios
  extra), CP29–CP36 (tablero de membresías activas + renovar) y CP37–CP46
  (cambio de plan).
- **3 bugs encontrados y corregidos** (BUG-08 a BUG-10, ver tabla arriba).
  0 bugs abiertos.
