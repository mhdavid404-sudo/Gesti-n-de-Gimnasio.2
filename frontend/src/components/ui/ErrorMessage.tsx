import './ErrorMessage.css'

interface ErrorMessageProps {
  title?: string
  /** Mensaje en español, orientado al usuario final (nunca el texto crudo de una excepción). */
  message: string
  onRetry?: () => void
}

/**
 * Mensaje de error de pantalla completa/sección (llamada a datos fallida,
 * ruta no encontrada, etc.) — generaliza el patrón de error ya usado por
 * campo en ClientFormPage (`.field-error`, `data-invalid`, `role="alert"`;
 * ver ClientFormPage.tsx/.css, que sigue siendo la referencia canónica para
 * VALIDACIÓN EN LÍNEA de un campo individual). Este componente es para el
 * otro caso: un error de nivel de pantalla/sección completa, no de un solo
 * input.
 */
export function ErrorMessage({ title = 'Algo salió mal', message, onRetry }: ErrorMessageProps) {
  return (
    <div className="error-message" role="alert">
      <p className="error-message__title">{title}</p>
      <p className="error-message__text">{message}</p>
      {onRetry && (
        <button type="button" className="btn btn-ghost error-message__retry" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  )
}
