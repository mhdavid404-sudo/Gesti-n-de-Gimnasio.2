import './LoadingState.css'

interface LoadingStateProps {
  label?: string
  /** 'spinner': estado de carga corto/puntual. 'skeleton': reserva el espacio de una tabla/lista mientras llega la respuesta real. */
  variant?: 'spinner' | 'skeleton'
  rows?: number
}

/**
 * Estado de carga reutilizable — listo para conectarse cuando las pantallas
 * pasen a pedir datos reales a la API (esta tarea sigue usando mocks
 * síncronos, así que hoy no hay un consumidor real todavía, ver
 * docs/REVISION-UX.md).
 */
export function LoadingState({ label = 'Cargando…', variant = 'spinner', rows = 3 }: LoadingStateProps) {
  if (variant === 'skeleton') {
    return (
      <div className="loading-state loading-state--skeleton" role="status" aria-label={label}>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="loading-state__skeleton-row" />
        ))}
      </div>
    )
  }

  return (
    <div className="loading-state" role="status" aria-label={label}>
      <span className="loading-state__spinner" aria-hidden="true" />
      <span className="loading-state__label">{label}</span>
    </div>
  )
}
