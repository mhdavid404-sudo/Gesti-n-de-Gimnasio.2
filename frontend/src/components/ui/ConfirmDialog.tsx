import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import './ConfirmDialog.css'

interface ConfirmDialogProps {
  open: boolean
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  /** 'danger' para acciones destructivas (eliminar) — tono por defecto. */
  tone?: 'danger' | 'neutral'
  onConfirm: () => void
  onCancel: () => void
}

/**
 * Confirmación antes de eliminar — no existía ningún componente para esto
 * en el sistema (ver docs/REVISION-UX.md, heurística "Prevención de
 * errores"). Listo para conectarse a cualquier acción destructiva futura
 * (borrar cliente, cancelar membresía, etc.); ninguna pantalla del panel
 * borra nada todavía, así que no se conecta a un botón real en esta tarea.
 *
 * Se monta vía `createPortal` en `document.body` para no quedar recortado
 * por el `overflow` de la columna "Resultados" o de tablas con scroll
 * horizontal. Usa una sombra suave de elevación (no la sombra "poster" de
 * las stat cards, ver theme.css) porque un diálogo flota sobre toda la
 * interfaz — es un objeto distinto de una tarjeta de resumen físico.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Eliminar',
  cancelLabel = 'Cancelar',
  tone = 'danger',
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!open) return
    confirmRef.current?.focus()

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, onCancel])

  if (!open) return null

  return createPortal(
    <div className="confirm-dialog">
      <button type="button" className="confirm-dialog__scrim" aria-label="Cancelar" onClick={onCancel} />
      <div className="confirm-dialog__panel" role="alertdialog" aria-modal="true" aria-labelledby="confirm-dialog-title">
        <h2 id="confirm-dialog-title" className="confirm-dialog__title">
          {title}
        </h2>
        {description && <p className="confirm-dialog__description">{description}</p>}
        <div className="confirm-dialog__actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            type="button"
            className="btn confirm-dialog__confirm"
            data-tone={tone}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
