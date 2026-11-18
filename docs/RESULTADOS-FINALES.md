# Resultados finales — SmartGym v2 (cierre, 23 de noviembre de 2026)

Fecha de esta corrida: 2026-11-16. Todos los números de esta página salen de
ejecutar algo de verdad: `docker compose exec backend pytest -v` (salida
literal completa en `docs/RESULTADO-PYTEST-FINAL.txt`, y el baseline de
seguridad previo al cierre en `docs/BASE-PYTEST-ANTES.txt`), más la
verificación con `curl` de `docs/PUESTA-EN-PRODUCCION.md`. Ningún resultado
de esta página es estimado.

**Actualización 2026-11-18 (restablecer contraseña + editar cliente):** se
agregó el restablecimiento de contraseña por Admin y la edición de datos
de cliente desde la ficha (ver `DECISIONES.md`, entrada "Restablecimiento
de contraseña por Admin + edición de datos de cliente desde la ficha") —
4 casos nuevos, 110/110.

**Actualización 2026-11-18 (pantalla "Usuarios"):** se agregó la pantalla
"Usuarios" -- alta de admin/entrenador, activar/desactivar y bitácora para
ambas acciones (ver `DECISIONES.md`, entrada "Pantalla 'Usuarios' (alta,
restablecer contraseña, activar/desactivar admin/entrenador)") — 3 casos
nuevos más, suite completa corrida de nuevo, **113/113 en verde**. Los
totales de abajo ya reflejan esta corrida.

## Totales reales

```
docker compose exec backend pytest -v
113 passed, 1 warning in 366.97s (0:06:06)
```

**113/113 casos automatizados en verde, 0 fallos** (106 del cierre original
+ 4 del 2026-11-18 de restablecer-contraseña/editar-cliente + 3 del
2026-11-18 de la pantalla "Usuarios"). Ninguna corrección hizo bajar el
número de casos en verde, así que no hizo falta revertir ningún commit.

| Archivo | Casos |
|---|---|
| test_auth.py | 7 |
| test_clients.py | 11 |
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
| test_users.py | 6 |
| **Total** | **113** |

## CP01–CP18 (plan de pruebas original, Tabla 15 del documento)

| CP | Descripción | Resultado | Observación |
|---|---|---|---|
| CP01 | Login con credenciales válidas | Pasó | `test_auth.py` + verificación manual, 3 cuentas demo |
| CP02 | Login con credenciales inválidas | Pasó | `test_login_con_password_incorrecto_devuelve_401` |
| CP03 | Restricción de acceso por rol | Pasó | `test_acceso_con_rol_insuficiente_devuelve_403` |
| CP04 | Registrar cliente nuevo | Pasó | `test_alta_exitosa_de_cliente_como_admin` |
| CP05 | Editar cliente existente | Pasó | `test_editar_cliente_como_admin_actualiza_datos`; pantalla ("Editar datos", ficha del cliente) agregada el 2026-11-18 -- el endpoint ya existía y pasaba, solo faltaba la UI. `test_editar_cliente_como_no_admin_devuelve_403` agregado el mismo día. |
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

## CP47–CP49 (restablecimiento de contraseña por Admin, 2026-11-18)

Sin ID formal en el documento (mismo caso que la ampliación de RF004/RF005
-- ver `DECISIONES.md`). Función nueva: ningún endpoint ni pantalla de
cambio/restablecimiento de contraseña existía antes de esta fecha.

| CP | Descripción | Resultado | Prueba |
|---|---|---|---|
| CP47 | Admin restablece la contraseña de otro usuario | Pasó | `test_restablecer_password_como_admin_funciona_y_queda_en_bitacora` (verifica además que la contraseña anterior deja de servir, la temporal nueva sí funciona, y que queda en `AuditLog`) |
| CP48 | Restablecer contraseña como rol no-admin | Pasó | `test_restablecer_password_como_no_admin_devuelve_403` |
| CP49 | Restablecer contraseña de un usuario inexistente | Pasó | `test_restablecer_password_de_usuario_inexistente_devuelve_404` |

## CP50–CP52 (pantalla "Usuarios": alta, activar/desactivar, 2026-11-18)

Sin ID formal en el documento (mismo caso que CP47-49). Antes de esta
fecha, `POST /users` ya existía pero `RegisterUserUseCase` no registraba
nada en Bitácora, y no existía ninguna regla que impidiera a un admin
desactivar su propia cuenta.

| CP | Descripción | Resultado | Prueba |
|---|---|---|---|
| CP50 | Alta de usuario como admin queda registrada en Bitácora | Pasó | `test_alta_de_usuario_como_admin_queda_en_bitacora` (`test_auth.py` ya cubría el 201 por sí solo, rol no-admin 403 y correo duplicado 409 -- no se duplicaron, solo se agregó la verificación de bitácora que faltaba) |
| CP51 | Admin desactiva y reactiva a otro usuario; ambas acciones quedan en Bitácora | Pasó | `test_desactivar_y_reactivar_usuario_como_admin_queda_en_bitacora` (verifica además que la cuenta no puede iniciar sesión mientras está desactivada, y sí puede al reactivarla) |
| CP52 | Un admin no puede desactivarse a sí mismo | Pasó | `test_admin_no_puede_desactivarse_a_si_mismo` (400; se confirma que sigue pudiendo iniciar sesión) |

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

- **113/113 pruebas automatizadas en verde** (106 del cierre del
  2026-11-16 + 4 de restablecer-contraseña/editar-cliente + 3 de la
  pantalla "Usuarios", ambas del 2026-11-18) -- 0 commits revertidos.
- **52 casos de prueba cubiertos en total** (CP01-18 del plan original +
  CP19-46 de la ampliación de RF004/RF005 + CP47-49 del restablecimiento
  de contraseña + CP50-52 de la pantalla "Usuarios"), todos "Pasó".
- **1 bug nuevo encontrado y corregido** (BUG-11) durante el cierre del
  2026-11-16; 0 bugs abiertos en todo el proyecto. Ninguno de los dos
  agregados del 2026-11-18 (restablecer contraseña/editar cliente, y la
  pantalla "Usuarios") encontró ningún bug nuevo.
- **Despliegue verificado end-to-end desde un clon limpio**, sin ningún
  problema encontrado.
