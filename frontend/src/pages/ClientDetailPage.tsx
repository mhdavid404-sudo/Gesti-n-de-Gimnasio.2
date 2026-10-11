import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatusPill } from '../components/ui/StatusPill'
import { Tabs } from '../components/ui/Tabs'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import { findDietPlan, getBodyProgressForClient, getDietAssignmentsForClient } from '../mocks/data'
import type {
  ApiClientProfile,
  ApiExercise,
  ApiMembership,
  ApiMembershipPlan,
  ApiPayment,
  ApiPaymentMethod,
  ApiRoutine,
  ApiRoutineAssignment,
  ApiRoutineExercise,
  MembershipCreatePayload,
  PaymentCreatePayload,
  RoutineAssignmentCreatePayload,
} from '../types/api'
import { addDaysIso, getMembershipDisplayStatus, pickCurrentMembership } from '../utils/membership'
import './ClientDetailPage.css'

const todayIso = () => new Date().toISOString().slice(0, 10)

const PAYMENT_METHODS: { value: ApiPaymentMethod; label: string }[] = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'tarjeta', label: 'Tarjeta' },
  { value: 'transferencia', label: 'Transferencia' },
]

type PaymentFormField = 'amount' | 'paymentDate'
type PaymentFormErrors = Partial<Record<PaymentFormField, string>>

