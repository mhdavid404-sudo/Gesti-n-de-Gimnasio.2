import { useEffect, useState } from 'react'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { useAuth } from '../hooks/useAuth'
import type { ApiAuditLog } from '../types/api'
import './AuditLogsPage.css'

/**
 * Conectado a la API real (RF015, modulo Bitacora) -- `GET /audit-logs`,
 * solo `admin`. Las entradas las genera el backend de forma automatica
 * (cualquier error HTTP 4xx/5xx se registra solo, ver
 * `backend/src/api/main.py`); esta pantalla es de solo lectura, no hay
 * ningun formulario de alta a proposito.
 */
export function AuditLogsPage() {
  const { logout } = useAuth()
  const [logs, setLogs] = useState<ApiAuditLog[] | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const loadLogs = () => {
    setIsLoading(true)
    setErrorMessage(null)
    apiFetch<ApiAuditLog[]>('/audit-logs?limit=200')
      .then(setLogs)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            return
          }
          if (err.status === 403) {
            setErrorMessage('Solo el administrador puede consultar la bitácora del sistema.')
            return
          }
          setErrorMessage(err.message)
          return
        }
        setErrorMessage('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setIsLoading(false))
  }

  useEffect(() => {
    loadLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="audit-logs-page">
      <div className="audit-logs-page__header">
        <h2 className="section-title">Bitácora del sistema</h2>
        <span className="eyebrow">Errores y eventos registrados automáticamente</span>
      </div>

      {isLoading ? (
        <div className="card">
          <LoadingState label="Cargando bitácora…" variant="skeleton" rows={6} />
        </div>
      ) : errorMessage ? (
        <ErrorMessage message={errorMessage} onRetry={loadLogs} />
      ) : !logs || logs.length === 0 ? (
        <div className="card">
          <EmptyState title="Sin eventos registrados" description="Todavía no se ha registrado ningún error en el sistema." />
        </div>
      ) : (
        <div className="card audit-logs-page__table-wrap">
          <table className="audit-logs-page__table data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Acción</th>
                <th>Usuario</th>
                <th>Módulo</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.created_at).toLocaleString('es-MX')}</td>
                  <td>{log.action}</td>
                  <td>{log.user_id ?? '—'}</td>
                  <td>{log.entity_type ?? '—'}</td>
                  <td className="audit-logs-page__details">{log.details ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
