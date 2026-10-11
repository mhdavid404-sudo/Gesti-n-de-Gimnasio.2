import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { IconBarbell, IconBowl, IconCard, IconClose, IconGrid, IconLogout, IconTrend, IconUsers } from './icons'
import './Sidebar.css'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Panel', Icon: IconGrid },
  { to: '/clientes', label: 'Clientes', Icon: IconUsers },
  { to: '/membresias', label: 'Membresías', Icon: IconCard },
  { to: '/rutinas', label: 'Rutinas', Icon: IconBarbell },
  { to: '/dietas', label: 'Dietas', Icon: IconBowl },
  { to: '/progreso', label: 'Progreso', Icon: IconTrend },
]

interface SidebarProps {
  /** Solo tiene efecto visual en el breakpoint de drawer (<=900px), ver Sidebar.css. */
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { logout } = useAuth()

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
        {NAV_ITEMS.map(({ to, label, Icon }) => (
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
