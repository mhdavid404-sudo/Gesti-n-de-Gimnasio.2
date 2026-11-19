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
nuevos más, suite completa corrida de nuevo, **113/113 en verde**.

**Actualización 2026-11-18 (editar nombre y correo del cliente desde la
ficha):** "Editar datos" se amplió para tocar también la cuenta (`User`)
dueña del perfil, no solo `ClientProfile` (ver `UpdateClientProfileUseCase`)
-- 2 casos nuevos en `test_clients.py` (cambio de nombre/correo con
bitácora y login con el correo nuevo; correo repetido -> 409), suite
completa **115/115 en verde**.

**Actualización 2026-11-18 (BUG-12 -- "Renovar" sin ventana ni cobro, y sin
forma de deshacer):** ver `DECISIONES.md`, entrada "BUG-12". "Renovar" y
"Cobrar" dejan de ser dos acciones separadas (ahora cobran en la misma
operación atómica), solo funcionan dentro de una ventana de 7 días, y se
agrega "Deshacer renovación" (anula el pago sin borrarlo). 7 casos nuevos
(CP53-CP59) + 4 casos existentes ampliados para exigir método de pago y la
nueva ventana — suite completa corrida de nuevo, **122/122 en verde**.

**Actualización 2026-11-18 (editar/eliminar rutinas y dietas):** ver
`DECISIONES.md`, entrada "Editar/eliminar rutinas y dietas". Se agregan
`PATCH`/`DELETE` para el catálogo de rutinas y planes de dieta (eliminar
desactiva en vez de borrar si hay asignaciones existentes) y `PATCH`
ampliado + `DELETE` nuevo para sus asignaciones (corregir "error de dedo"
y quitarla sin perder la bitácora). 17 casos nuevos (9 en
`test_routines.py`, 8 en `test_diets.py`) — suite completa corrida de
nuevo, **139/139 en verde**. Los totales de abajo ya reflejan esta
corrida.

## Totales reales

```
docker compose exec backend pytest tests/ -q
139 passed, 1 warning in 494.47s (0:08:14)
```

**139/139 casos automatizados en verde, 0 fallos** (106 del cierre original
+ 4 del 2026-11-18 de restablecer-contraseña/editar-cliente + 3 del
2026-11-18 de la pantalla "Usuarios" + 2 del 2026-11-18 de editar
nombre/correo + 7 del 2026-11-18 de BUG-12 + 17 del 2026-11-18 de
editar/eliminar rutinas y dietas). Ninguna corrección hizo bajar el número
de casos en verde, así que no hizo falta revertir ningún commit.

| Archivo | Casos |
|---|---|
| test_auth.py | 7 |
| test_clients.py | 13 |
| test_memberships.py | 26 |
| test_payments.py | 9 |
| test_services.py | 8 |
| test_change_plan.py | 10 |
| test_notifications.py | 7 |
| test_scheduler.py | 2 |
| test_routines.py | 19 |
| test_diets.py | 16 |
| test_progress.py | 7 |
| test_audit_logs.py | 5 |
| test_cp17_documentacion_api.py | 2 |
| test_health.py | 2 |
| test_users.py | 6 |
| **Total** | **139** |

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

## CP53–CP59 (BUG-12: renovar + cobrar atómico, ventana de 7 días, deshacer, 2026-11-18)

Sin ID formal en el documento (mismo caso que CP47-52). Ver `DECISIONES.md`,
entrada "BUG-12" para la falla/causa/solución completa. Además de estos 7
casos nuevos, 4 casos existentes de `test_memberships.py` se ampliaron
(ahora exigen `method` en el body y están dentro de la ventana de 7 días):
`test_renovar_membresia_extiende_la_vigencia_y_cobra`,
`test_renovar_membresia_vencida_la_reactiva_desde_hoy`,
`test_renovar_membresia_como_no_admin_devuelve_403`,
`test_renovar_membresia_inexistente_falla`.

