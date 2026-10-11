import './Toast.css'

interface ToastProps {
  message: string
  tone?: 'success' | 'info' | 'danger'
  onDismiss?: () => void
}

/**
 * Feedback tras una acción — patrón canónico fuera del layout de 3 zonas.
 *
 * Generaliza el banner que `ClientsListPage.tsx` ya construye a mano
 * (`.clients-page__toast`, viaja como router state desde `/clientes/nuevo`)
 * en un componente reutilizable, sin tocar esa pantalla (fuera del alcance
 * de esta tarea). Dos canales de feedback conviven a propósito en el
 * sistema, cada uno con un trabajo distinto:
 *
 *   - Dentro de una pantalla de 3 zonas (Dashboard): la columna
 *     "Resultados" (ver AppShell/useResultsPanel) es el canal persistente —
 *     no se descarta, se actualiza con cada acción nueva.
 *   - En un flujo que NAVEGA a otra pantalla al completarse (ej. alta de
 *     cliente -> vuelve a /clientes): este `Toast`, descartable, viajando
 *     como router state. Es un evento puntual, no un resumen vivo.
 *
 * Ver docs/REVISION-UX.md para el detalle de esta decisión.
 */
export function Toast({ message, tone = 'success', onDismiss }: ToastProps) {
  return (
    <div className="toast" data-tone={tone} role="status">
      <span>{message}</span>
      {onDismiss && (
        <button type="button" className="toast__dismiss" onClick={onDismiss} aria-label="Cerrar aviso">
          ×
        </button>
      )}
    </div>
  )
}
