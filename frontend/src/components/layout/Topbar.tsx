import { getNotificationsForUser } from '../../mocks/data'
import { IconBell, IconMenu, IconResults } from './icons'
import './Topbar.css'

interface TopbarProps {
  title: string
  subtitle?: string
  onToggleSidebar: () => void
  hasResults: boolean
  onToggleResults: () => void
}

export function Topbar({ title, subtitle, onToggleSidebar, hasResults, onToggleResults }: TopbarProps) {
  const unread = getNotificationsForUser(1).filter((n) => !n.is_read).length

  return (
    <header className="topbar">
      <div className="topbar__left">
        <button
          type="button"
          className="topbar__menu-btn"
          onClick={onToggleSidebar}
          aria-label="Abrir menú de navegación"
        >
          <IconMenu />
        </button>
        <div>
          <h1 className="topbar__title">{title}</h1>
          {subtitle ? <p className="topbar__subtitle">{subtitle}</p> : null}
        </div>
      </div>

      <div className="topbar__actions">
        {hasResults && (
          <button
            type="button"
            className="topbar__results-btn"
            onClick={onToggleResults}
            aria-label="Ver resultados"
          >
            <IconResults />
            Resultados
          </button>
        )}
        <button type="button" className="topbar__bell" aria-label={`${unread} notificaciones sin leer`}>
          <IconBell />
          {unread > 0 ? <span className="topbar__bell-badge">{unread}</span> : null}
        </button>
        <div className="topbar__user">
          <div className="topbar__avatar">MA</div>
          <div className="topbar__user-text">
            <strong>Marisol Aragón</strong>
            <span>Administradora</span>
          </div>
        </div>
      </div>
    </header>
  )
}
