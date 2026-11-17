# Resultados finales — SmartGym v2 (cierre, 23 de noviembre de 2026)

Fecha de esta corrida: 2026-11-16. Todos los números de esta página salen de
ejecutar algo de verdad: `docker compose exec backend pytest -v` (salida
literal completa en `docs/RESULTADO-PYTEST-FINAL.txt`, y el baseline de
seguridad previo al cierre en `docs/BASE-PYTEST-ANTES.txt`), más la
verificación con `curl` de `docs/PUESTA-EN-PRODUCCION.md`. Ningún resultado
de esta página es estimado.

## Totales reales

```
docker compose exec backend pytest -v
106 passed, 1 warning in 345.55s (0:05:45)
```

**106/106 casos automatizados en verde, 0 fallos.** Mismo total que el
baseline tomado al arrancar este cierre (`docs/BASE-PYTEST-ANTES.txt`,
también 106/106) — ninguna corrección de este cierre hizo bajar el número
de casos en verde, así que no hizo falta revertir ningún commit.

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

## CP01–CP18 (plan de pruebas original, Tabla 15 del documento)

| CP | Descripción | Resultado | Observación |
|---|---|---|---|
| CP01 | Login con credenciales válidas | Pasó | `test_auth.py` + verificación manual, 3 cuentas demo |
| CP02 | Login con credenciales inválidas | Pasó | `test_login_con_password_incorrecto_devuelve_401` |
| CP03 | Restricción de acceso por rol | Pasó | `test_acceso_con_rol_insuficiente_devuelve_403` |
| CP04 | Registrar cliente nuevo | Pasó | `test_alta_exitosa_de_cliente_como_admin` |
| CP05 | Editar cliente existente | Pasó | `test_editar_cliente_como_admin_actualiza_datos` |
| CP06 | Eliminar cliente | Pasó | `test_eliminar_cliente_como_admin_elimina_correctamente`; advertencia específica agregada en este cierre (CU04) |
| CP07 | Asignar membresía | Pasó | `test_asignar_membresia_exitosa` |
| CP08 | Registrar pago | Pasó | `test_registrar_pago_exitoso_como_admin` |
| CP09 | Detección de membresía vencida | Pasó | automático (scheduler) + manual |
| CP10 | Crear y asignar rutina | Pasó | `test_crear_rutina_como_entrenador_devuelve_created_by_correcto` |
| CP11 | Consultar historial de rutinas | Pasó | `test_historial_como_cliente_ve_lo_propio_pero_no_lo_de_otro` |
| CP12 | Entrenador edita rutina de cliente asignado | Pasó | `test_patch_assignment_como_entrenador_dueno_devuelve_200` |
| CP13 | Crear y asignar plan de dieta | Pasó | `test_asignar_plan_a_cliente_propio_como_entrenador_devuelve_201` |
| CP14 | Registrar progreso corporal | Pasó | `test_registrar_progreso_como_admin_devuelve_201` |
| CP15 | Dashboard de progreso | Pasó | verificación manual (sin prueba de render) |
| CP16 | Cliente solo lectura | Pasó | 7 pruebas de ownership por dato |
| CP17 | Documentación de la API | Pasó | `test_docs_endpoint_serves_swagger_ui` |
| CP18 | Registro de errores en bitácora | Pasó | `test_audit_logs.py` (5 pruebas) |

## CP19–CP46 (ampliación de RF004/RF005)

Ver `docs/RESULTADOS-ENTREGA-3.md` para la tabla detallada (CP19-CP46, 28
casos, todos "Pasó"). Siguen en verde sin cambios en esta corrida final.

## Bugs encontrados en este cierre

BUG-01 a BUG-10 (de entregas y sesiones anteriores) siguen cerrados — ver
`DECISIONES.md`. Esta sesión de cierre encontró y corrigió 1 bug nuevo:

| Bug | Repro | Causa | Corrección | Estado |
|---|---|---|---|---|
| BUG-11 | Al agregar la advertencia específica de CU04 (eliminar cliente con membresía activa), una membresía activa mostrando el estado calculado "por vencer" no disparaba la advertencia -- solo mostraba el texto genérico, como si no tuviera membresía activa | `ClientDetailPage.tsx` comparaba contra `getMembershipDisplayStatus()` (que devuelve `'por_vencer'` para una membresía activa próxima a expirar) en vez de `membership.status` (el dato real en la base, que sigue siendo `"activa"`) | Se compara ahora contra `membership.status === 'activa'` directamente | Corregido, verificado en navegador (commit `139d20d`) |

## Verificación de despliegue

Ver `docs/PUESTA-EN-PRODUCCION.md` — flujo completo (clon limpio → build →
migraciones → seed → `/health` → login de los 3 roles → alta de cliente →
membresía → pago con desglose → cambio de plan) verificado con `curl`, los
5 pasos del flujo exitosos en la primera corrida.

## Resumen

- **106/106 pruebas automatizadas en verde**, igual que el baseline de
  seguridad tomado al arrancar este cierre -- 0 commits revertidos.
- **46 casos de prueba cubiertos en total** (CP01-18 del plan original +
  CP19-46 de la ampliación), todos "Pasó".
- **1 bug nuevo encontrado y corregido** (BUG-11) durante este cierre; 0
  bugs abiertos en todo el proyecto.
- **Despliegue verificado end-to-end desde un clon limpio**, sin ningún
  problema encontrado.
