import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type { ApiActiveMembershipsBoard, ApiMembership, ApiMembershipPlan } from '../types/api'
import { getMembershipDisplayStatus } from '../utils/membership'
import './MembershipsPage.css'

function formatCurrency(value: string | number): string {
  return `$${Number(value).toLocaleString('es-MX')}`
}

/**
 * Entrega 3, ajuste de UX: esta pantalla deja de mostrar el catálogo de
 * planes (eso vive solo en `/planes-servicios`, ver DECISIONES.md) y pasa a
 * ser un tablero operativo de membresías ACTIVAS para `admin`/`entrenador`
 * (indicadores + tabla + acciones), conectado a `GET /memberships/board`.
 *
 * `cliente` NUNCA llega al tablero (el backend responde 403) -- para ese rol
 * esta misma ruta muestra en su lugar un panel simple de solo lectura
 * ("Mi membresía"), igual que ya hacía la pantalla antes de este ajuste.
 */
export function MembershipsPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isCliente = user?.role === 'cliente'

  const handleApiError = (err: unknown, onForbidden: () => void, onOther: (message: string) => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      if (err.status === 403) {
        onForbidden()
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  // --- Vista Cliente: "Mi membresía", solo lectura ------------------------
  const [myMemberships, setMyMemberships] = useState<ApiMembership[] | null>(null)
  const [myPlans, setMyPlans] = useState<ApiMembershipPlan[]>([])
  const [myLoading, setMyLoading] = useState(true)
  const [myError, setMyError] = useState<string | null>(null)

  useEffect(() => {
    if (!isCliente) return
    setMyLoading(true)
    setMyError(null)
    Promise.all([apiFetch<ApiMembership[]>('/memberships'), apiFetch<ApiMembershipPlan[]>('/membership-plans')])
      .then(([memberships, plans]) => {
        setMyMemberships(memberships)
        setMyPlans(plans)
      })
      .catch((err: unknown) =>
        handleApiError(err, () => setMyError('No tienes permiso para ver esta información.'), setMyError),
      )
      .finally(() => setMyLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCliente])

  const myPlanById = useMemo(() => {
    const map = new Map<number, ApiMembershipPlan>()
    myPlans.forEach((p) => map.set(p.id, p))
    return map
  }, [myPlans])

  // --- Vista Admin/Entrenador: tablero de membresías activas ---------------
  const [board, setBoard] = useState<ApiActiveMembershipsBoard | null>(null)
  const [boardLoading, setBoardLoading] = useState(true)
  const [boardError, setBoardError] = useState<string | null>(null)
  const [plans, setPlans] = useState<ApiMembershipPlan[]>([])
  const [search, setSearch] = useState('')
  const [planFilter, setPlanFilter] = useState('')
  const [toast, setToast] = useState<string | null>(null)
  const [errorToast, setErrorToast] = useState<string | null>(null)
  const [renewingId, setRenewingId] = useState<number | null>(null)
  const [isDetecting, setIsDetecting] = useState(false)

  const loadBoard = (q: string, planId: string) => {
    setBoardLoading(true)
    setBoardError(null)
    const params = new URLSearchParams()
    if (q.trim()) params.set('q', q.trim())
    if (planId) params.set('plan_id', planId)
    const qs = params.toString()
    apiFetch<ApiActiveMembershipsBoard>(`/memberships/board${qs ? `?${qs}` : ''}`)
      .then(setBoard)
      .catch((err: unknown) =>
        handleApiError(err, () => setBoardError('No tienes permiso para ver este tablero.'), setBoardError),
      )
      .finally(() => setBoardLoading(false))
  }

  useEffect(() => {
    if (isCliente) return
    apiFetch<ApiMembershipPlan[]>('/membership-plans')
      .then(setPlans)
      .catch(() => {
        // El filtro por plan es secundario -- si falla, el select simplemente queda sin opciones.
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCliente])

  // Búsqueda por nombre con un pequeño debounce -- evita un round-trip al
  // backend por cada tecla, consistente con que el filtro SÍ vive en el
  // servidor (a diferencia de ClientsListPage, aquí la tabla puede crecer
  // con el uso real del gimnasio día a día).
  useEffect(() => {
    if (isCliente) return
    const timeout = setTimeout(() => loadBoard(search, planFilter), 300)
    return () => clearTimeout(timeout)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, planFilter, isCliente])

  const handleDetectExpiring = async () => {
    setIsDetecting(true)
    try {
      const affected = await apiFetch<ApiMembership[]>('/memberships/detect-expiring', { method: 'POST' })
      setToast(
        affected.length === 0
          ? 'Todo al día, nada que actualizar.'
          : `${affected.length} membresía${affected.length === 1 ? '' : 's'} actualizada${affected.length === 1 ? '' : 's'}.`,
      )
      loadBoard(search, planFilter)
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthorized) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setErrorToast(err instanceof ApiError ? err.message : 'Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsDetecting(false)
    }
  }

  const handleRenew = async (membershipId: number) => {
    setRenewingId(membershipId)
    try {
      await apiFetch(`/memberships/${membershipId}/renew`, { method: 'POST' })
      setToast('Membresía renovada.')
      loadBoard(search, planFilter)
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthorized) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setErrorToast(err instanceof ApiError ? err.message : 'Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setRenewingId(null)
    }
  }

  if (isCliente) {
    return (
      <div className="memberships-page">
        <section>
          <div className="memberships-page__section-header">
            <h2 className="section-title">Mi membresía</h2>
          </div>

          {myLoading ? (
            <div className="card">
              <LoadingState label="Cargando tu membresía…" variant="skeleton" rows={3} />
            </div>
          ) : myError ? (
            <ErrorMessage message={myError} />
          ) : !myMemberships || myMemberships.length === 0 ? (
            <div className="card">
              <EmptyState
                title="Todavía no tienes una membresía"
                description="Acércate a recepción para activar tu membresía."
              />
            </div>
          ) : (
            <div className="card memberships-page__table-wrap">
              <table className="memberships-page__table">
                <thead>
                  <tr>
                    <th>Plan</th>
                    <th>Inicio</th>
                    <th>Vence</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {myMemberships.map((m) => (
                    <tr key={m.id}>
                      <td>{myPlanById.get(m.plan_id)?.name ?? 'Plan no disponible'}</td>
                      <td>{m.start_date}</td>
                      <td>{m.end_date}</td>
                      <td>
                        <StatusPill status={getMembershipDisplayStatus(m)} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    )
  }

  const indicators = board?.indicators
  const items = board?.items ?? []
  const hasActiveFilter = Boolean(search.trim() || planFilter)

  return (
    <div className="memberships-page">
      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}
      {errorToast && <Toast message={errorToast} tone="danger" onDismiss={() => setErrorToast(null)} />}

      <section className="memberships-page__indicators">
        <div className="card">
          <p className="memberships-page__indicator-label">Membresías activas</p>
          <p className="memberships-page__indicator-value">{indicators ? indicators.total_active : '—'}</p>
        </div>
        <div className="card">
          <p className="memberships-page__indicator-label">Vencen en 7 días o menos</p>
          <p className="memberships-page__indicator-value" data-tone={indicators?.expiring_soon ? 'warning' : undefined}>
            {indicators ? indicators.expiring_soon : '—'}
          </p>
        </div>
        {isAdmin && (
          <div className="card">
            <p className="memberships-page__indicator-label">Ingresos del mes</p>
            <p className="memberships-page__indicator-value">
              {indicators?.monthly_revenue != null ? formatCurrency(indicators.monthly_revenue) : '—'}
            </p>
          </div>
        )}
      </section>

      <section>
        <div className="memberships-page__toolbar">
          <input
            className="input memberships-page__search"
            placeholder="Buscar por nombre de cliente…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Buscar membresía por nombre de cliente"
          />
          <select
            className="input memberships-page__plan-filter"
            value={planFilter}
            onChange={(e) => setPlanFilter(e.target.value)}
            aria-label="Filtrar por plan"
          >
            <option value="">Todos los planes</option>
            {plans.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <span className="memberships-page__toolbar-spacer" />
          {isAdmin && (
            <button type="button" className="btn btn-ghost" onClick={handleDetectExpiring} disabled={isDetecting}>
              {isDetecting ? 'Revisando…' : 'Revisar vencimientos ahora'}
            </button>
          )}
        </div>

        {boardLoading ? (
          <div className="card">
            <LoadingState label="Cargando membresías…" variant="skeleton" rows={5} />
          </div>
        ) : boardError ? (
          <ErrorMessage message={boardError} onRetry={() => loadBoard(search, planFilter)} />
        ) : items.length === 0 ? (
          <div className="card">
            <EmptyState
              title={hasActiveFilter ? 'Sin resultados' : 'Todavía no hay membresías activas'}
              description={
                hasActiveFilter
                  ? 'Ningún cliente activo coincide con tu búsqueda.'
                  : 'Las membresías vencidas o canceladas no aparecen aquí -- consulta el reporte de vencimientos o la ficha del cliente.'
              }
            />
          </div>
        ) : (
          <div className="card memberships-page__table-wrap">
            <table className="memberships-page__table">
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Plan</th>
                  <th>Extras activos</th>
                  <th>Inicio</th>
                  <th>Vence</th>
                  <th>Días restantes</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={row.membership_id} className={row.expiring_soon ? 'memberships-page__row--expiring' : undefined}>
                    <td>{row.client_name}</td>
                    <td>{row.plan_name}</td>
                    <td className="memberships-page__extras">
                      {row.active_extras.length > 0 ? row.active_extras.join(', ') : '—'}
                    </td>
                    <td>{row.start_date}</td>
                    <td>{row.end_date}</td>
                    <td>
                      <span
                        className="memberships-page__days-remaining"
                        data-tone={row.expiring_soon ? 'warning' : undefined}
                      >
                        {row.days_remaining}
                      </span>
                    </td>
                    <td>
                      <div className="memberships-page__row-actions">
                        <Link to={`/clientes/${row.client_id}`} className="btn btn-ghost memberships-page__view">
                          Ver ficha
                        </Link>
                        {isAdmin && (
                          <>
                            <button
                              type="button"
                              className="btn btn-ghost"
                              onClick={() => handleRenew(row.membership_id)}
                              disabled={renewingId === row.membership_id}
                            >
                              {renewingId === row.membership_id ? 'Renovando…' : 'Renovar'}
                            </button>
                            <Link to={`/clientes/${row.client_id}?tab=pagos`} className="btn btn-primary">
                              Cobrar
                            </Link>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
