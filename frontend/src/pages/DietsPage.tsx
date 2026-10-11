import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { StatusPill } from '../components/ui/StatusPill'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type {
  ApiClientProfile,
  ApiDietAssignment,
  ApiDietAssignmentStatus,
  ApiDietPlan,
  DietAssignmentCreatePayload,
  DietPlanCreatePayload,
} from '../types/api'
import './DietsPage.css'

const todayIso = () => new Date().toISOString().slice(0, 10)

const ASSIGNMENT_STATUSES: { value: ApiDietAssignmentStatus; label: string }[] = [
  { value: 'activa', label: 'Activa' },
  { value: 'completada', label: 'Completada' },
  { value: 'cancelada', label: 'Cancelada' },
]

/**
 * Conectado a la API real (RF009, RF012, RF013) — ver docstring de
 * `backend/src/api/v1/routers/diets.py` para la autorización exacta de
 * cada endpoint. Mismo patrón que `RoutinesPage.tsx` (ver DECISIONES.md,
 * módulo Dietas), simplificado donde corresponde: un `DietPlan` no tiene
 * un catálogo de sub-items equivalente a `Exercise`/`RoutineExercise`, así
 * que no hay carga bajo demanda de "items de un plan" ni formulario de
 * "agregar item" -- el plan es plano (nombre/descripción/objetivo calórico).
 *
 * Igual que Rutinas, no existe un endpoint de "listar TODAS las
 * asignaciones del gimnasio" (a propósito, mismo criterio de
 * ownership-por-dato) -- la sección "Asignaciones" elige un cliente
 * (`GET /clients`, ya scoped por rol) y muestra/gestiona el historial de
 * dietas de ESE cliente (`GET /diets/assignments/clients/{id}`). Para el
 * rol `cliente` no hay selector: se resuelve su propio `client_id` vía
 * `GET /clients/me` y se muestra directo su propio historial (RF013,
 * solo lectura).
 */