const TABS = [
  { id: 'perfil', label: 'Perfil' },
  { id: 'membresia', label: 'Membresía' },
  { id: 'pagos', label: 'Pagos' },
  { id: 'rutina', label: 'Rutina' },
  { id: 'dieta', label: 'Dieta' },
  { id: 'progreso', label: 'Progreso' },
]

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState('perfil')
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'
  const clientProfileId = Number(id)

  const [profile, setProfile] = useState<ApiClientProfile | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  useEffect(() => {
    setIsLoading(true)
    setErrorMessage(null)
    setNotFound(false)

    apiFetch<ApiClientProfile>(`/clients/${clientProfileId}`)
      .then(setProfile)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 404) {
            setNotFound(true)
            return
          }
          if (err.status === 403) {
            setErrorMessage('No tienes permiso para ver este cliente.')
            return
          }
          setErrorMessage(err.message)
          return
        }
        setErrorMessage('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setIsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientProfileId])

  // --- Membresía (RF004, módulo Planes y Membresías) -----------------------
  // `GET /memberships?client_id=` puede devolver varias (historial) -- "la"
  // membresía a mostrar se elige con `pickCurrentMembership` (prefiere
  // `activa`; si no hay, la de `end_date` más lejana), ver utils/membership.ts.
  const [membership, setMembership] = useState<ApiMembership | null>(null)
  const [membershipLoading, setMembershipLoading] = useState(true)
  const [membershipError, setMembershipError] = useState<string | null>(null)

  useEffect(() => {
    setMembershipLoading(true)
    setMembershipError(null)

    apiFetch<ApiMembership[]>(`/memberships?client_id=${clientProfileId}`)
      .then((list) => setMembership(pickCurrentMembership(list) ?? null))
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setMembershipError('No tienes permiso para ver la membresía de este cliente.')
            return
          }
          setMembershipError(err.message)
          return
        }
        setMembershipError('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setMembershipLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientProfileId])

  // Catálogo de planes -- se necesita tanto para mostrar el plan de la
  // membresía vigente (nombre/precio/beneficios, `MembershipRead` no los
  // trae embebidos) como para el selector del formulario de alta. Se carga
  // una sola vez; si falla, el formulario de asignación simplemente queda
  // sin opciones (mensaje ya cubre ese caso más abajo).
  const [plans, setPlans] = useState<ApiMembershipPlan[]>([])

  useEffect(() => {
    apiFetch<ApiMembershipPlan[]>('/membership-plans')
      .then(setPlans)
      .catch(() => setPlans([]))
  }, [])

  const plan = useMemo(
    () => (membership ? plans.find((p) => p.id === membership.plan_id) : undefined),
    [membership, plans],
  )

  // --- Asignar membresía (solo admin, ver docstring del router backend) ---
  const [showAssignForm, setShowAssignForm] = useState(false)
  const [assignPlanId, setAssignPlanId] = useState('')
  const [assignStartDate, setAssignStartDate] = useState(todayIso)
  const [assignServerError, setAssignServerError] = useState<string | null>(null)
  const [isAssigning, setIsAssigning] = useState(false)
  const [assignToast, setAssignToast] = useState<string | null>(null)

  const selectedAssignPlan = plans.find((p) => p.id === Number(assignPlanId))
  const computedEndDate = selectedAssignPlan ? addDaysIso(assignStartDate, selectedAssignPlan.duration_days) : ''

  const handleAssignSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setAssignServerError(null)

    if (!selectedAssignPlan || !assignStartDate) {
      setAssignServerError('Selecciona un plan y una fecha de inicio.')
      return
    }

    const payload: MembershipCreatePayload = {
      client_id: clientProfileId,
      plan_id: selectedAssignPlan.id,
      start_date: assignStartDate,
      end_date: addDaysIso(assignStartDate, selectedAssignPlan.duration_days),
      status: 'activa',
    }

    setIsAssigning(true)
    try {
      const created = await apiFetch<ApiMembership>('/memberships', { method: 'POST', body: payload })
      setMembership(created)
      setAssignToast(`Membresía "${selectedAssignPlan.name}" asignada correctamente.`)
      setShowAssignForm(false)
      setAssignPlanId('')
      setAssignStartDate(todayIso())
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setAssignServerError('No tienes permiso para asignar membresías.')
          return
        }
        setAssignServerError(err.message)
        return
      }
      setAssignServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsAssigning(false)
    }
  }

  // --- Pagos (RF005, módulo Pagos) -----------------------------------------
  // Depende de la membresía resuelta arriba (comparte el mismo fetch, no se
  // vuelve a llamar `GET /memberships` aquí) -- sin membresía no hay
  // `membership_id` que filtrar, así que la pestaña ofrece un EmptyState que
  // manda a la pestaña "Membresía" en vez de pedir uno.
  const [payments, setPayments] = useState<ApiPayment[]>([])
  const [paymentsLoading, setPaymentsLoading] = useState(true)
  const [paymentsError, setPaymentsError] = useState<string | null>(null)

  const loadPayments = (membershipId: number) => {
    setPaymentsLoading(true)
    setPaymentsError(null)
    apiFetch<ApiPayment[]>(`/payments?membership_id=${membershipId}`)
      .then(setPayments)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setPaymentsError('No tienes permiso para ver los pagos de este cliente.')
            return
          }
          setPaymentsError(err.message)
          return
        }
        setPaymentsError('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setPaymentsLoading(false))
  }

  useEffect(() => {
    if (membershipLoading) return
    if (!membership) {
      setPayments([])
      setPaymentsLoading(false)
      return
    }
    loadPayments(membership.id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [membership?.id, membershipLoading])

  // --- Registrar pago (solo admin) -----------------------------------------
  const [showPaymentForm, setShowPaymentForm] = useState(false)
  const [paymentAmount, setPaymentAmount] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<ApiPaymentMethod>('efectivo')
  const [paymentDate, setPaymentDate] = useState(todayIso)
  const [paymentNotes, setPaymentNotes] = useState('')
  const [paymentErrors, setPaymentErrors] = useState<PaymentFormErrors>({})
  const [paymentServerError, setPaymentServerError] = useState<string | null>(null)
  const [isRegisteringPayment, setIsRegisteringPayment] = useState(false)
  const [paymentToast, setPaymentToast] = useState<string | null>(null)

  const clearPaymentError = (field: PaymentFormField) => {
    setPaymentErrors((prev) => (prev[field] ? { ...prev, [field]: undefined } : prev))
  }

  const resetPaymentForm = () => {
    setPaymentAmount('')
    setPaymentMethod('efectivo')
    setPaymentDate(todayIso())
    setPaymentNotes('')
    setPaymentErrors({})
    setPaymentServerError(null)
  }

  const handleRegisterPayment = async (event: FormEvent) => {
    event.preventDefault()
    setPaymentServerError(null)
    if (!membership) return

    const nextErrors: PaymentFormErrors = {}
    const amountValue = Number(paymentAmount)
    if (!paymentAmount || Number.isNaN(amountValue) || amountValue <= 0) {
      nextErrors.amount = 'Ingresa un monto mayor a 0.'
    }
    if (!paymentDate) nextErrors.paymentDate = 'Selecciona una fecha de pago.'
    if (Object.keys(nextErrors).length > 0) {
      setPaymentErrors(nextErrors)
      return
    }

    const payload: PaymentCreatePayload = {
      membership_id: membership.id,
      amount: amountValue,
      payment_date: paymentDate,
      method: paymentMethod,
      notes: paymentNotes.trim() || null,
    }

    setIsRegisteringPayment(true)
    try {
      const created = await apiFetch<ApiPayment>('/payments', { method: 'POST', body: payload })
      setPayments((prev) => [created, ...prev])
      setPaymentToast('Pago registrado correctamente.')
      setShowPaymentForm(false)
      resetPaymentForm()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setPaymentServerError('No tienes permiso para registrar pagos.')
          return
        }
        setPaymentServerError(err.message)
        return
      }
      setPaymentServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsRegisteringPayment(false)
    }
  }

  // --- Rutina (RF007/RF008, módulo Ejercicios y Rutinas) ------------------
  // Mismo patrón ya usado arriba por la pestaña "Membresía": historial real
  // vía `GET /routines/assignments/clients/{id}` (ownership por dato ya
  // resuelto en el backend -- si esta pantalla cargó, el rol actual ya tenía
  // acceso a este cliente, ver docstring del router). Si es `entrenador` o
  // `admin`, puede asignar una rutina nueva del catálogo.
  const isStaff = user?.role === 'admin' || user?.role === 'entrenador'

  const [routineAssignments, setRoutineAssignments] = useState<ApiRoutineAssignment[] | null>(null)
  const [routineAssignmentsLoading, setRoutineAssignmentsLoading] = useState(true)
  const [routineAssignmentsError, setRoutineAssignmentsError] = useState<string | null>(null)

  const loadRoutineAssignments = () => {
    setRoutineAssignmentsLoading(true)
    setRoutineAssignmentsError(null)
    apiFetch<ApiRoutineAssignment[]>(`/routines/assignments/clients/${clientProfileId}`)
      .then(setRoutineAssignments)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setRoutineAssignmentsError('No tienes permiso para ver las rutinas de este cliente.')
            return
          }
          setRoutineAssignmentsError(err.message)
          return
        }
        setRoutineAssignmentsError('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setRoutineAssignmentsLoading(false))
  }

  useEffect(() => {
    loadRoutineAssignments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientProfileId])

  // Catálogo de rutinas (para el selector del formulario de asignación) y de
  // ejercicios (para mostrar los nombres dentro de cada rutina asignada) --
  // se cargan una sola vez, mismo criterio que el catálogo de planes arriba.
  const [routinesCatalog, setRoutinesCatalog] = useState<ApiRoutine[]>([])
  const [exercisesCatalog, setExercisesCatalog] = useState<ApiExercise[]>([])

  useEffect(() => {
    apiFetch<ApiRoutine[]>('/routines').then(setRoutinesCatalog).catch(() => setRoutinesCatalog([]))
    apiFetch<ApiExercise[]>('/exercises').then(setExercisesCatalog).catch(() => setExercisesCatalog([]))
  }, [])

  const routineById = useMemo(() => {
    const map = new Map<number, ApiRoutine>()
    routinesCatalog.forEach((r) => map.set(r.id, r))
    return map
  }, [routinesCatalog])

  const exerciseById = useMemo(() => {
    const map = new Map<number, ApiExercise>()
    exercisesCatalog.forEach((e) => map.set(e.id, e))
    return map
  }, [exercisesCatalog])

  // Ejercicios de cada rutina asignada -- se cargan en cuanto se conoce el
  // historial (un cliente tiene pocas asignaciones, no amerita carga bajo
  // demanda como en el catálogo completo de RoutinesPage.tsx).
  const [routineExercisesById, setRoutineExercisesById] = useState<Map<number, ApiRoutineExercise[]>>(new Map())

  useEffect(() => {
    if (!routineAssignments) return
    const pendingIds = Array.from(new Set(routineAssignments.map((ra) => ra.routine_id))).filter(
      (id) => !routineExercisesById.has(id),
    )
    pendingIds.forEach((routineId) => {
      apiFetch<ApiRoutineExercise[]>(`/routines/${routineId}/exercises`)
        .then((items) => {
          setRoutineExercisesById((prev) => new Map(prev).set(routineId, items))
        })
        .catch(() => {
          setRoutineExercisesById((prev) => new Map(prev).set(routineId, []))
        })
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routineAssignments])

  // --- Asignar rutina (admin/entrenador dueño del cliente) -----------------
  const [showAssignRoutineForm, setShowAssignRoutineForm] = useState(false)
  const [assignRoutineId, setAssignRoutineId] = useState('')
  const [assignRoutineDate, setAssignRoutineDate] = useState(todayIso)
  const [assignRoutineServerError, setAssignRoutineServerError] = useState<string | null>(null)
  const [isAssigningRoutine, setIsAssigningRoutine] = useState(false)
  const [assignRoutineToast, setAssignRoutineToast] = useState<string | null>(null)

  const resetAssignRoutineForm = () => {
    setAssignRoutineId('')
    setAssignRoutineDate(todayIso())
    setAssignRoutineServerError(null)
  }

  const handleAssignRoutineSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setAssignRoutineServerError(null)

    if (!assignRoutineId) {
      setAssignRoutineServerError('Selecciona una rutina.')
      return
    }
    if (!assignRoutineDate) {
      setAssignRoutineServerError('Selecciona una fecha de asignación.')
      return
    }

    const payload: RoutineAssignmentCreatePayload = {
      routine_id: Number(assignRoutineId),
      client_id: clientProfileId,
      assigned_date: assignRoutineDate,
    }

    setIsAssigningRoutine(true)
    try {
      const created = await apiFetch<ApiRoutineAssignment>('/routines/assignments', { method: 'POST', body: payload })
      setRoutineAssignments((prev) => [created, ...(prev ?? [])])
      setAssignRoutineToast('Rutina asignada correctamente.')
      setShowAssignRoutineForm(false)
      resetAssignRoutineForm()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setAssignRoutineServerError('No tienes permiso para asignar rutinas a este cliente.')
          return
        }
        setAssignRoutineServerError(err.message)
        return
      }
      setAssignRoutineServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsAssigningRoutine(false)
    }
  }

  if (isLoading) {
    return (
      <div className="card">
        <LoadingState label="Cargando cliente…" variant="skeleton" rows={6} />
      </div>
    )
  }

  if (errorMessage) {
    return <ErrorMessage message={errorMessage} />
  }

  if (notFound || !profile) {
    return (
      <div className="card">
        <p>No se encontró este cliente.</p>
        <Link to="/clientes" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Volver a clientes
        </Link>
      </div>
    )
  }

  // TODO(módulos Rutinas/Dietas/Progreso, todavía no construidos): el resto
  // de pestañas sigue usando los mismos datos mock de Entrega 1, indexados
  // por `clientProfileId` de ejemplo -- no corresponden necesariamente al
  // cliente real de esta pantalla. Se reemplazan por llamadas reales cuando
  // cada módulo exista. "Membresía", "Pagos" y "Rutina" (arriba) ya usan la
  // API real.
  const dietAssignments = getDietAssignmentsForClient(clientProfileId)
  const progress = getBodyProgressForClient(clientProfileId)
  const lastProgress = progress[progress.length - 1]

  return (
    <div className="client-detail">
      <div className="client-detail__header card">
        <div className="client-detail__avatar">
          {profile.full_name
            .split(' ')
            .slice(0, 2)
            .map((p) => p[0])
            .join('')}
        </div>
        <div className="client-detail__identity">
          <h2 className="section-title">{profile.full_name}</h2>
          <p className="client-detail__email">{profile.email}</p>
        </div>
        <div className="client-detail__header-meta">
          <div>
            <span className="eyebrow">Entrenador</span>
            <p>{profile.trainer_name ?? 'Sin asignar'}</p>
          </div>
          <div>
            <span className="eyebrow">Membresía</span>
            {membershipLoading ? (
              <p className="client-detail__meta-loading">Cargando…</p>
            ) : membership ? (
              <StatusPill status={getMembershipDisplayStatus(membership)} />
            ) : (
              <StatusPill status="sin_membresia" />
            )}
          </div>
        </div>
      </div>

      <div className="card client-detail__tabs">
        <Tabs items={TABS} activeId={activeTab} onChange={setActiveTab}>
          {activeTab === 'perfil' && (
            <dl className="client-detail__grid">
              <div>
                <dt>Teléfono</dt>
                <dd>{profile.phone ?? '—'}</dd>
              </div>
              <div>
                <dt>Fecha de nacimiento</dt>
                <dd>{profile.birth_date ?? '—'}</dd>
              </div>
              <div>
                <dt>Dirección</dt>
                <dd>{profile.address ?? '—'}</dd>
              </div>
              <div>
                <dt>Contacto de emergencia</dt>
                <dd>{profile.emergency_contact ?? '—'}</dd>
              </div>
              <div>
                <dt>Cliente desde</dt>
                <dd>{new Date(profile.created_at).toLocaleDateString('es-MX')}</dd>
              </div>
            </dl>
          )}

          {/* Conectado a la API real (RF004) -- ver useEffect de `membership`/
              `plans` arriba. */}
          {activeTab === 'membresia' && (
            <div className="client-detail__membership-tab">
              {assignToast && <Toast message={assignToast} onDismiss={() => setAssignToast(null)} />}

              {membershipLoading ? (
                <LoadingState label="Cargando membresía…" variant="skeleton" rows={3} />
              ) : membershipError ? (
                <ErrorMessage message={membershipError} />
              ) : membership && plan ? (
                <dl className="client-detail__grid">
                  <div>
                    <dt>Plan</dt>
                    <dd>{plan.name}</dd>
                  </div>
                  <div>
                    <dt>Precio</dt>
                    <dd>${Number(plan.price).toLocaleString('es-MX')} / mes</dd>
                  </div>
                  <div>
                    <dt>Vigencia</dt>
                    <dd>
                      {membership.start_date} — {membership.end_date}
                    </dd>
                  </div>
                  <div>
                    <dt>Estado</dt>
                    <dd>
                      <StatusPill status={getMembershipDisplayStatus(membership)} />
                    </dd>
                  </div>
                  {plan.benefits.length > 0 && (
                    <div className="client-detail__grid-full">
                      <dt>Beneficios</dt>
                      <dd>
                        <ul className="client-detail__benefits">
                          {plan.benefits.map((b) => (
                            <li key={b}>{b}</li>
                          ))}
                        </ul>
                      </dd>
                    </div>
                  )}
                </dl>
              ) : showAssignForm ? (
                <form className="client-detail__assign-form" onSubmit={handleAssignSubmit}>
                  {assignServerError && (
                    <ErrorMessage title="No se pudo asignar la membresía" message={assignServerError} />
                  )}

                  {plans.length === 0 ? (
                    <p className="client-detail__empty">
                      Todavía no hay planes registrados -- crea uno primero desde{' '}
                      <Link to="/membresias">Membresías</Link>.
                    </p>
                  ) : (
                    <div className="client-detail__assign-row">
                      <div className="client-detail__field">
                        <label className="field-label" htmlFor="assignPlan">
                          Plan
                        </label>
                        <select
                          id="assignPlan"
                          className="input"
                          value={assignPlanId}
                          onChange={(e) => setAssignPlanId(e.target.value)}
                          required
                        >
                          <option value="">Selecciona un plan</option>
                          {plans.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.name} — ${Number(p.price).toLocaleString('es-MX')}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="client-detail__field">
                        <label className="field-label" htmlFor="assignStart">
                          Fecha de inicio
                        </label>
                        <input
                          id="assignStart"
                          type="date"
                          className="input"
                          value={assignStartDate}
                          onChange={(e) => setAssignStartDate(e.target.value)}
                          required
                        />
                      </div>
                      <div className="client-detail__field">
                        <label className="field-label" htmlFor="assignEnd">
                          Fecha de vencimiento
                        </label>
                        <input
                          id="assignEnd"
                          type="date"
                          className="input"
                          value={computedEndDate}
                          readOnly
                          disabled
                        />
                      </div>
                    </div>
                  )}

                  <div className="client-detail__assign-actions">
                    <button type="button" className="btn btn-ghost" onClick={() => setShowAssignForm(false)}>
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={isAssigning || plans.length === 0}
                    >
                      {isAssigning ? 'Asignando…' : 'Asignar membresía'}
                    </button>
                  </div>
                </form>
              ) : (
                <EmptyState
                  title="Este cliente no tiene una membresía registrada"
                  description="Asigna un plan para activar su membresía."
                  actionLabel={isAdmin ? 'Asignar membresía' : undefined}
                  onAction={isAdmin ? () => setShowAssignForm(true) : undefined}
                />
              )}
            </div>
          )}

          {/* Conectado a la API real (RF005) -- comparte el fetch de membresía
              hecho arriba, no vuelve a llamar GET /memberships. */}
          {activeTab === 'pagos' && (
            <div className="client-detail__payments-tab">
              {paymentToast && <Toast message={paymentToast} onDismiss={() => setPaymentToast(null)} />}

              {membershipLoading ? (
                <LoadingState label="Cargando membresía…" variant="skeleton" rows={3} />
              ) : membershipError ? (
                <ErrorMessage message={membershipError} />
              ) : !membership ? (
                <EmptyState
                  title="Este cliente todavía no tiene una membresía"
                  description="Para registrar y consultar pagos primero necesita una membresía activa."
                  actionLabel="Ir a Membresía"
                  onAction={() => setActiveTab('membresia')}
                />
              ) : paymentsLoading ? (
                <LoadingState label="Cargando pagos…" variant="skeleton" rows={3} />
              ) : paymentsError ? (
                <ErrorMessage message={paymentsError} onRetry={() => loadPayments(membership.id)} />
              ) : (
                <>
                  {isAdmin && showPaymentForm && (
                    <form className="client-detail__payment-form" onSubmit={handleRegisterPayment}>
                      {paymentServerError && (
                        <ErrorMessage title="No se pudo registrar el pago" message={paymentServerError} />
                      )}

                      <div className="client-detail__payment-row">
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="paymentAmount">
                            Monto
                          </label>
                          <input
                            id="paymentAmount"
                            type="number"
                            min={0}
                            step="0.01"
                            className="input"
                            value={paymentAmount}
                            onChange={(e) => {
                              setPaymentAmount(e.target.value)
                              clearPaymentError('amount')
                            }}
                            placeholder="399.00"
                            data-invalid={Boolean(paymentErrors.amount)}
                            aria-invalid={Boolean(paymentErrors.amount)}
                            aria-describedby={paymentErrors.amount ? 'paymentAmount-error' : undefined}
                          />
                          {paymentErrors.amount && (
                            <p className="field-error" id="paymentAmount-error" role="alert">
                              {paymentErrors.amount}
                            </p>
                          )}
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="paymentMethodSelect">
                            Método
                          </label>
                          <select
                            id="paymentMethodSelect"
                            className="input"
                            value={paymentMethod}
                            onChange={(e) => setPaymentMethod(e.target.value as ApiPaymentMethod)}
                          >
                            {PAYMENT_METHODS.map((m) => (
                              <option key={m.value} value={m.value}>
                                {m.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="paymentDateInput">
                            Fecha de pago
                          </label>
                          <input
                            id="paymentDateInput"
                            type="date"
                            className="input"
                            value={paymentDate}
                            onChange={(e) => {
                              setPaymentDate(e.target.value)
                              clearPaymentError('paymentDate')
                            }}
                            data-invalid={Boolean(paymentErrors.paymentDate)}
                            aria-invalid={Boolean(paymentErrors.paymentDate)}
                            aria-describedby={paymentErrors.paymentDate ? 'paymentDate-error' : undefined}
                          />
                          {paymentErrors.paymentDate && (
                            <p className="field-error" id="paymentDate-error" role="alert">
                              {paymentErrors.paymentDate}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="client-detail__field">
                        <label className="field-label" htmlFor="paymentNotes">
                          Notas (opcional)
                        </label>
                        <input
                          id="paymentNotes"
                          className="input"
                          value={paymentNotes}
                          onChange={(e) => setPaymentNotes(e.target.value)}
                          placeholder="Ej. pago de reinscripción"
                        />
                      </div>

                      <div className="client-detail__assign-actions">
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => {
                            setShowPaymentForm(false)
                            resetPaymentForm()
                          }}
                        >
                          Cancelar
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={isRegisteringPayment}>
                          {isRegisteringPayment ? 'Registrando…' : 'Registrar pago'}
                        </button>
                      </div>
                    </form>
                  )}

                  {payments.length === 0 ? (
                    !showPaymentForm && (
                      <EmptyState
                        title="No hay pagos registrados"
                        description="Registra el primer pago para esta membresía."
                        actionLabel={isAdmin ? 'Registrar pago' : undefined}
                        onAction={isAdmin ? () => setShowPaymentForm(true) : undefined}
                      />
                    )
                  ) : (
                    <>
                      {isAdmin && !showPaymentForm && (
                        <div className="client-detail__payments-toolbar">
                          <button type="button" className="btn btn-ghost" onClick={() => setShowPaymentForm(true)}>
                            + Registrar pago
                          </button>
                        </div>
                      )}
                      <table className="client-detail__table">
                        <thead>
                          <tr>
                            <th>Fecha</th>
                            <th>Monto</th>
                            <th>Método</th>
                            <th>Estado</th>
                            <th>Notas</th>
                          </tr>
                        </thead>
                        <tbody>
                          {payments.map((p) => (
                            <tr key={p.id}>
                              <td>{p.payment_date}</td>
                              <td>${Number(p.amount).toLocaleString('es-MX')}</td>
                              <td className="client-detail__capitalize">{p.method}</td>
                              <td>
                                <StatusPill status={p.status} />
                              </td>
                              <td>{p.notes ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </>
                  )}
                </>
              )}
            </div>
          )}

          {/* Conectado a la API real (RF007/RF008) -- ver useEffect de
              `routineAssignments`/`routinesCatalog`/`exercisesCatalog` arriba. */}
          {activeTab === 'rutina' && (
            <div className="client-detail__routine-tab">
              {assignRoutineToast && (
                <Toast message={assignRoutineToast} onDismiss={() => setAssignRoutineToast(null)} />
              )}

              {routineAssignmentsLoading ? (
                <LoadingState label="Cargando rutinas…" variant="skeleton" rows={3} />
              ) : routineAssignmentsError ? (
                <ErrorMessage message={routineAssignmentsError} onRetry={loadRoutineAssignments} />
              ) : (
                <>
                  {isStaff && showAssignRoutineForm && (
                    <form className="client-detail__assign-form" onSubmit={handleAssignRoutineSubmit}>
                      {assignRoutineServerError && (
                        <ErrorMessage title="No se pudo asignar la rutina" message={assignRoutineServerError} />
                      )}

                      {routinesCatalog.length === 0 ? (
                        <p className="client-detail__empty">
                          Todavía no hay rutinas en el catálogo -- crea una primero desde{' '}
                          <Link to="/rutinas">Rutinas</Link>.
                        </p>
                      ) : (
                        <div className="client-detail__assign-row">
                          <div className="client-detail__field">
                            <label className="field-label" htmlFor="assignRoutineSelect">
                              Rutina
                            </label>
                            <select
                              id="assignRoutineSelect"
                              className="input"
                              value={assignRoutineId}
                              onChange={(e) => setAssignRoutineId(e.target.value)}
                              required
                            >
                              <option value="">Selecciona una rutina</option>
                              {routinesCatalog.map((r) => (
                                <option key={r.id} value={r.id}>
                                  {r.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="client-detail__field">
                            <label className="field-label" htmlFor="assignRoutineDate">
                              Fecha de asignación
                            </label>
                            <input
                              id="assignRoutineDate"
                              type="date"
                              className="input"
                              value={assignRoutineDate}
                              onChange={(e) => setAssignRoutineDate(e.target.value)}
                              required
                            />
                          </div>
                        </div>
                      )}

                      <div className="client-detail__assign-actions">
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => {
                            setShowAssignRoutineForm(false)
                            resetAssignRoutineForm()
                          }}
                        >
                          Cancelar
                        </button>
                        <button
                          type="submit"
                          className="btn btn-primary"
                          disabled={isAssigningRoutine || routinesCatalog.length === 0}
                        >
                          {isAssigningRoutine ? 'Asignando…' : 'Asignar rutina'}
                        </button>
                      </div>
                    </form>
                  )}

                  {!routineAssignments || routineAssignments.length === 0 ? (
                    !showAssignRoutineForm && (
                      <EmptyState
                        title="Este cliente no tiene rutinas asignadas"
                        description="Asigna una rutina del catálogo para que empiece a entrenar con un plan."
                        actionLabel={isStaff ? 'Asignar rutina' : undefined}
                        onAction={isStaff ? () => setShowAssignRoutineForm(true) : undefined}
                      />
                    )
                  ) : (
                    <div className="client-detail__stack">
                      {isStaff && !showAssignRoutineForm && (
                        <div className="client-detail__payments-toolbar">
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => setShowAssignRoutineForm(true)}
                          >
                            + Asignar rutina
                          </button>
                        </div>
                      )}
                      {routineAssignments.map((ra) => {
                        const routine = routineById.get(ra.routine_id)
                        const items = routineExercisesById.get(ra.routine_id)
                        return (
                          <div key={ra.id} className="client-detail__sub-card">
                            <div className="client-detail__sub-card-header">
                              <div>
                                <h3>{routine?.name ?? `Rutina #${ra.routine_id}`}</h3>
                                <p>{routine?.description}</p>
                              </div>
                              <StatusPill status={ra.status} />
                            </div>
                            <p className="client-detail__diet-meta">
                              Asignada el {ra.assigned_date}
                              {ra.notes ? ` · ${ra.notes}` : ''}
                            </p>
                            {items === undefined ? (
                              <LoadingState label="Cargando ejercicios…" variant="skeleton" rows={2} />
                            ) : items.length === 0 ? (
                              <p className="client-detail__empty">Esta rutina todavía no tiene ejercicios.</p>
                            ) : (
                              <table className="client-detail__table">
                                <thead>
                                  <tr>
                                    <th>Ejercicio</th>
                                    <th>Series</th>
                                    <th>Reps</th>
                                    <th>Descanso</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {items.map((it) => {
                                    const exercise = exerciseById.get(it.exercise_id)
                                    return (
                                      <tr key={it.id}>
                                        <td>{exercise?.name ?? `#${it.exercise_id}`}</td>
                                        <td>{it.sets}</td>
                                        <td>{it.reps}</td>
                                        <td>{it.rest_seconds != null ? `${it.rest_seconds}s` : '—'}</td>
                                      </tr>
                                    )
                                  })}
                                </tbody>
                              </table>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* TODO(módulo Dietas, todavía no construido): pestaña mock. */}
          {activeTab === 'dieta' &&
            (dietAssignments.length > 0 ? (
              <div className="client-detail__stack">
                {dietAssignments.map((da) => {
                  const plan = findDietPlan(da.diet_plan_id)
                  return (
                    <div key={da.id} className="client-detail__sub-card">
                      <div className="client-detail__sub-card-header">
                        <div>
                          <h3>{plan?.name}</h3>
                          <p>{plan?.description}</p>
                        </div>
                        <StatusPill status={da.status} />
                      </div>
                      <p className="client-detail__diet-meta">
                        {plan?.calories_target ? `${plan.calories_target} kcal / día` : 'Sin objetivo calórico definido'}{' '}
                        · asignado el {da.assigned_date}
                      </p>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="client-detail__empty">Este cliente no tiene un plan de dieta asignado.</p>
            ))}

          {/* TODO(módulo Progreso corporal, todavía no construido): pestaña mock. */}
          {activeTab === 'progreso' &&
            (progress.length > 0 ? (
              <div className="client-detail__progress">
                <div className="client-detail__progress-chart">
                  <ProgressChart points={progress.map((p) => ({ date: p.record_date, value: p.weight_kg }))} unit="kg" />
                </div>
                <table className="client-detail__table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Peso</th>
                      <th>% Grasa</th>
                      <th>Cintura</th>
                      <th>Notas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...progress].reverse().map((p) => (
                      <tr key={p.id}>
                        <td>{p.record_date}</td>
                        <td>{p.weight_kg} kg</td>
                        <td>{p.body_fat_pct ?? '—'}</td>
                        <td>{p.waist_cm ? `${p.waist_cm} cm` : '—'}</td>
                        <td>{p.notes ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {lastProgress && (
                  <p className="client-detail__footnote">
                    Estatura registrada: {lastProgress.height_cm} cm (campo `height_cm` vive en BodyProgress, no en el
                    perfil — ver DECISIONES.md).
                  </p>
                )}
              </div>
            ) : (
              <p className="client-detail__empty">No hay registros de progreso corporal.</p>
            ))}
        </Tabs>
      </div>
    </div>
  )
}