| CP | Descripción | Resultado | Prueba |
|---|---|---|---|
| CP53 | Renovar fuera de la ventana de 7 días -> 409, y no cambia nada (atómico: ni la fecha ni los pagos se tocan) | Pasó | `test_renovar_fuera_de_la_ventana_devuelve_409_y_no_cambia_nada` |
| CP54 | Renovar dos veces seguidas (doble clic) -> la segunda falla con 409 | Pasó | `test_renovar_dos_veces_seguidas_la_segunda_falla` |
| CP55 | Deshacer una renovación restaura la fecha de vencimiento anterior, anula el pago (sin borrarlo) y queda en Bitácora | Pasó | `test_deshacer_renovacion_restaura_fecha_y_anula_pago` |
| CP56 | Deshacer una renovación ya deshecha -> 409 | Pasó | `test_deshacer_renovacion_ya_deshecha_devuelve_409` |
| CP57 | Deshacer con una renovación posterior -> 409 (rechazado) | Pasó | `test_deshacer_renovacion_con_renovacion_posterior_devuelve_409` |
| CP58 | Deshacer como no-admin -> 403 | Pasó | `test_deshacer_renovacion_como_no_admin_devuelve_403` |
| CP59 | Un pago anulado no cuenta en los ingresos del mes (tablero de Membresías) | Pasó | `test_pago_anulado_no_cuenta_en_ingresos_del_mes` |

## CP60–CP76 (editar/eliminar rutinas y dietas, 2026-11-18)

Sin ID formal en el documento (mismo caso que CP47-59). Ver `DECISIONES.md`,
entrada "Editar/eliminar rutinas y dietas".

| CP | Descripción | Resultado | Observación |
|---|---|---|---|
| CP60 | Editar rutina como admin -> 200, queda en bitácora | Pasó | `test_editar_rutina_como_admin_actualiza_datos` |
| CP61 | Editar rutina ajena como entrenador -> 403 | Pasó | `test_editar_rutina_ajena_como_entrenador_devuelve_403` |
| CP62 | Eliminar rutina sin asignaciones -> se borra de verdad | Pasó | `test_eliminar_rutina_sin_asignaciones_borra_de_verdad` |
| CP63 | Eliminar rutina con asignaciones -> se desactiva, conserva historial | Pasó | `test_eliminar_rutina_con_asignaciones_la_desactiva` |
| CP64 | Eliminar rutina como cliente -> 403 | Pasó | `test_eliminar_rutina_como_cliente_devuelve_403` |
| CP65 | Corregir una asignación de rutina (rutina/fecha) como entrenador dueño -> 200, queda en bitácora | Pasó | `test_corregir_asignacion_rutina_como_entrenador_dueno_actualiza_y_registra_bitacora` |
| CP66 | Eliminar una asignación de rutina -> 204, desaparece del historial pero la bitácora sobrevive | Pasó | `test_eliminar_asignacion_rutina_borra_la_fila_pero_bitacora_sobrevive` |
| CP67 | Eliminar una asignación de rutina como entrenador no dueño -> 403 | Pasó | `test_eliminar_asignacion_rutina_como_entrenador_no_dueno_devuelve_403` |
| CP68 | Editar una asignación de rutina ya 'completada' nunca la borra | Pasó | `test_editar_asignacion_completada_no_la_elimina` |
| CP69 | Editar plan de dieta como admin -> 200, queda en bitácora | Pasó | `test_editar_plan_como_admin_actualiza_datos` |
| CP70 | Editar plan de dieta ajeno como entrenador -> 403 | Pasó | `test_editar_plan_ajeno_como_entrenador_devuelve_403` |
| CP71 | Eliminar plan de dieta sin asignaciones -> se borra de verdad | Pasó | `test_eliminar_plan_sin_asignaciones_borra_de_verdad` |
| CP72 | Eliminar plan de dieta con asignaciones -> se desactiva, conserva historial | Pasó | `test_eliminar_plan_con_asignaciones_lo_desactiva` |
| CP73 | Eliminar plan de dieta como cliente -> 403 | Pasó | `test_eliminar_plan_como_cliente_devuelve_403` |
| CP74 | Corregir una asignación de dieta (plan/fecha) como entrenador dueño -> 200, queda en bitácora | Pasó | `test_corregir_asignacion_dieta_como_entrenador_dueno_actualiza_y_registra_bitacora` |
| CP75 | Eliminar una asignación de dieta -> 204, bitácora sobrevive | Pasó | `test_eliminar_asignacion_dieta_borra_la_fila_pero_bitacora_sobrevive` |
| CP76 | Eliminar una asignación de dieta como entrenador no dueño -> 403 | Pasó | `test_eliminar_asignacion_dieta_como_entrenador_no_dueno_devuelve_403` |

## Bugs encontrados en este cierre

BUG-01 a BUG-10 (de entregas y sesiones anteriores) siguen cerrados — ver
`DECISIONES.md`. Esta sesión de cierre encontró y corrigió 1 bug nuevo; dos
sesiones posteriores (ambas 2026-11-18) encontraron y corrigieron tres más:

