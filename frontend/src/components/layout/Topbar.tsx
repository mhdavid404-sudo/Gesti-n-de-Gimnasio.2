import { getNotificationsForUser } from '../../mocks/data'
import { IconBell } from './icons'
import './Topbar.css'

interface TopbarProps {
  title: string
  subtitle?: string
}

export function Topbar({ title, subtitle }: TopbarProps) {
  const unread = getNotificationsForUser(1).filter((n) => !n.is_read).length

  return (
    <header className="topbar">
      <div>
        <h1 className="topbar__title">{title}</h1>
        {subtitle ? <p className="topbar__subtitle">{subtitle}</p> : null}
      </div>

      <div className="topbar__actions">
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
