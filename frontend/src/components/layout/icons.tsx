/**
 * Iconos de línea dibujados a mano para la navegación — deliberadamente NO
 * un icon-pack genérico ni emojis. Trazo uniforme (1.6), 18x18.
 */
type IconProps = { className?: string }

const base = {
  width: 18,
  height: 18,
  viewBox: '0 0 18 18',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.6,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export const IconGrid = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="2.2" y="2.2" width="5.6" height="5.6" rx="1" />
    <rect x="10.2" y="2.2" width="5.6" height="5.6" rx="1" />
    <rect x="2.2" y="10.2" width="5.6" height="5.6" rx="1" />
    <rect x="10.2" y="10.2" width="5.6" height="5.6" rx="1" />
  </svg>
)

export const IconUsers = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <circle cx="6.5" cy="6" r="2.3" />
    <path d="M2.2 15c0-2.4 1.9-4 4.3-4s4.3 1.6 4.3 4" />
    <circle cx="13" cy="6.8" r="1.8" />
    <path d="M11.7 11.3c1.8.2 3.2 1.6 3.2 3.7" />
  </svg>
)

export const IconCard = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <rect x="2" y="4" width="14" height="10" rx="1.4" />
    <line x1="2" y1="7.2" x2="16" y2="7.2" />
    <line x1="4.2" y1="11" x2="8.2" y2="11" />
  </svg>
)

export const IconBarbell = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <line x1="2" y1="9" x2="16" y2="9" />
    <rect x="3.2" y="6" width="1.8" height="6" rx="0.5" />
    <rect x="13" y="6" width="1.8" height="6" rx="0.5" />
    <rect x="1" y="7.2" width="1.4" height="3.6" rx="0.4" />
    <rect x="15.6" y="7.2" width="1.4" height="3.6" rx="0.4" />
  </svg>
)

export const IconBowl = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M2.4 8.4h13.2c0 3.4-3 5.8-6.6 5.8s-6.6-2.4-6.6-5.8Z" />
    <path d="M6 8.4c0-1.9 1.3-3.4 3-3.4" />
  </svg>
)

export const IconTrend = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M2.2 13 6.6 8.2l3 2.8 5.2-6" />
    <path d="M11.6 5h3.2v3.2" />
  </svg>
)

export const IconBell = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M4.4 12.2V8a4.6 4.6 0 0 1 9.2 0v4.2l1.2 1.6H3.2Z" />
    <path d="M7.4 14.6a1.6 1.6 0 0 0 3.2 0" />
  </svg>
)

export const IconLogout = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M7.4 2.6H4A1.6 1.6 0 0 0 2.4 4.2v9.6A1.6 1.6 0 0 0 4 15.4h3.4" />
    <path d="M11.4 12.2 15.4 9l-4-3.2" />
    <line x1="15.4" y1="9" x2="6.6" y2="9" />
  </svg>
)

/** Abre el menú/drawer lateral en pantallas angostas (ver AppShell/Sidebar). */
export const IconMenu = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <line x1="2.2" y1="4.8" x2="15.8" y2="4.8" />
    <line x1="2.2" y1="9" x2="15.8" y2="9" />
    <line x1="2.2" y1="13.2" x2="15.8" y2="13.2" />
  </svg>
)

/** Cierra un drawer/diálogo (sidebar móvil, zona de Resultados, ConfirmDialog). */
export const IconClose = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <line x1="3.6" y1="3.6" x2="14.4" y2="14.4" />
    <line x1="14.4" y1="3.6" x2="3.6" y2="14.4" />
  </svg>
)

/** Alerta/resultados — campanita llena para distinguir del estado "vacío". */
export const IconResults = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M2.4 13.4 9 2.6l6.6 10.8Z" />
    <line x1="9" y1="6.8" x2="9" y2="10.2" />
    <circle cx="9" cy="12.4" r="0.9" fill="currentColor" stroke="none" />
  </svg>
)

/** Planes y servicios extra — etiqueta de precio, distinta de IconCard (membresías = tarjeta, no etiqueta). */
export const IconTag = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M2.6 9.4 9.4 2.6h5.2a1.2 1.2 0 0 1 1.2 1.2v5.2L8.6 15.8a1.2 1.2 0 0 1-1.7 0L2.6 11.1a1.2 1.2 0 0 1 0-1.7Z" />
    <circle cx="12.2" cy="5.8" r="1.1" fill="currentColor" stroke="none" />
  </svg>
)

/** Bitácora — hoja de registro con renglones, para distinguir de IconCard (sin reglón inferior). */
export const IconLog = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M4.4 2.6h9.2v12.8H4.4z" />
    <line x1="6.6" y1="6" x2="11.4" y2="6" />
    <line x1="6.6" y1="9" x2="11.4" y2="9" />
    <line x1="6.6" y1="12" x2="9.6" y2="12" />
  </svg>
)

/** Usuarios (admin/entrenador, pantalla "Usuarios") — escudo con palomita, para distinguir de IconUsers (clientes). */
export const IconShield = ({ className }: IconProps) => (
  <svg {...base} className={className}>
    <path d="M9 2.4 14.6 4.4V9c0 3.6-3 6.2-5.6 7.2C6.4 15.2 3.4 12.6 3.4 9V4.4Z" />
    <path d="M6.6 9 8.2 10.6 11.4 7.2" />
  </svg>
)
