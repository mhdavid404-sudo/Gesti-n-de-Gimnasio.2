# Resultados de pruebas — Entrega 3

Fecha de cierre: 2026-11-04. Todos los números de esta página salen de una
corrida real de `pytest` (nunca estimados o inventados) y de verificación
manual en navegador sobre datos reales del script de seed (`backend/seed.py`).

## Resultado real de pytest

```
docker compose exec backend pytest -q
88 passed, 1 warning in 255.18s (0:04:15)
```

88/88 casos automatizados en verde, 0 fallos, al cierre de la Entrega 3.
(Partía de 75/75 en la auditoría de arranque — Fase 1 agregó 3 casos
[`test_scheduler.py` ×2, `test_memberships.py::test_listar_planes_sin_autenticacion_es_publico`
×1], Fase 2/3 agregó los 10 de abajo: 75 + 3 + 10 = 88.)

> Nota de proceso: correr dos invocaciones de `pytest` en paralelo contra la
> misma base de desarrollo genera fallos cruzados (`TRUNCATE` de aislamiento
> de una corrida pisa a la otra a mitad de prueba) — no es una regresión del
> código. Esta entrega se corrió siempre una invocación a la vez.

| Archivo | Casos | Módulo / RF |
|---|---|---|
| test_auth.py | 7 | RF001/002 — Login, roles |
| test_clients.py | 10 | RF003 — Clientes |
| test_memberships.py | 11 | RF004 — Membresías |
| test_payments.py | 9 | RF005 — Pagos (7 Entrega 2 + CP27-28 desglose) |
| test_services.py | 8 | RF004/RF005 Fase 2 — Planes y servicios extra (CP19-26) |
| test_notifications.py | 7 | RF006 — Vencimientos y notificaciones |
| test_scheduler.py | 2 | RF006 — Automatización diaria (Fase 1) |
| test_routines.py | 10 | RF007/008/012 — Rutinas |
| test_diets.py | 8 | RF009 — Dietas |
| test_progress.py | 7 | RF010/011 — Progreso corporal |
| test_audit_logs.py | 5 | RF015 — Bitácora |
| test_cp17_documentacion_api.py | 2 | RF014 — Documentación de la API |
| test_health.py | 2 | Salud del servicio |
| **Total** | **88** | |

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

Resultado: los 5 pasos funcionaron sin errores en la primera corrida.

## Bugs encontrados en esta entrega

Ninguno nuevo (BUG-01 a BUG-07, de entregas anteriores, siguen cerrados —
ver `DECISIONES.md`). La Fase 2 no introdujo ningún defecto detectado por
pytest ni por la verificación manual en navegador.

## Resumen

- **88/88 pruebas automatizadas en verde** (0 fallos) al cierre de la
  Entrega 3.
- **10 casos nuevos** (CP19–CP28) cubren exactamente las reglas de negocio
  explícitas del encargo de Fase 2: desactivar-vs-eliminar, congelamiento
  de precio, exclusión de cobro doble, permisos de catálogo, y vista
  recortada del entrenador.
- **0 bugs nuevos abiertos.**
