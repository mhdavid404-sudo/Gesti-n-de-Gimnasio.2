# Pendientes que requieren una persona (no se pueden resolver solo con código)

Fecha: 2026-11-16.

## 1. Redactar la sección 3.4 del documento de entrega (máxima prioridad)

**Quién:** Espinosa Medina Luis Layonet (Ingeniero de Requerimientos, Tabla 4
del documento).

La ampliación de RF004/RF005 (catálogo de servicios extra, cambio de plan,
tablero de membresías activas) está completa y probada en el código, pero
el documento `SmartGym-v2-Documentacion-Apartados-I-IV.docx` nunca llegó a
tener una sección 3.4 que la describa formalmente — ver
`docs/AUDITORIA-DOC-VS-CODIGO.md` para el detalle completo del hallazgo.
Esta sesión documentó el comportamiento real en `DECISIONES.md` y
`docs/AUDITORIA-DOC-VS-CODIGO.md`, pero redactar la sección 3.4 en el estilo
y formato del resto del documento (como RF/HU/CU nuevos, siguiendo la Tabla
10 de trazabilidad) es una tarea de documentación académica que le
corresponde a quien lleva esa responsabilidad en el equipo.

## 2. Confirmar con el cliente real: política de reembolso al cambiar de plan

**Quién:** quien tenga la relación con Stronger Aragón (administración del
gimnasio).

Al cambiar el plan de un cliente, si eso cancela un extra ya pagado, el
sistema **no calcula ningún reembolso ni prorrateo** por decisión explícita
del encargo — solo informa cuánto se había pagado y deja un campo de notas
para que el Admin registre el acuerdo comercial a mano. Esto es correcto
mientras no exista una política real; en cuanto el gimnasio defina una
(reembolso completo, saldo a favor para el siguiente pago, sin reembolso),
hay que registrarla en `DECISIONES.md` y programarla.

## 3. Confirmar con el cliente real: qué servicio incluye cada plan

**Quién:** administración de Stronger Aragón.

La asignación actual en `backend/seed.py` (Básica solo incluye casillero;
VIP suma clases grupales y evaluación; Premium los 6 servicios) es dato de
ejemplo para la demo -- ya está marcado así en el `README.md` de la raíz.
Es 100% configurable desde la pantalla "Planes y servicios" sin tocar
código, pero alguien del lado del negocio tiene que decidir la asignación
real antes de usarse en producción.

## 4. Decidir qué hacer con los 4 flujos alternos simplificados (CU05/08/10/11)

**Quién:** quien apruebe el alcance final con la profesora / el cliente.

4 casos de uso (asignar membresía/rutina/dieta/progreso cuando el cliente
ya tiene uno activo) describen en el documento un diálogo interactivo
("¿deseas renovar o reemplazar?", "¿sobrescribir?") que el sistema no
construye — en su lugar, resuelve la intención de fondo (no perder
historial, no terminar en un estado ambiguo) con un diseño distinto
(evolucionar un único registro en vez de preguntar). Ver el detalle de cada
caso en `docs/AUDITORIA-DOC-VS-CODIGO.md`. Si la profesora o el cliente
exigen el diálogo literal, es trabajo de desarrollo adicional (4 pantallas
de confirmación nuevas) fuera del alcance decidido en este cierre.

## 5. Rama `pruebas/delacruz`: pedirle a Benjamín que corrija la carpeta

**Quién:** De La Cruz Ramírez Benjamín.

Su rama agrega los mismos 2 `.docx` que ya están en `main`, pero bajo
`DOCS/` (mayúscula) en vez de `docs/` -- ver `docs/RAMAS-PENDIENTES.md`.
Nadie debe fusionar esa rama tal como está en un checkout de Windows/macOS.

## 6. Actualizar la Tabla 12 y la Tabla 18 del documento (datos desactualizados)

**Quién:** quien mantenga el documento de la entrega.

- Tabla 12 dice que la detección de vencimientos "se dispara manualmente...
  limitación documentada" -- ya no es cierto, se automatizó (job diario,
  ver `DECISIONES.md`).
- Tabla 18 dice "43 rutas, 11 módulos" -- la API real hoy expone 59
  combinaciones ruta+método en 12 módulos (se agregó `services`).

No se editó el `.docx` en esta sesión por la regla explícita de no tocar la
documentación para que cuadre con el código; queda como ajuste editorial
normal (actualizar una cifra que cambió), no como una corrección de fondo.

## 7. Planner / wireframes / anexos pendientes que ya estaban marcados "PENDIENTE" en el documento

No corresponden a este cierre técnico: liga de Microsoft Planner, wireframes
definitivos (con la corrección de "AVIONES"→"PLANES" que el propio
documento ya pide en 3.3 -- ver nota abajo), validación formal con el
usuario, conclusiones, trabajo futuro, bibliografía. Siguen a cargo de cada
responsable según la Tabla 4.

**Nota sobre "AVIONES"/"PERSONAJE"/"DE PRIMERA CALIDAD":** el propio
documento (3.3) ya pide corregir esos rótulos en los *wireframes*, no en el
código -- y una sesión de auditoría anterior (ver `DECISIONES.md`,
entrada "Ajuste de UX: Membresías pasa a tablero de activas", punto 6) ya
confirmó que esas palabras no existen en ningún archivo del código ni en lo
renderizado. El pendiente real es exclusivamente sobre los wireframes
(archivo fuera de este repo), no sobre la aplicación.