export function DietsPage() {
  const { user, logout } = useAuth()
  const isStaff = user?.role === 'admin' || user?.role === 'entrenador'
  const isCliente = user?.role === 'cliente'

  const handleAuthError = (err: unknown, onOther: (message: string) => void, onForbidden?: () => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        return
      }
      if (err.status === 403 && onForbidden) {
        onForbidden()
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  // --- Catálogo de planes de dieta -----------------------------------------
  const [plans, setPlans] = useState<ApiDietPlan[] | null>(null)
  const [plansLoading, setPlansLoading] = useState(true)
  const [plansError, setPlansError] = useState<string | null>(null)

  const loadPlans = () => {
    setPlansLoading(true)
    setPlansError(null)
    apiFetch<ApiDietPlan[]>('/diets/plans')
      .then(setPlans)
      .catch((err: unknown) => handleAuthError(err, setPlansError))
      .finally(() => setPlansLoading(false))
  }

  useEffect(() => {
    loadPlans()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const planById = useMemo(() => {
    const map = new Map<number, ApiDietPlan>()
    plans?.forEach((p) => map.set(p.id, p))
    return map
  }, [plans])

  // Alta de plan (admin/entrenador) -- sin esto el catálogo nunca podría
  // poblarse (no hay seed), mismo criterio ya usado en Rutinas/Membresías.
  const [showPlanForm, setShowPlanForm] = useState(false)
  const [planName, setPlanName] = useState('')
  const [planDescription, setPlanDescription] = useState('')
  const [planCalories, setPlanCalories] = useState('')
  const [planServerError, setPlanServerError] = useState<string | null>(null)
  const [isSubmittingPlan, setIsSubmittingPlan] = useState(false)
  const [planToast, setPlanToast] = useState<string | null>(null)

  const resetPlanForm = () => {
    setPlanName('')
    setPlanDescription('')
    setPlanCalories('')
    setPlanServerError(null)
  }

  const handleCreatePlan = async (event: FormEvent) => {
    event.preventDefault()
    setPlanServerError(null)

    if (!planName.trim()) {
      setPlanServerError('Ingresa el nombre del plan.')
      return
    }

    const caloriesValue = planCalories ? Number(planCalories) : null
    if (planCalories && (Number.isNaN(caloriesValue) || (caloriesValue ?? 0) <= 0)) {
      setPlanServerError('Ingresa un objetivo calórico mayor a 0, o déjalo vacío.')
      return
    }

    const payload: DietPlanCreatePayload = {
      name: planName.trim(),
      description: planDescription.trim() || null,
      calories_target: caloriesValue,
    }

    setIsSubmittingPlan(true)
    try {
      const created = await apiFetch<ApiDietPlan>('/diets/plans', { method: 'POST', body: payload })
      setPlans((prev) => [created, ...(prev ?? [])])
      setPlanToast(`Plan "${created.name}" creado.`)
      resetPlanForm()
      setShowPlanForm(false)
    } catch (err) {
      handleAuthError(
        err,
        setPlanServerError,
        () => setPlanServerError('No tienes permiso para crear planes de dieta.'),
      )
    } finally {
      setIsSubmittingPlan(false)
    }
  }

  // --- Asignaciones ---------------------------------------------------------
  // Selector de cliente (admin/entrenador) en vez de una tabla global --
  // ver docstring de la función y DECISIONES.md.
  const [clients, setClients] = useState<ApiClientProfile[] | null>(null)
  const [clientsLoading, setClientsLoading] = useState(true)
  const [clientsError, setClientsError] = useState<string | null>(null)
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [ownClientName, setOwnClientName] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return

    if (isCliente) {
      setClientsLoading(true)
      setClientsError(null)
      apiFetch<ApiClientProfile>('/clients/me')
        .then((profile) => {
          setSelectedClientId(profile.id)
          setOwnClientName(profile.full_name)
        })
        .catch((err: unknown) => handleAuthError(err, setClientsError))
        .finally(() => setClientsLoading(false))
      return
    }

    setClientsLoading(true)
    setClientsError(null)
    apiFetch<ApiClientProfile[]>('/clients')
      .then((data) => setClients(data))
      .catch((err: unknown) =>
        handleAuthError(err, setClientsError, () => setClientsError('No tienes permiso para ver clientes.')),
      )
      .finally(() => setClientsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.role])

  const [assignments, setAssignments] = useState<ApiDietAssignment[] | null>(null)
  const [assignmentsLoading, setAssignmentsLoading] = useState(false)
  const [assignmentsError, setAssignmentsError] = useState<string | null>(null)

  const loadAssignments = (clientId: number) => {
    setAssignmentsLoading(true)
    setAssignmentsError(null)
    apiFetch<ApiDietAssignment[]>(`/diets/assignments/clients/${clientId}`)
      .then(setAssignments)
      .catch((err: unknown) =>
        handleAuthError(err, setAssignmentsError, () => setAssignmentsError('No tienes acceso al historial de este cliente.')),
      )
      .finally(() => setAssignmentsLoading(false))
  }

  useEffect(() => {
    if (selectedClientId == null) {
      setAssignments(null)
      return
    }
    loadAssignments(selectedClientId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClientId])

  // Alta de asignación (admin/entrenador) -----------------------------------
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [assignPlanId, setAssignPlanId] = useState('')
  const [assignDate, setAssignDate] = useState(todayIso)
  const [assignServerError, setAssignServerError] = useState<string | null>(null)
  const [isAssigning, setIsAssigning] = useState(false)
  const [assignToast, setAssignToast] = useState<string | null>(null)

  const resetAssignForm = () => {
    setAssignPlanId('')
    setAssignDate(todayIso())
    setAssignServerError(null)
  }

  const handleCreateAssignment = async (event: FormEvent) => {
    event.preventDefault()
    setAssignServerError(null)
    if (selectedClientId == null) return

    if (!assignPlanId) {
      setAssignServerError('Selecciona un plan de dieta.')
      return
    }
    if (!assignDate) {
      setAssignServerError('Selecciona una fecha de asignación.')
      return
    }

    const payload: DietAssignmentCreatePayload = {
      diet_plan_id: Number(assignPlanId),
      client_id: selectedClientId,
      assigned_date: assignDate,
    }

    setIsAssigning(true)
    try {
      const created = await apiFetch<ApiDietAssignment>('/diets/assignments', { method: 'POST', body: payload })
      setAssignments((prev) => [created, ...(prev ?? [])])
      setAssignToast('Dieta asignada correctamente.')
      resetAssignForm()
      setShowAssignForm(false)
    } catch (err) {
      handleAuthError(
        err,
        setAssignServerError,
        () => setAssignServerError('No tienes permiso para asignar esta dieta a este cliente.'),
      )
    } finally {
      setIsAssigning(false)
    }
  }

  // Cambiar status de una asignación existente (admin, o entrenador dueño
  // del cliente -- ya garantizado porque solo aparece en el selector si el
  // backend lo dejó ver/listar, ver docstring de la función).
  const [updatingAssignmentId, setUpdatingAssignmentId] = useState<number | null>(null)
  const [updateError, setUpdateError] = useState<string | null>(null)

  const handleUpdateStatus = async (assignment: ApiDietAssignment, status: ApiDietAssignmentStatus) => {
    if (status === assignment.status) return
    setUpdateError(null)
    setUpdatingAssignmentId(assignment.id)
    try {
      const updated = await apiFetch<ApiDietAssignment>(`/diets/assignments/${assignment.id}`, {
        method: 'PATCH',
        body: { status },
      })
      setAssignments((prev) => (prev ?? []).map((a) => (a.id === updated.id ? updated : a)))
    } catch (err) {
      handleAuthError(
        err,
        setUpdateError,
        () => setUpdateError('No tienes permiso para actualizar esta asignación.'),
      )
    } finally {
      setUpdatingAssignmentId(null)
    }
  }

  const selectedClient = clients?.find((c) => c.id === selectedClientId)

  return (
    <div className="diets-page">
      {planToast && <Toast message={planToast} onDismiss={() => setPlanToast(null)} />}
      {assignToast && <Toast message={assignToast} onDismiss={() => setAssignToast(null)} />}
      {updateError && <Toast message={updateError} tone="danger" onDismiss={() => setUpdateError(null)} />}

      <section>
        <div className="diets-page__section-header">
          <h2 className="section-title">Planes de dieta</h2>
          <span className="eyebrow">
            {plansLoading ? '…' : plans ? `${plans.length} planes en catálogo` : '0 planes en catálogo'}
          </span>
        </div>

        {plansError && <ErrorMessage message={plansError} onRetry={loadPlans} />}

        {isStaff && (
          <div className="diets-page__toolbar">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                setShowPlanForm((prev) => !prev)
                if (showPlanForm) resetPlanForm()
              }}
            >
              {showPlanForm ? 'Cancelar' : '+ Nuevo plan'}
            </button>
          </div>
        )}

        {isStaff && showPlanForm && (
          <form className="card diets-page__inline-form" onSubmit={handleCreatePlan}>
            {planServerError && <ErrorMessage title="No se pudo crear el plan" message={planServerError} />}
            <div className="diets-page__form-row">
              <div className="diets-page__field">
                <label className="field-label" htmlFor="planName">
                  Nombre
                </label>
                <input
                  id="planName"
                  className="input"
                  value={planName}
                  onChange={(e) => setPlanName(e.target.value)}
                  placeholder="Ej. Déficit calórico moderado"
                />
              </div>
              <div className="diets-page__field">
                <label className="field-label" htmlFor="planCalories">
                  Objetivo calórico (opcional)
                </label>
                <input
                  id="planCalories"
                  type="number"
                  min={1}
                  className="input"
                  value={planCalories}
                  onChange={(e) => setPlanCalories(e.target.value)}
                  placeholder="Ej. 2000"
                />
              </div>
            </div>
            <div className="diets-page__field">
              <label className="field-label" htmlFor="planDescription">
                Descripción (opcional)
              </label>
              <input
                id="planDescription"
                className="input"
                value={planDescription}
                onChange={(e) => setPlanDescription(e.target.value)}
                placeholder="Ej. 5 comidas al día, alto en proteína…"
              />
            </div>
            <div className="diets-page__form-actions">
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
        ) : !plans || plans.length === 0 ? (
          <div className="card">
            <EmptyState
              title="Todavía no hay planes de dieta en el catálogo"
              description={
                isStaff
                  ? 'Crea el primer plan con el botón "+ Nuevo plan" para empezar a asignarlo a tus clientes.'
                  : 'Todavía no se ha dado de alta ningún plan.'
              }
            />
          </div>
        ) : (
          <div className="diets-page__catalog">
            {plans.map((plan) => (
              <article key={plan.id} className="card diet-card">
                <span className="diet-card__name">{plan.name}</span>
                {plan.description && <p className="diet-card__description">{plan.description}</p>}
                <div className="diet-card__calories">
                  {plan.calories_target ? (
                    <>
                      <strong>{plan.calories_target}</strong> kcal / día
                    </>
                  ) : (
                    'Sin objetivo calórico fijo'
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="diets-page__assign-section">
        <div className="diets-page__section-header">
          <h2 className="section-title">Asignaciones</h2>
        </div>

        {clientsLoading ? (
          <div className="card">
            <LoadingState label="Cargando clientes…" variant="skeleton" rows={2} />
          </div>
        ) : clientsError ? (
          <ErrorMessage message={clientsError} />
        ) : isCliente ? (
          <p className="eyebrow diets-page__own-client">{ownClientName ?? 'Tu historial de dietas'}</p>
        ) : (
          <div className="card diets-page__client-picker">
            <label className="field-label" htmlFor="diet-assign-client-select">
              Cliente
            </label>
            <select
              id="diet-assign-client-select"
              className="input"
              value={selectedClientId ?? ''}
              onChange={(e) => setSelectedClientId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Selecciona un cliente</option>
              {clients?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {selectedClientId == null ? (
          <div className="card">
            <EmptyState
              title="Selecciona un cliente"
              description="Elige un cliente arriba para ver y gestionar su historial de dietas asignadas."
            />
          </div>
        ) : (
          <>
            {isStaff && (
              <div className="diets-page__toolbar">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    setShowAssignForm((prev) => !prev)
                    if (showAssignForm) resetAssignForm()
                  }}
                  disabled={!plans || plans.length === 0}
                >
                  {showAssignForm ? 'Cancelar' : '+ Asignar dieta'}
                </button>
              </div>
            )}

            {isStaff && showAssignForm && (
              <form className="card diets-page__inline-form" onSubmit={handleCreateAssignment}>
                {assignServerError && (
                  <ErrorMessage title="No se pudo asignar la dieta" message={assignServerError} />
                )}
                <div className="diets-page__form-row">
                  <div className="diets-page__field">
                    <label className="field-label" htmlFor="assignPlanSelect">
                      Plan
                    </label>
                    <select
                      id="assignPlanSelect"
                      className="input"
                      value={assignPlanId}
                      onChange={(e) => setAssignPlanId(e.target.value)}
                    >
                      <option value="">Selecciona un plan</option>
                      {plans?.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="diets-page__field">
                    <label className="field-label" htmlFor="assignDateInput">
                      Fecha de asignación
                    </label>
                    <input
                      id="assignDateInput"
                      type="date"
                      className="input"
                      value={assignDate}
                      onChange={(e) => setAssignDate(e.target.value)}
                    />
                  </div>
                </div>
                <div className="diets-page__form-actions">
                  <button type="submit" className="btn btn-primary" disabled={isAssigning}>
                    {isAssigning ? 'Asignando…' : 'Asignar dieta'}
                  </button>
                </div>
              </form>
            )}

            {assignmentsLoading ? (
              <div className="card">
                <LoadingState label="Cargando historial…" variant="skeleton" rows={4} />
              </div>
            ) : assignmentsError ? (
              <ErrorMessage message={assignmentsError} onRetry={() => loadAssignments(selectedClientId)} />
            ) : !assignments || assignments.length === 0 ? (
              <div className="card">
                <EmptyState
                  title="Sin dietas asignadas"
                  description={
                    isStaff
                      ? `${selectedClient?.full_name ?? 'Este cliente'} todavía no tiene dietas asignadas.`
                      : 'Todavía no tienes dietas asignadas.'
                  }
                />
              </div>
            ) : (
              <div className="card diets-page__table-wrap">
                <table className="diets-page__table">
                  <thead>
                    <tr>
                      <th>Plan</th>
                      <th>Asignada</th>
                      <th>Notas</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {assignments.map((da) => (
                      <tr key={da.id}>
                        <td>{planById.get(da.diet_plan_id)?.name ?? `#${da.diet_plan_id}`}</td>
                        <td>{da.assigned_date}</td>
                        <td>{da.notes ?? '—'}</td>
                        <td>
                          {isStaff ? (
                            <select
                              className="input diets-page__status-select"
                              value={da.status}
                              disabled={updatingAssignmentId === da.id}
                              onChange={(e) => handleUpdateStatus(da, e.target.value as ApiDietAssignmentStatus)}
                            >
                              {ASSIGNMENT_STATUSES.map((s) => (
                                <option key={s.value} value={s.value}>
                                  {s.label}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <StatusPill status={da.status} />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}
