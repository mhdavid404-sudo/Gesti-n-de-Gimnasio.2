import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type { ApiClientProfile, ApiMembership, ApiMembershipPlan, MembershipPlanCreatePayload } from '../types/api'
import { getMembershipDisplayStatus } from '../utils/membership'
import './MembershipsPage.css'

type PlanFormField = 'name' | 'price' | 'durationDays'
type PlanFormErrors = Partial<Record<PlanFormField, string>>

/**
 * Conectado a la API real (RF004) — ver docstring de
 * `backend/src/api/v1/routers/memberships.py` para la autorización exacta
 * de cada endpoint. `MembershipRead` NO trae embebido el nombre del
 * cliente/plan (a diferencia de `ClientProfileRead`, ver DECISIONES.md) —
 * se carga `clients`/`membership-plans` UNA SOLA VEZ y se indexa en memoria
 * (`clientById`/`planById`) para evitar una llamada HTTP por fila.
 *
 * `GET /clients` está bloqueado para el rol `cliente` (403, ver
 * `routers/clients.py`) -- para ese rol se usa `GET /clients/me` (su propio
 * perfil) en vez de la lista completa, que de todos modos no la necesita:
 * `GET /memberships` para un `cliente` ya le devuelve solo la suya.
 */
export function MembershipsPage() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'

  const [plans, setPlans] = useState<ApiMembershipPlan[] | null>(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)

  const [memberships, setMemberships] = useState<ApiMembership[] | null>(null)
  const [membershipsLoading, setMembershipsLoading] = useState(true)
  const [membershipsError, setMembershipsError] = useState<string | null>(null)

  const [clients, setClients] = useState<ApiClientProfile[] | null>(null)
  const [clientsLoading, setClientsLoading] = useState(true)
  const [clientsError, setClientsError] = useState<string | null>(null)

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

  const loadPlans = () => {
    setPlansLoading(true)
    setPlansError(null)
    apiFetch<ApiMembershipPlan[]>('/membership-plans')
      .then(setPlans)
      .catch((err: unknown) =>
        handleApiError(
          err,
          () => setPlansError('No tienes permiso para ver el catálogo de planes.'),
          setPlansError,
        ),
      )
      .finally(() => setPlansLoading(false))
  }

  const loadMemberships = () => {
    setMembershipsLoading(true)
    setMembershipsError(null)
    apiFetch<ApiMembership[]>('/memberships')
      .then(setMemberships)
      .catch((err: unknown) =>
        handleApiError(
          err,
          () => setMembershipsError('No tienes permiso para ver las membresías.'),
          setMembershipsError,
        ),
      )
      .finally(() => setMembershipsLoading(false))
  }

  const loadClients = () => {
    setClientsLoading(true)
    setClientsError(null)
    const request =
      user?.role === 'cliente'
        ? apiFetch<ApiClientProfile>('/clients/me').then((profile) => [profile])
        : apiFetch<ApiClientProfile[]>('/clients')
    request
      .then(setClients)
      .catch((err: unknown) =>
        handleApiError(
          err,
          () => setClientsError('No tienes permiso para ver los datos de clientes.'),
          setClientsError,
        ),
      )
      .finally(() => setClientsLoading(false))
  }

  useEffect(() => {
    loadPlans()
    loadMemberships()
    loadClients()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const planById = useMemo(() => {
    const map = new Map<number, ApiMembershipPlan>()
    plans?.forEach((p) => map.set(p.id, p))
    return map
  }, [plans])

  const clientById = useMemo(() => {
    const map = new Map<number, ApiClientProfile>()
    clients?.forEach((c) => map.set(c.id, c))
    return map
  }, [clients])

  // --- Alta de plan (solo admin) ---------------------------------------
  const [showPlanForm, setShowPlanForm] = useState(false)
  const [planName, setPlanName] = useState('')
  const [planPrice, setPlanPrice] = useState('')
  const [planDuration, setPlanDuration] = useState('')
  const [planDescription, setPlanDescription] = useState('')
  const [planBenefits, setPlanBenefits] = useState('')
  const [planErrors, setPlanErrors] = useState<PlanFormErrors>({})
  const [planServerError, setPlanServerError] = useState<string | null>(null)
  const [isSubmittingPlan, setIsSubmittingPlan] = useState(false)
  const [planToast, setPlanToast] = useState<string | null>(null)

  const clearPlanError = (field: PlanFormField) => {
    setPlanErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev))
  }

  const resetPlanForm = () => {
    setPlanName('')
    setPlanPrice('')
    setPlanDuration('')
    setPlanDescription('')
    setPlanBenefits('')
    setPlanErrors({})
    setPlanServerError(null)
  }

  const validatePlanForm = (): PlanFormErrors => {
    const next: PlanFormErrors = {}
    if (!planName.trim()) next.name = 'Ingresa el nombre del plan.'
    const priceValue = Number(planPrice)
    if (!planPrice || Number.isNaN(priceValue) || priceValue <= 0) next.price = 'Ingresa un precio mayor a 0.'
    const durationValue = Number(planDuration)
    if (!planDuration || Number.isNaN(durationValue) || durationValue <= 0 || !Number.isInteger(durationValue)) {
      next.durationDays = 'Ingresa una duración en días mayor a 0.'
    }
    return next
  }

  const handleCreatePlan = async (event: FormEvent) => {
    event.preventDefault()
    setPlanServerError(null)

    const nextErrors = validatePlanForm()
    if (Object.keys(nextErrors).length > 0) {
      setPlanErrors(nextErrors)
      return
    }

    const payload: MembershipPlanCreatePayload = {
      name: planName.trim(),
      price: Number(planPrice),
      duration_days: Number(planDuration),
      description: planDescription.trim() || null,
      benefits: planBenefits
        .split('\n')
        .map((b) => b.trim())
        .filter((b) => b.length > 0),
    }

    setIsSubmittingPlan(true)
    try {
      const created = await apiFetch<ApiMembershipPlan>('/membership-plans', { method: 'POST', body: payload })
      setPlans((prev) => [...(prev ?? []), created])
      setPlanToast(`Plan "${created.name}" creado.`)
      resetPlanForm()
      setShowPlanForm(false)
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setPlanServerError('No tienes permiso para crear planes.')
          return
        }
        setPlanServerError(err.message)
        return
      }
      setPlanServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsSubmittingPlan(false)
    }
  }

  const tableLoading = membershipsLoading || clientsLoading || plansLoading
  const tableError = membershipsError ?? clientsError ?? plansError

  // --- Revisar vencimientos ahora (RF006, solo admin) --------------------
  // No hay scheduler real en este stack (ver DECISIONES.md, módulo
  // Vencimientos/Notificaciones) -- `DetectExpiringMembershipsUseCase` se
  // dispara manualmente desde aquí en vez de correr como job diario.
  const [isDetecting, setIsDetecting] = useState(false)
  const [detectToast, setDetectToast] = useState<string | null>(null)
  const [detectError, setDetectError] = useState<string | null>(null)

  const handleDetectExpiring = async () => {
    setIsDetecting(true)
    setDetectError(null)
    try {
      const affected = await apiFetch<ApiMembership[]>('/memberships/detect-expiring', { method: 'POST' })
      setDetectToast(
        affected.length === 0
          ? 'Todo al día, nada que actualizar.'
          : `${affected.length} membresía${affected.length === 1 ? '' : 's'} actualizada${affected.length === 1 ? '' : 's'}.`,
      )
      loadMemberships()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        setDetectError(err.message)
        return
      }
      setDetectError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsDetecting(false)
    }
  }

  return (
    <div className="memberships-page">
      {planToast && <Toast message={planToast} onDismiss={() => setPlanToast(null)} />}
      {detectToast && <Toast message={detectToast} onDismiss={() => setDetectToast(null)} />}
      {detectError && <Toast message={detectError} tone="danger" onDismiss={() => setDetectError(null)} />}

      <section>
        <div className="memberships-page__section-header">
          <h2 className="section-title">Planes</h2>
          {isAdmin && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                setShowPlanForm((prev) => !prev)
                if (showPlanForm) resetPlanForm()
              }}
            >
              {showPlanForm ? 'Cancelar' : '+ Nuevo plan'}
            </button>
          )}
        </div>

        {isAdmin && showPlanForm && (
          <form className="card plan-form" onSubmit={handleCreatePlan}>
            {planServerError && <ErrorMessage title="No se pudo crear el plan" message={planServerError} />}

            <div className="plan-form__row">
              <div className="plan-form__field">
                <label className="field-label" htmlFor="planName">
                  Nombre
                </label>
                <input
                  id="planName"
                  className="input"
                  value={planName}
                  onChange={(e) => {
                    setPlanName(e.target.value)
                    clearPlanError('name')
                  }}
                  placeholder="Ej. VIP"
                  data-invalid={Boolean(planErrors.name)}
                  aria-invalid={Boolean(planErrors.name)}
                  aria-describedby={planErrors.name ? 'planName-error' : undefined}
                />
                {planErrors.name && (
                  <p className="field-error" id="planName-error" role="alert">
                    {planErrors.name}
                  </p>
                )}
              </div>
              <div className="plan-form__field">
                <label className="field-label" htmlFor="planPrice">
                  Precio mensual
                </label>
                <input
                  id="planPrice"
                  type="number"
                  min={0}
                  step="0.01"
                  className="input"
                  value={planPrice}
                  onChange={(e) => {
                    setPlanPrice(e.target.value)
                    clearPlanError('price')
                  }}
                  placeholder="399"
                  data-invalid={Boolean(planErrors.price)}
                  aria-invalid={Boolean(planErrors.price)}
                  aria-describedby={planErrors.price ? 'planPrice-error' : undefined}
                />
                {planErrors.price && (
                  <p className="field-error" id="planPrice-error" role="alert">
                    {planErrors.price}
                  </p>
                )}
              </div>
              <div className="plan-form__field">
                <label className="field-label" htmlFor="planDuration">
                  Duración (días)
                </label>
                <input
                  id="planDuration"
                  type="number"
                  min={1}
                  step="1"
                  className="input"
                  value={planDuration}
                  onChange={(e) => {
                    setPlanDuration(e.target.value)
                    clearPlanError('durationDays')
                  }}
                  placeholder="30"
                  data-invalid={Boolean(planErrors.durationDays)}
                  aria-invalid={Boolean(planErrors.durationDays)}
                  aria-describedby={planErrors.durationDays ? 'planDuration-error' : undefined}
                />
                {planErrors.durationDays && (
                  <p className="field-error" id="planDuration-error" role="alert">
                    {planErrors.durationDays}
                  </p>
                )}
              </div>
            </div>

            <div className="plan-form__field">
              <label className="field-label" htmlFor="planDescription">
                Descripción
              </label>
              <input
                id="planDescription"
                className="input"
                value={planDescription}
                onChange={(e) => setPlanDescription(e.target.value)}
                placeholder="Acceso a piso de pesas y cardio en horario general."
              />
            </div>

            <div className="plan-form__field">
              <label className="field-label" htmlFor="planBenefits">
                Beneficios (uno por línea)
              </label>
              <textarea
                id="planBenefits"
                className="input plan-form__benefits-input"
                value={planBenefits}
                onChange={(e) => setPlanBenefits(e.target.value)}
                placeholder={'Acceso a piso de pesas\nZona de cardio\nCasillero diario'}
                rows={3}
              />
            </div>

            <div className="plan-form__actions">
              <button type="submit" className="btn btn-primary" disabled={isSubmittingPlan}>
                {isSubmittingPlan ? 'Creando…' : 'Crear plan'}
              </button>
            </div>
          </form>
        )}

        {plansLoading ? (
          <div className="card">
            <LoadingState label="Cargando planes…" variant="skeleton" rows={3} />
          </div>
        ) : plansError ? (
          <ErrorMessage message={plansError} onRetry={loadPlans} />
        ) : !plans || plans.length === 0 ? (
          <div className="card">
            <EmptyState
              title="Todavía no hay planes registrados"
              description={
                isAdmin
                  ? 'Crea el primer plan con el botón "+ Nuevo plan" para empezar a asignar membresías.'
                  : 'Todavía no se ha dado de alta ningún plan de membresía.'
              }
            />
          </div>
        ) : (
          <div className="memberships-page__plans">
            {plans.map((plan) => (
              <article key={plan.id} className="card plan-card" data-plan={plan.name}>
                <span className="plan-card__name">{plan.name}</span>
                <div className="plan-card__price">
                  ${Number(plan.price).toLocaleString('es-MX')}
                  <span>/{plan.duration_days === 30 ? 'mes' : `${plan.duration_days} días`}</span>
                </div>
                {plan.description && <p className="plan-card__description">{plan.description}</p>}
                {plan.benefits.length > 0 && (
                  <ul className="plan-card__benefits">
                    {plan.benefits.map((b) => (
                      <li key={b}>{b}</li>
                    ))}
                  </ul>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="memberships-page__section-header">
          <h2 className="section-title">Membresías activas</h2>
          {isAdmin && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={handleDetectExpiring}
              disabled={isDetecting}
            >
              {isDetecting ? 'Revisando…' : 'Revisar vencimientos ahora'}
            </button>
          )}
        </div>

        {tableLoading ? (
          <div className="card">
            <LoadingState label="Cargando membresías…" variant="skeleton" rows={5} />
          </div>
        ) : tableError ? (
          <ErrorMessage
            message={tableError}
            onRetry={() => {
              loadMemberships()
              loadClients()
              loadPlans()
            }}
          />
        ) : !memberships || memberships.length === 0 ? (
          <div className="card">
            <EmptyState
              title="Todavía no hay membresías asignadas"
              description="Asigna la primera membresía desde el detalle de un cliente."
            />
          </div>
        ) : (
          <div className="card memberships-page__table-wrap">
            <table className="memberships-page__table">
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Plan</th>
                  <th>Inicio</th>
                  <th>Vence</th>
                  <th>Estado</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {memberships.map((m) => {
                  const client = clientById.get(m.client_id)
                  const plan = planById.get(m.plan_id)
                  return (
                    <tr key={m.id}>
                      <td>{client?.full_name ?? 'Cliente no disponible'}</td>
                      <td>{plan?.name ?? 'Plan no disponible'}</td>
                      <td>{m.start_date}</td>
                      <td>{m.end_date}</td>
                      <td>
                        <StatusPill status={getMembershipDisplayStatus(m)} />
                      </td>
                      <td>
                        <Link to={`/clientes/${m.client_id}`} className="btn btn-ghost memberships-page__view">
                          Ver cliente
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
