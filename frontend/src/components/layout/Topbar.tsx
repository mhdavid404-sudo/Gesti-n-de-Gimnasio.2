import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ApiError, apiFetch } from '../../api/client'
import { useAuth } from '../../hooks/useAuth'
import type { ApiNotification } from '../../types/api'
import type { UserRole } from '../../types/models'
import { IconBell, IconMenu, IconResults } from './icons'
import './Topbar.css'

interface TopbarProps {
  title: string
  subtitle?: string
  onToggleSidebar: () => void
  hasResults: boolean
  onToggleResults: () => void
}

/**
 * Etiqueta de rol en español mostrada junto al nombre real del usuario.
 * `User`/`AuthUser` no tiene campo de género -- "Administración" se eligió
 * deliberadamente neutro para `admin` en vez de "Administrador"/
 * "Administradora" para no asumir género sin dato real que lo respalde;
 * `entrenador`/`cliente` son los propios nombres de rol del dominio, sin
 * ambigüedad de género adicional que resolver.
 */
const ROLE_LABEL: Record<UserRole, string> = {
  admin: 'Administración',
  entrenador: 'Entrenador',
  cliente: 'Cliente',
}

/** Mismo criterio de iniciales que `ClientDetailPage.tsx` (avatar de cliente): primera letra de las primeras 2 palabras del nombre completo. */
function getInitials(fullName: string): string {
  const initials = fullName
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] ?? '')
    .join('')
  return initials ? initials.toUpperCase() : '?'
}

export function Topbar({ title, subtitle, onToggleSidebar, hasResults, onToggleResults }: TopbarProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const [notifications, setNotifications] = useState<ApiNotification[]>([])
  const [panelOpen, setPanelOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!user) return
    apiFetch<ApiNotification[]>(`/notifications/users/${user.id}`)
      .then(setNotifications)
      .catch((err: unknown) => {
        // La campana es un indicador secundario -- un fallo al cargarla no
        // debe tumbar el resto del Topbar/la pantalla. Un 401 sí se honra
        // (sesión vencida) igual que el resto de la app.
        if (err instanceof ApiError && err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
        }
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id])

  useEffect(() => {
    if (!panelOpen) return
    const handleClickOutside = (event: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setPanelOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [panelOpen])

  const unread = notifications.filter((n) => !n.is_read).length

  const handleMarkAsRead = (notification: ApiNotification) => {
    if (notification.is_read) return
    setNotifications((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: true } : n)))
    apiFetch<ApiNotification>(`/notifications/${notification.id}/read`, { method: 'POST' }).catch(
      (err: unknown) => {
        // Si falla, se revierte el marcado optimista.
        setNotifications((prev) => prev.map((n) => (n.id === notification.id ? { ...n, is_read: false } : n)))
        if (err instanceof ApiError && err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
        }
      },
    )
  }

  const displayName = user?.full_name ?? 'Usuario'
  const roleLabel = user ? ROLE_LABEL[user.role] : ''

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

        <div className="topbar__bell-wrap" ref={panelRef}>
          <button
            type="button"
            className="topbar__bell"
            aria-label={`${unread} notificaciones sin leer`}
            aria-expanded={panelOpen}
            onClick={() => setPanelOpen((v) => !v)}
          >
            <IconBell />
            {unread > 0 ? <span className="topbar__bell-badge">{unread}</span> : null}
          </button>

          {panelOpen && (
            <div className="topbar__notif-panel" role="menu">
              <div className="topbar__notif-header">
                <strong>Notificaciones</strong>
                <button
                  type="button"
                  className="topbar__notif-viewall"
                  onClick={() => {
                    setPanelOpen(false)
                    navigate('/dashboard')
                  }}
                >
                  Ver en el panel
                </button>
              </div>
              {notifications.length === 0 ? (
                <p className="topbar__notif-empty">Sin notificaciones.</p>
              ) : (
                <ul className="topbar__notif-list">
                  {notifications.slice(0, 8).map((n) => (
                    <li key={n.id}>
                      <button
                        type="button"
                        className="topbar__notif-item"
                        data-unread={!n.is_read}
                        onClick={() => handleMarkAsRead(n)}
                      >
                        <span className="topbar__notif-dot" aria-hidden="true" />
                        <span className="topbar__notif-text">
                          <strong>{n.title}</strong>
                          <span>{n.message}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div className="topbar__user">
          <div className="topbar__avatar">{getInitials(displayName)}</div>
          <div className="topbar__user-text">
            <strong>{displayName}</strong>
            <span>{roleLabel}</span>
          </div>
        </div>
      </div>
    </header>
  )
}
