import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import './EmptyState.css'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
  /** Usa uno u otro, no ambos: navega a otra pantalla (Link) o dispara una acción local (button). */
  actionLabel?: string
  actionHref?: string
  onAction?: () => void
  /** Variante chica para usarse dentro de paneles angostos (ej. columna "Resultados"). */
  compact?: boolean
}

/**
 * Estado vacío reutilizable — mensaje + acción opcional. Reemplaza los
 * `<p>` sueltos tipo "No hay membresías vencidas…" que cada pantalla
 * escribía por su cuenta (ver DashboardPage.css histórico, `.dashboard__empty`)
 * por un componente con el mismo lenguaje visual en todo el sistema.
 */
export function EmptyState({
  title,
  description,
  icon,
  actionLabel,
  actionHref,
  onAction,
  compact = false,
}: EmptyStateProps) {
  return (
    <div className="empty-state" data-compact={compact}>
      {icon ? <span className="empty-state__icon">{icon}</span> : null}
      <p className="empty-state__title">{title}</p>
      {description ? <p className="empty-state__description">{description}</p> : null}
      {actionLabel && actionHref ? (
        <Link to={actionHref} className="btn btn-primary empty-state__action">
          {actionLabel}
        </Link>
      ) : actionLabel && onAction ? (
        <button type="button" className="btn btn-primary empty-state__action" onClick={onAction}>
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}
