# SmartGym v2 — Frontend (Entrega 1)

Prototipo de frontend "decente pero no completo" para **Stronger Aragón**,
construido por Leo (agente de frontend) según el alcance fijado en
`SMARTGYM-V2-BRIEF.md` y las convenciones de `COORDINACION-ENTREGA1.md`
(raíz del repo).

## Cómo correrlo

```bash
cd frontend
npm install
npm run dev
```

El servidor de desarrollo corre en **http://localhost:5173** (puerto fijo en
`vite.config.ts`, tal como exige la convención compartida con Royer/DevOps).

Instalación y build ya se verificaron en este entorno: `npm install`,
`npx tsc -b` y `npm run build` corren sin errores. No falta ejecutar nada
adicional.

## Alcance de esta entrega

- 8 pantallas con **datos mock/estáticos únicamente** — cero llamadas a un
  backend real (todavía no existe uno funcional que consumir).
- Navegación real entre pantallas con `react-router-dom`.
- Login **solo de UI**: el formulario no valida nada, cualquier submit
  navega directo a `/dashboard`.
- TypeScript en modo estricto (`strict: true` explícito en
  `tsconfig.app.json`, además de `noUncheckedIndexedAccess` y
  `noImplicitReturns`).

## Pantallas construidas

| Ruta | Pantalla |
|---|---|
| `/` | Login (solo UI) |
| `/dashboard` | Panel general (KPIs + atención + notificaciones) |
| `/clientes` | Lista de clientes con búsqueda |
| `/clientes/:id` | Detalle de cliente — tabs: perfil / membresía / pagos / rutina / dieta / progreso |
| `/membresias` | Planes (Básica/VIP/Premium) + membresías activas |
| `/rutinas` | Catálogo de ejercicios/rutinas + asignación a clientes |
| `/dietas` | Planes de dieta + asignación a clientes |
| `/progreso` | Progreso corporal con gráfica de evolución (SVG propio) |

## Concepto de diseño

Stronger Aragón hoy administra clientes, membresías y pagos en hojas de
Excel repartidas entre dos turnos (mañana / tarde-noche), sin cruce de
información. El concepto visual **no es una "app de fitness genérica azul
con ícono de pesa"**: es un tablero de control con la crudeza de un
gimnasio real — grafito, hierro y el cobre de los discos de las barras —
donde los números que antes vivían perdidos en columnas de Excel ahora se
leen de un vistazo, como en el marcador de una sala de pesas.

**Paleta** (definida en `src/styles/theme.css`):

| Token | Hex | Uso |
|---|---|---|
| `--color-bg` | `#14151A` | fondo general (grafito casi negro) |
| `--color-surface` | `#1D1F26` | tarjetas |
| `--color-border-soft` | `#2A2D36` | bordes sutiles (sin sombras genéricas de tarjeta) |
| `--color-text` | `#F3F0E8` | texto principal (blanco tiza) |
| `--color-text-muted` | `#9A9DAA` | texto secundario (gris acero) |
| `--color-accent` | `#D98E3E` | cobre — color protagonista |
| `--color-success` | `#6FB98F` | membresía al día |
| `--color-warning` | `#E3B341` | membresía por vencer |
| `--color-danger` | `#DD5B4F` | membresía vencida |

**Tipografía:** *Bebas Neue* (condensada, de marcador de gimnasio) reservada
solo para números protagonistas y títulos de sección — nunca para párrafos
— combinada con *Inter* para todo el texto de lectura y la UI.

**Protagonista visual:** los números grandes en Bebas Neue (componente
`StatNumber`) — clientes activos, ingresos del mes, peso/estatura en
progreso corporal, precios de planes. Es la idea central del concepto:
convertir cifras que hoy están perdidas en una hoja de cálculo en algo que
se lee de un vistazo. Todo lo demás (tablas, formularios, tabs) se mantiene
disciplinado en Inter y tamaños moderados para no competir con ese
elemento.

**Iconografía:** trazos de línea dibujados a mano en `components/layout/icons.tsx`
(grid, personas, tarjeta, barra, plato, tendencia) — no un icon-pack
genérico ni emojis.

**Movimiento:** deliberadamente mínimo — transición de color/borde en hover
de 0.12s, sin "fade-in" por default en ninguna sección.

**Accesibilidad:** `:focus-visible` con contorno cobre en toda la UI,
layout responsive con breakpoints hasta mobile (sidebar colapsa a barra
horizontal), contraste de texto sobre fondo oscuro verificado a simple
vista (texto principal `#F3F0E8` sobre `#14151A`/`#1D1F26`).

## Modelo de datos (alineación con `DECISIONES.md`)

Los tipos en `src/types/models.ts` reflejan 1:1 las 13/14 entidades
aprobadas por Isai en `DECISIONES.md` (raíz del repo): mismos nombres de
entidad, mismos campos, mismos valores de `role`/`status`/`method`/`type`
modelados como *string literal unions* (equivalente TS de VARCHAR + CHECK,
no ENUM nativo — tal como exige la corrección de Isai). Puntos verificados
explícitamente:

- `User.password_hash` existe aunque el login no sea funcional.
- `ClientProfile.trainer_id` es `number | null` (FK 1:n simple, sin tabla
  puente).
- `BodyProgress.height_cm` vive en `BodyProgress`, **no** en
  `ClientProfile` (punto menor confirmado en `DECISIONES.md`).
- `RoutineExercise` existe como tabla puente entre `Routine` y `Exercise`
  con `sets`/`reps`/`rest_seconds`/`order`.
- Las 14 entidades nombradas en `DECISIONES.md` (`User`, `ClientProfile`,
  `MembershipPlan`, `Membership`, `Payment`, `Exercise`, `Routine`,
  `RoutineExercise`, `RoutineAssignment`, `DietPlan`, `DietAssignment`,
  `BodyProgress`, `Notification`, `AuditLog`) tienen su interfaz
  correspondiente.

Los datos de ejemplo en `src/mocks/data.ts` usan estos tipos directamente
(sin `any`), enlazados por ID de forma consistente (un cliente, su
membresía, sus pagos, su rutina, su dieta y su progreso cuentan la misma
historia). En Entrega 2 este archivo se reemplaza por llamadas a la API
real; las pantallas no deberían necesitar reescritura, solo el swap de
origen de datos.
