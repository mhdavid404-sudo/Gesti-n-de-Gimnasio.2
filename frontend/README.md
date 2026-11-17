# SmartGym v2 — Frontend

Panel de administración y landing pública de **Stronger Aragón**, construido
con React + Vite + TypeScript. Conectado por completo a la API real (sin
datos mock) — ver el `README.md` de la raíz del repo para el stack completo,
cómo levantar todo el proyecto con Docker y las cuentas de demostración por
rol.

## Cómo correrlo (solo este servicio, fuera de Docker)

```bash
cd frontend
npm install
npm run dev
```

El servidor de desarrollo corre en **http://localhost:5173** (puerto fijo en
`vite.config.ts`). Requiere que el backend esté corriendo (ver `README.md`
de la raíz) y la variable `VITE_API_URL` apuntando a él (por defecto
`http://localhost:8000`, ver `.env.example`).

## Pantallas

| Ruta | Pantalla | Acceso |
|---|---|---|
| `/` | Landing pública | Público |
| `/login` | Inicio de sesión | Público |
| `/dashboard` | Panel general (resumen operativo) | Todos los roles |
| `/clientes`, `/clientes/nuevo`, `/clientes/:id` | Padrón de clientes y ficha (membresía, extras, pagos, rutina, dieta, progreso) | Admin / Entrenador |
| `/membresias` | Tablero de membresías activas (Admin/Entrenador) o "Mi membresía" (Cliente) | Todos los roles |
| `/planes-servicios` | Catálogo de planes y servicios extra | Admin |
| `/rutinas` | Catálogo y asignación de rutinas | Todos los roles |
| `/dietas` | Planes de dieta y asignación | Todos los roles |
| `/progreso` | Progreso corporal y gráfica de evolución | Todos los roles |
| `/bitacora` | Bitácora de errores/eventos del sistema | Admin |

## Identidad visual

Paleta definida en `src/styles/theme.css` (tokens con contraste AA
documentado en el propio archivo):

| Token | Hex | Uso |
|---|---|---|
| `--color-bg` | `#0B0C09` | fondo general |
| `--color-surface` | `#181A13` | tarjetas |
| `--color-text` | `#F2F3EC` | texto principal |
| `--color-primary` | `#97A947` | verde oliva — acento/acción principal |
| `--color-success` | `#3FB6A0` | estado al día |
| `--color-warning` | `#E08D3C` | por vencer |
| `--color-danger` | `#D65A4A` | vencido/error |

Tipografía condensada (`Bebas Neue`) para títulos y números protagonistas,
`Helvetica Neue` para el resto de la interfaz. Accesibilidad básica:
`:focus-visible` visible en toda la UI, `prefers-reduced-motion` respetado,
layout responsive (el menú lateral colapsa a drawer en móvil).

## Verificación

`npm install`, `npx tsc -b` (modo estricto, `noUnusedLocals`/
`noUnusedParameters` incluidos) y `npm run build` corren sin errores.