| Bug | Repro | Causa | Corrección | Estado |
|---|---|---|---|---|
| BUG-11 | Al agregar la advertencia específica de CU04 (eliminar cliente con membresía activa), una membresía activa mostrando el estado calculado "por vencer" no disparaba la advertencia -- solo mostraba el texto genérico, como si no tuviera membresía activa | `ClientDetailPage.tsx` comparaba contra `getMembershipDisplayStatus()` (que devuelve `'por_vencer'` para una membresía activa próxima a expirar) en vez de `membership.status` (el dato real en la base, que sigue siendo `"activa"`) | Se compara ahora contra `membership.status === 'activa'` directamente | Corregido, verificado en navegador (commit `139d20d`) |
| BUG-12 | En el tablero de Membresías, "Renovar" estaba disponible siempre (incluso con 154 días restantes) y cada clic sumaba otro periodo sin límite y sin ningún pago asociado; no había forma de deshacer un clic equivocado | `RenewMembershipUseCase` (Entrega 3) se diseñó a propósito sin ventana ni pago ("renovar" y "cobrar" como dos acciones separadas) -- esa decisión de diseño resultó ser el defecto real en uso | Reemplazado por `RenewAndChargeMembershipUseCase` (renueva y cobra en una sola operación atómica, solo dentro de una ventana de 7 días) + `UndoMembershipRenewalUseCase` (deshacer la última renovación, anula el pago sin borrarlo) | Corregido, verificado en navegador y con 7 pruebas automatizadas nuevas (CP53-CP59) |
| BUG-13 | `PATCH /routines/assignments/{id}`/`PATCH /diets/assignments/{id}` con `routine_id`/`diet_plan_id` nuevo devolvía 200 pero el id seguía siendo el viejo -- la corrección de "error de dedo" no corregía nada | `SqlAlchemyRoutineAssignmentRepository.update()`/`SqlAlchemyDietAssignmentRepository.update()` (desde Entrega 2) solo escribían `status`/`notes` en el modelo -- nunca `routine_id`/`assigned_date`/`diet_plan_id`. Invisible hasta ahora porque el `PATCH` original solo tocaba esos dos campos | Ambos repositorios ahora persisten también `routine_id`/`assigned_date`/`diet_plan_id` | Corregido, delatado por el primer caso de prueba de la ampliación (`test_corregir_asignacion_*`), 17 pruebas nuevas en verde |
| BUG-14 | El contenedor Docker del backend quedaba caído (`AssertionError: Status code 204 must not have a response body`) al agregar los `DELETE` nuevos de asignación | Faltaba `response_model=None` en los dos `DELETE` (204) nuevos; `fastapi==0.115.0` (el pin real de `requirements.txt`, el que corre en el contenedor) lo exige, una versión más nueva instalada en el entorno de desarrollo local no -- `pytest` local pasaba igual, sin detectarlo | Se agrega `response_model=None` (mismo patrón que `DELETE /clients/{id}`, que ya lo tenía) | Corregido, confirmado con `docker logs` y verificación en navegador contra el contenedor real |

## Verificación de despliegue

Ver `docs/PUESTA-EN-PRODUCCION.md` — flujo completo (clon limpio → build →
migraciones → seed → `/health` → login de los 3 roles → alta de cliente →
membresía → pago con desglose → cambio de plan) verificado con `curl`, los
5 pasos del flujo exitosos en la primera corrida.

## Resumen

- **139/139 pruebas automatizadas en verde** (106 del cierre del
  2026-11-16 + 4 de restablecer-contraseña/editar-cliente + 3 de la
  pantalla "Usuarios" + 2 de editar nombre/correo del cliente + 7 de
  BUG-12 + 17 de editar/eliminar rutinas y dietas, las últimas cinco
  actualizaciones del 2026-11-18) -- 0 commits revertidos.
- **76 casos de prueba cubiertos en total** (CP01-18 del plan original +
  CP19-46 de la ampliación de RF004/RF005 + CP47-49 del restablecimiento
  de contraseña + CP50-52 de la pantalla "Usuarios" + CP53-59 de BUG-12 +
  CP60-76 de editar/eliminar rutinas y dietas), todos "Pasó".
- **4 bugs nuevos encontrados y corregidos**: BUG-11 durante el cierre del
  2026-11-16, BUG-12/13/14 el 2026-11-18 (ver tabla de bugs arriba); 0
  bugs abiertos en todo el proyecto. Ninguna de las otras actualizaciones
  del 2026-11-18 (restablecer contraseña/editar cliente, editar
  nombre/correo, y la pantalla "Usuarios") encontró ningún bug nuevo.
- **Despliegue verificado end-to-end desde un clon limpio**, sin ningún
  problema encontrado.
