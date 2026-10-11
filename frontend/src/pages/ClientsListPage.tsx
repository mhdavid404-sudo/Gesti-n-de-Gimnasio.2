import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { useAuth } from '../hooks/useAuth'
import { apiFetch, ApiError } from '../api/client'
import { clientListRows } from '../mocks/data'
import type { ApiClientProfile } from '../types/api'
import './ClientsListPage.css'

interface ClientsListLocationState {
  toast?: string
}

export function ClientsListPage() {
  const [query, setQuery] = useState('')
  const location = useLocation()
  const navigate = useNavigate()
  const { logout } = useAuth()

  const initialToast = (location.state as ClientsListLocationState | null)?.toast ?? null
  const [toast, setToast] = useState<string | null>(initialToast)

  const [clients, setClients] = useState<ApiClientProfile[] | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  // El mensaje de éxito viaja como router state desde /clientes/nuevo. Se
  // limpia del history en cuanto se muestra para que un refresh o un
  // "atrás" del navegador no lo repita.
  useEffect(() => {
    if (initialToast) {
      navigate('.', { replace: true, state: null })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const loadClients = () => {
    setIsLoading(true)
    setErrorMessage(null)
    apiFetch<ApiClientProfile[]>('/clients')
      .then((data) => setClients(data))
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setErrorMessage('No tienes permiso para ver el listado de clientes.')
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
    loadClients()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const filtered = useMemo(() => {
    if (!clients) return []
    const q = query.trim().toLowerCase()
    if (!q) return clients
    return clients.filter(
      (c) => c.full_name.toLowerCase().includes(q) || c.email.toLowerCase().includes(q),
    )
  }, [clients, query])

  return (
    <div className="clients-page">
      {toast && (
        <div className="clients-page__toast" role="status">
          <span>{toast}</span>
          <button
            type="button"
            className="clients-page__toast-dismiss"
            onClick={() => setToast(null)}
            aria-label="Cerrar aviso"
          >
            ×
          </button>
        </div>
      )}

      <div className="clients-page__toolbar">
        <input
          className="input clients-page__search"
          placeholder="Buscar por nombre o correo…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Buscar cliente"
          disabled={!clients}
        />
        <span className="clients-page__count">{clients ? `${filtered.length} clientes` : ''}</span>
        <span className="clients-page__toolbar-spacer" />
        <Link to="/clientes/nuevo" className="btn btn-primary">
          + Nuevo cliente
        </Link>
      </div>

      {isLoading ? (
        <div className="card">
          <LoadingState label="Cargando clientes…" variant="skeleton" rows={5} />
        </div>
      ) : errorMessage ? (
        <ErrorMessage message={errorMessage} onRetry={loadClients} />
      ) : filtered.length === 0 ? (
        <div className="card">
          <EmptyState
            title={query ? 'Sin resultados' : 'Todavía no hay clientes registrados'}
            description={
              query
                ? 'Ningún cliente coincide con tu búsqueda.'
                : 'Da de alta al primer cliente para empezar a usar el padrón.'
            }
            actionLabel={query ? undefined : 'Nuevo cliente'}
            actionHref={query ? undefined : '/clientes/nuevo'}
          />
        </div>
      ) : (
        <div className="card clients-page__table-wrap">
          <table className="clients-page__table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Contacto</th>
                <th>Entrenador</th>
                <th>Plan</th>
                <th>Membresía</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, index) => {
                // TODO(módulo Membresías, todavía no construido): "Plan" y
                // "Membresía" siguen con datos MOCK (`clientListRows`,
                // ver mocks/data.ts) indexados por posición, no por cliente
                // real -- los ids de `clientListRows` son de datos de
                // ejemplo y no corresponden a los ids reales de esta
                // tabla. Reemplazar por datos reales cuando exista
                // `GET /memberships?client_id=...`.
                const mockRow = clientListRows[index % clientListRows.length]
                return (
                  <tr
                    key={row.id}
                    style={{ animationDelay: `${Math.min(index, 12) * 45}ms` }}
                  >
                    <td>
                      <span className="clients-page__name">{row.full_name}</span>
                    </td>
                    <td>
                      <div className="clients-page__contact">
                        <span>{row.email}</span>
                        <span className="clients-page__phone">{row.phone ?? '—'}</span>
                      </div>
                    </td>
                    <td>{row.trainer_name ?? 'Sin asignar'}</td>
                    <td>{mockRow?.planName ?? 'Sin membresía'}</td>
                    <td>
                      <StatusPill status={mockRow?.membershipStatus ?? 'sin_membresia'} />
                    </td>
                    <td>
                      <Link to={`/clientes/${row.id}`} className="btn btn-ghost clients-page__view">
                        Ver detalle
                      </Link>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
