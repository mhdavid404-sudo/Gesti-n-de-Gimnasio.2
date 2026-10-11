# Revisión de arquitectura de interfaz — panel interno (Entrega 2, Parte A)

Revisión del panel interno de SmartGym v2 (Dashboard, Clientes, Detalle de
cliente, Membresías, Rutinas, Dietas, Progreso) contra las 10 heurísticas de
usabilidad de Nielsen, hecha antes de tocar código. El hallazgo principal es
literalmente el feedback recibido sobre el panel: **"No tiene buen UI/UX.
Necesito ver al entrar qué puedo hacer."** — se documenta primero porque es
el que determina el resto del rediseño (layout de 3 zonas, Parte A2/A3).

Cada hallazgo indica la pantalla, el problema concreto y la heurística que
viola, seguido de la mejora aplicada en esta tarea.

---

## Hallazgo principal — Dashboard sin punto de entrada a la acción

- **Pantalla:** `DashboardPage` (como quedó en Entrega 1).
- **Problema:** al entrar, la pantalla mostraba 4 números grandes
  (clientes activos, ingresos, vencimientos) y dos tablas de solo lectura
  (membresías por atender, notificaciones). No había ningún botón, enlace o
  tarjeta que respondiera a "¿qué hago ahora?" — un usuario nuevo (recepción,
  entrenador, cliente) tenía que adivinar que la acción de alta de cliente
  vivía detrás de la sección "Clientes", en la esquina superior de una
  tabla, sin ninguna pista desde el Dashboard.
- **Heurística violada:** **#6, Reconocimiento antes que recuerdo** (el
  usuario tiene que recordar/explorar dónde está cada acción, en vez de que
  el sistema la muestre) y **#7, Flexibilidad y eficiencia de uso** (una
  recepcionista, un entrenador y un cliente veían exactamente la misma
  pantalla, sin accesos directos a las tareas de su propio rol).
