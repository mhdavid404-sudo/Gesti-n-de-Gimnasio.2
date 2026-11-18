import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import type { UserRole } from '../../types/models'
import {
  IconBarbell,
  IconBowl,
  IconCard,
  IconClose,
  IconGrid,
  IconLog,
  IconLogout,
  IconShield,
  IconTag,
  IconTrend,
  IconUsers,
} from './icons'
import './Sidebar.css'

interface NavItem {
  to: string
  label: string
  Icon: typeof IconGrid
  /** Si se omite, el link es visible para los 3 roles. */
  roles?: UserRole[]
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Panel', Icon: IconGrid },
  // "Clientes" es un padrón administrativo (listar/dar de alta clientes) --
  // RF013 limita al rol `cliente` a consultar SU PROPIA información, nunca
  // un listado de clientes (el backend ya responde 403 a `GET /clients`
  // para ese rol, ver routers/clients.py). Membresías/Rutinas/Dietas/
  // Progreso sí se quedan visibles para `cliente`: esas pantallas ya se
  // auto-acotan a "lo propio" cuando las abre un cliente (ver
  // MembershipsPage/RoutinesPage/DietsPage/ProgressPage), son el mismo
  // destino que ya usan sus accesos rápidos "Mi rutina"/"Mi dieta"/etc. del
  // Dashboard.
  { to: '/clientes', label: 'Clientes', Icon: IconUsers, roles: ['admin', 'entrenador'] },
  { to: '/membresias', label: 'Membresías', Icon: IconCard },
  // Administración completa del catálogo (Entrega 3, Fase 2) -- solo
  // admin, mismo criterio que "Clientes"/"Bitácora": entrenador/cliente
  // consultan planes y extras desde la ficha del cliente, no desde aquí.
  { to: '/planes-servicios', label: 'Planes y servicios', Icon: IconTag, roles: ['admin'] },
  { to: '/rutinas', label: 'Rutinas', Icon: IconBarbell },
  { to: '/dietas', label: 'Dietas', Icon: IconBowl },
  { to: '/progreso', label: 'Progreso', Icon: IconTrend },
  // Bitácora (RF015): vista operativa de errores/eventos de TODO el
  // sistema, no "información propia" de ningún rol -- mismo criterio que
  // "Clientes" y el bloque "En números" del Dashboard (ver DECISIONES.md).
  { to: '/bitacora', label: 'Bitácora', Icon: IconLog, roles: ['admin'] },
  // "Usuarios" (2026-11-18): administra cuentas de admin/entrenador
  // (`POST`/`GET`/`PATCH /users`) -- los clientes NO aparecen aquí, se
  // gestionan en "Clientes". Mismo criterio de visibilidad que "Bitácora":
  // solo admin, misma protección (el link desaparece del menú Y el
  // backend ya responde 403 a `GET /users` para `cliente` si entra por URL
  // directa -- `entrenador` sí puede leer `GET /users`, pero esta pantalla
  // igual se le oculta porque dar de alta/activar/desactivar cuentas es
  // acción exclusiva de admin).
  { to: '/usuarios', label: 'Usuarios', Icon: IconShield, roles: ['admin'] },
]

interface SidebarProps {
  /** Solo tiene efecto visual en el breakpoint de drawer (<=900px), ver Sidebar.css. */
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { logout, user } = useAuth()
  const visibleItems = NAV_ITEMS.filter((item) => !item.roles || (user && item.roles.includes(user.role)))

  return (
    <aside className="sidebar" data-open={isOpen}>
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark">SA</div>
        <div className="sidebar__brand-text">
          <strong>Stronger Aragón</strong>
          <span>Control de gimnasio</span>
        </div>
        <button type="button" className="sidebar__close" onClick={onClose} aria-label="Cerrar menú">
          <IconClose />
        </button>
      </div>

      <nav className="sidebar__nav" aria-label="Navegación principal">
        {visibleItems.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          >
            <Icon className="sidebar__icon" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Solo se toca la función de logout (llamar a logout() antes de navegar) --
          estilos/estructura de este link se dejan intactos a propósito, ver nota
          en DECISIONES.md sobre el rediseño de layout en curso en paralelo. */}
      <NavLink to="/login" className="sidebar__logout" onClick={() => logout()}>
        <IconLogout className="sidebar__icon" />
        Cerrar sesión
      </NavLink>
    </aside>
  )
}
