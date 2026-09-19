import { NavLink } from 'react-router-dom'
import { IconBarbell, IconBowl, IconCard, IconGrid, IconLogout, IconTrend, IconUsers } from './icons'
import './Sidebar.css'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Panel', Icon: IconGrid },
  { to: '/clientes', label: 'Clientes', Icon: IconUsers },
  { to: '/membresias', label: 'Membresías', Icon: IconCard },
  { to: '/rutinas', label: 'Rutinas', Icon: IconBarbell },
  { to: '/dietas', label: 'Dietas', Icon: IconBowl },
  { to: '/progreso', label: 'Progreso', Icon: IconTrend },
]

export function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__brand-mark">SA</div>
        <div className="sidebar__brand-text">
          <strong>Stronger Aragón</strong>
          <span>Control de gimnasio</span>
        </div>
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

      <NavLink to="/login" className="sidebar__logout">
        <IconLogout className="sidebar__icon" />
        Cerrar sesión
      </NavLink>
    </aside>
  )
}