- **Mejora aplicada:** layout de 3 zonas (ver A2 abajo). La zona CENTRO del
  Dashboard ahora es una respuesta directa a la pregunta: tarjetas grandes
  con verbo en el título ("Registrar cliente", "Asignar rutina", "Ver mi
  progreso"), filtradas por rol. Los números pasan a un bloque secundario,
  más chico, debajo — siguen existiendo pero ya no son lo primero que se lee.

---

## Hallazgos por heurística

### 1 — Visibilidad del estado del sistema

- **Pantalla:** todo el panel fuera de `ClientFormPage` → `ClientsListPage`.
- **Problema:** el único flujo con feedback de "tu acción funcionó" era
  alta de cliente (toast al volver al listado). Asignar una rutina/dieta
  (`RoutinesPage`, `DietsPage`) solo actualiza una tabla en silencio, sin
  ninguna confirmación visible de que la asignación se guardó.
- **Mejora aplicada:** se define un patrón canónico de feedback con dos
  canales explícitos (ver `components/ui/Toast.tsx`, comentario de cabecera,
  y la sección "Feedback tras acción" más abajo): la columna "Resultados"
  para pantallas de 3 zonas, y el `Toast` reutilizable para flujos que
  navegan a otra pantalla. Los módulos que todavía no lo usan (Rutinas,
  Dietas) quedan fuera del alcance de esta tarea, pero el componente ya
  existe listo para conectarse.

### 2 — Coincidencia entre el sistema y el mundo real

- Sin hallazgos nuevos relevantes: la terminología (Básica/VIP/Premium,
  "por vencer", "pago registrado") ya usa vocabulario del negocio, no jerga
  técnica. No se tocó nada aquí.

### 3 — Control y libertad del usuario

- **Pantalla:** `ClientDetailPage`.
- **Problema:** no hay ninguna miga de pan ni botón "volver" visible en el
  caso normal (solo aparece un `btn btn-ghost` "Volver a clientes" dentro
  del estado de error, cuando el cliente no existe). Si alguien llega aquí
  desde un link de `MembershipsPage` o del Dashboard, no hay un camino de
  regreso consistente más que el botón "Atrás" del navegador.
- **Mejora aplicada:** componente `Breadcrumbs` (ver
  `components/ui/Breadcrumbs.tsx`) listo para usarse en Detalle de Cliente.
  No se conecta en esta tarea porque editar `ClientDetailPage.tsx` está
  fuera del alcance delegado (ver encargo); queda documentado como el punto
  de integración exacto para el siguiente trabajo que la toque.

### 4 — Consistencia y estándares

- **Pantalla:** sidebar (`Sidebar.tsx`) y resto del panel.
- **Problema:** el estado "sección activa" del sidebar se distinguía solo
  por un borde blanco de 2px y un fondo casi imperceptible — fácil de pasar
  por alto a primera vista, inconsistente con que el resto del sistema
  (botones, foco de teclado) sí usa color con fuerza para señalar estado.
- **Mejora aplicada:** el verde oliva, ahora color PRIMARIO del sistema (no
  solo un acento en botones, ver A1 abajo), se usa directamente en el ícono,
  el texto y el borde izquierdo del link activo del sidebar — la sección
  activa ya no depende de un detalle sutil de 2px para notarse.

### 5 — Prevención de errores

- **Pantalla:** todo el panel.
- **Problema:** ninguna pantalla pide confirmación antes de una acción
  destructiva — hoy no existe ningún botón de eliminar todavía, pero
  tampoco existía el componente para cuando lo haya, lo que invita a que la
  primera vez que alguien construya un "Eliminar cliente" lo haga sin
  confirmación por simple ausencia de un patrón ya resuelto.
- **Mejora aplicada:** `components/ui/ConfirmDialog.tsx` — diálogo modal
  reutilizable (confirmar/cancelar, tono danger por defecto, cierre con
  Escape, foco inicial en el botón de confirmar). Ninguna pantalla borra
  nada todavía, así que no se conecta a un botón real en esta tarea.

### 6 — Reconocimiento antes que recuerdo

- Ver "Hallazgo principal" arriba — es el caso más grave de esta heurística
  en todo el sistema, y el que resuelve el layout de 3 zonas.

### 7 — Flexibilidad y eficiencia de uso

- Ver "Hallazgo principal" arriba (falta de accesos por rol). Mejora
  aplicada: acciones rápidas filtradas por rol en el Dashboard (ver A3), más
  un selector de rol mock (`RoleSwitcher.tsx`, claramente marcado como
  herramienta de desarrollo) para poder probar las 3 variantes mientras el
  proceso de autenticación real no está conectado todavía.

### 8 — Diseño estético y minimalista

- **Pantalla:** `DashboardPage`.
- **Problema:** la pantalla mezclaba "membresías que requieren atención" y
  "notificaciones recientes" en el mismo nivel de jerarquía que la acción
  principal del día — sin una jerarquía clara de qué es la tarea primaria y
  qué es información de apoyo.
- **Mejora aplicada:** separación explícita de zonas (centro = tareas,
  derecha = información de apoyo/resultados) en vez de un solo grid donde
  todo compite por atención al mismo nivel.

### 9 — Ayudar a reconocer, diagnosticar y recuperarse de errores

- **Pantalla:** `ClientFormPage` (ya tenía el patrón correcto) vs. el resto
  del panel (no tenía equivalente para errores de pantalla completa, por
  ejemplo una carga de datos fallida).
- **Mejora aplicada:** `components/ui/ErrorMessage.tsx` generaliza el
  mensaje de error en español para el caso de pantalla/sección completa,
  dejando el patrón de `ClientFormPage` (`.field-error`, `data-invalid`,
  `role="alert"`) como la referencia canónica para validación de UN campo
  — ver sección "Patrones documentados" más abajo.

### 10 — Ayuda y documentación

- **Pantalla:** todo el panel.
- **Problema:** ninguna pantalla tiene un estado vacío construido a
  propósito — cuando una tabla no tiene filas, cada pantalla escribía su
  propio `<p>` suelto (`.dashboard__empty`, `.client-detail__empty`, etc.),
  sin acción sugerida ni lenguaje visual compartido.
- **Mejora aplicada:** `components/ui/EmptyState.tsx` (mensaje + acción
  opcional), ya usado de forma real dentro de la columna "Resultados" del
  Dashboard (alertas de membresía vacías, progreso sin registros, etc.).

---

## Patrones documentados (referencia canónica)

Para que el siguiente trabajo sobre el panel no reinvente estos patrones:

- **Validación en línea de un campo:** `ClientFormPage.tsx` / `.css` —
  atributo `data-invalid`, clase `.field-error`, `role="alert"`, limpieza
  del error individual al corregir el campo. No se tocó, sigue siendo la
  referencia.
- **Feedback tras una acción — dos canales, cada uno con un trabajo
  distinto:**
  - Dentro de una pantalla de 3 zonas (Dashboard): la columna
    "Resultados" (`AppShellContext` / `useResultsPanel`) es el canal
    persistente — se actualiza con cada acción, no se descarta.
  - En un flujo que navega a otra pantalla al completarse (ej. alta de
    cliente → vuelve a `/clientes`): el componente `Toast` (descartable,
    viaja como router state), que generaliza el banner que
    `ClientsListPage.tsx` ya construía a mano.
- **Estado vacío:** `components/ui/EmptyState.tsx`.
- **Estado de carga:** `components/ui/LoadingState.tsx` (spinner puntual o
  skeleton para listas/tablas).
- **Confirmación antes de eliminar:** `components/ui/ConfirmDialog.tsx`.
- **Migas de pan:** `components/ui/Breadcrumbs.tsx` (pensado especialmente
  para `ClientDetailPage`, ver heurística #3 arriba).
- **Foco de teclado:** `:focus-visible` global en `theme.css`, sin cambios
  de comportamiento — se verificó que sigue funcionando con la paleta nueva
  (el outline usa `--color-primary`, con contraste AA verificado, ver
  `theme.css`).

---

## A2 — Por qué drawers en vez de reflow horizontal en móvil

El sidebar de Entrega 1 no colapsaba en móvil: a 900px de ancho se
reacomodaba a una barra horizontal con los mismos enlaces en fila, sin
ocultar nada. Eso funciona en pantallas medianas (tablet) pero en un
teléfono angosto termina envolviendo en 2-3 líneas y empujando el
contenido hacia abajo — el usuario pierde la primera pantalla completa en
navegación antes de ver cualquier contenido real (heurística #8).

Se sustituyó por un drawer real (oculto por defecto en `<=900px`, con botón
de apertura/cierre y un scrim) tanto para el sidebar como para la nueva
columna "Resultados" (`<=1100px`) — el contenido central siempre tiene
prioridad en pantallas angostas, y la navegación/los resultados quedan "a
una acción de distancia" en vez de competir por espacio permanentemente.
