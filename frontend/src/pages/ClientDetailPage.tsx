import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { ConfirmDialog } from '../components/ui/ConfirmDialog'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatusPill } from '../components/ui/StatusPill'
import { Tabs } from '../components/ui/Tabs'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type {
  ApiBodyProgress,
  ApiClientProfile,
  ApiDietAssignment,
  ApiDietPlan,
  ApiExercise,
  ApiMembership,
  ApiMembershipPlan,
  ApiMembershipService,
  ApiMembershipServiceLimited,
  ApiPayment,
  ApiPaymentMethod,
  ApiPlanChangePreview,
  ApiRoutine,
  ApiRoutineAssignment,
  ApiRoutineExercise,
  ApiService,
  BodyProgressCreatePayload,
  DietAssignmentCreatePayload,
  MembershipCreatePayload,
  MembershipServiceCreatePayload,
  PaymentCreatePayload,
  PaymentItemCreatePayload,
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

const TAB_IDS = TABS.map((t) => t.id)

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [searchParams] = useSearchParams()
  // `?tab=pagos` -- usado por la acción "Cobrar" del tablero de membresías
  // activas para llegar directo a la pestaña de Pagos, en vez de dejar al
  // admin reabrir "Perfil" y volver a hacer clic.
  const initialTab = searchParams.get('tab')
  const [activeTab, setActiveTab] = useState(
    initialTab && TAB_IDS.includes(initialTab) ? initialTab : 'perfil',
  )
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const isAdmin = user?.role === 'admin'
  const clientProfileId = Number(id)

  // --- Eliminar cliente (RF003, solo admin) ---------------------------------
  // `DeleteClientUseCase` hace un hard delete del `ClientProfile` -- sus
  // membresías/pagos/rutinas/dietas/progreso caen en cascada (ver FKs en
  // `infrastructure/db/models/`). Irreversible, por eso pasa por
  // `ConfirmDialog` (ver docstring del componente: existía desde el
  // rediseño de UX pero ninguna pantalla lo conectaba todavía).
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const handleDeleteClient = async () => {
    setDeleteError(null)
    setIsDeleting(true)
    try {
      await apiFetch<void>(`/clients/${clientProfileId}`, { method: 'DELETE' })
      navigate('/clientes', {
        replace: true,
        state: { toast: `${profile?.full_name ?? 'El cliente'} fue eliminado correctamente.` },
      })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        setDeleteError(
          err.status === 403
            ? 'No tienes permiso para eliminar este cliente.'
            : err.message,
        )
      } else {
        setDeleteError('Ocurrió un error inesperado. Intenta de nuevo.')
      }
      setShowDeleteConfirm(false)
    } finally {
      setIsDeleting(false)
    }
  }

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

  const loadMembership = () => {
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
  }

  useEffect(() => {
    loadMembership()
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

  // --- Cambiar plan (amplía RF004/RF005 de nuevo) --------------------------
  // Flujo en dos pasos sobre el MISMO endpoint-pareja: "Ver resumen" pide
  // `/change-plan/preview` (no persiste nada) y guarda el resultado en
  // `changePlanPreview`; mientras ese estado exista, el panel muestra el
  // resumen en vez del selector. "Confirmar cambio" reenvía el mismo
  // `new_plan_id` a `/change-plan` (ahí sí persiste) -- nunca se arma un
  // segundo cálculo del lado del cliente, siempre se confía en lo que
  // devolvió el backend.
  const [showChangePlanForm, setShowChangePlanForm] = useState(false)
  const [changePlanTargetId, setChangePlanTargetId] = useState('')
  const [changePlanNotes, setChangePlanNotes] = useState('')
  const [changePlanPreview, setChangePlanPreview] = useState<ApiPlanChangePreview | null>(null)
  const [isPreviewingPlanChange, setIsPreviewingPlanChange] = useState(false)
  const [isConfirmingPlanChange, setIsConfirmingPlanChange] = useState(false)
  const [changePlanError, setChangePlanError] = useState<string | null>(null)
  const [changePlanToast, setChangePlanToast] = useState<string | null>(null)

  const changeablePlans = plans.filter((p) => p.is_active && p.id !== membership?.plan_id)

  const resetChangePlanFlow = () => {
    setShowChangePlanForm(false)
    setChangePlanTargetId('')
    setChangePlanNotes('')
    setChangePlanPreview(null)
    setChangePlanError(null)
  }

  const handleChangePlanApiError = (err: unknown) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      setChangePlanError(err.message)
      return
    }
    setChangePlanError('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  const handlePreviewChangePlan = async (event: FormEvent) => {
    event.preventDefault()
    if (!membership || !changePlanTargetId) {
      setChangePlanError('Selecciona un plan.')
      return
    }
    setChangePlanError(null)
    setIsPreviewingPlanChange(true)
    try {
      const preview = await apiFetch<ApiPlanChangePreview>(`/memberships/${membership.id}/change-plan/preview`, {
        method: 'POST',
        body: { new_plan_id: Number(changePlanTargetId) },
      })
      setChangePlanPreview(preview)
    } catch (err) {
      handleChangePlanApiError(err)
    } finally {
      setIsPreviewingPlanChange(false)
    }
  }

  const handleConfirmChangePlan = async () => {
    if (!membership || !changePlanPreview) return
    setChangePlanError(null)
    setIsConfirmingPlanChange(true)
    try {
      await apiFetch<ApiPlanChangePreview>(`/memberships/${membership.id}/change-plan`, {
        method: 'POST',
        body: { new_plan_id: changePlanPreview.new_plan_id, notes: changePlanNotes.trim() || null },
      })
      setChangePlanToast(`Plan cambiado a "${changePlanPreview.new_plan_name}".`)
      resetChangePlanFlow()
      loadMembership()
    } catch (err) {
      handleChangePlanApiError(err)
    } finally {
      setIsConfirmingPlanChange(false)
    }
  }

  // --- Servicios extra (Entrega 3, Fase 2 -- amplía RF004/RF005) ----------
  // Dos listas distintas: qué incluye el PLAN (plan_services, catálogo) vs.
  // qué CONTRATÓ el cliente aparte (membership_services, con precio
  // congelado). `GET /memberships/{id}/services` ya recorta `price_at_purchase`
  // del lado del backend para `entrenador` -- se tipa como el "or" de ambas
  // formas en vez de asumir cuál llega.
  const [includedServices, setIncludedServices] = useState<ApiService[]>([])
  const [contractedServices, setContractedServices] = useState<
    (ApiMembershipService | ApiMembershipServiceLimited)[]
  >([])
  const [servicesLoading, setServicesLoading] = useState(false)
  const [allServices, setAllServices] = useState<ApiService[]>([])

  useEffect(() => {
    apiFetch<ApiService[]>('/services')
      .then(setAllServices)
      .catch(() => setAllServices([]))
  }, [])

  useEffect(() => {
    if (!membership || !plan) {
      setIncludedServices([])
      setContractedServices([])
      return
    }
    setServicesLoading(true)
    Promise.all([
      apiFetch<ApiService[]>(`/membership-plans/${plan.id}/services`),
      apiFetch<(ApiMembershipService | ApiMembershipServiceLimited)[]>(`/memberships/${membership.id}/services`),
    ])
      .then(([included, contracted]) => {
        setIncludedServices(included)
        setContractedServices(contracted)
      })
      .catch(() => {
        setIncludedServices([])
        setContractedServices([])
      })
      .finally(() => setServicesLoading(false))
  }, [membership?.id, plan?.id])

  // Solo los extras VIGENTES bloquean una nueva contratación o se ofrecen
  // para cobrar -- uno cancelado (manualmente o por un cambio de plan, ver
  // flujo "Cambiar plan" más abajo) no debe impedir recontratar ese mismo
  // servicio después, ni seguir apareciendo como cobrable.
  const activeContractedServices = useMemo(
    () => contractedServices.filter((ms) => ms.status === 'activa'),
    [contractedServices],
  )
  const includedServiceIds = useMemo(() => new Set(includedServices.map((s) => s.id)), [includedServices])
  const contractedServiceIds = useMemo(
    () => new Set(activeContractedServices.map((ms) => ms.service_id)),
    [activeContractedServices],
  )
  const contractableServices = allServices.filter(
    (s) => s.is_active && !includedServiceIds.has(s.id) && !contractedServiceIds.has(s.id),
  )

  // --- Contratar un servicio extra (solo admin) ----------------------------
  const [showContractForm, setShowContractForm] = useState(false)
  const [contractServiceId, setContractServiceId] = useState('')
  const [contractServerError, setContractServerError] = useState<string | null>(null)
  const [isContracting, setIsContracting] = useState(false)
  const [contractToast, setContractToast] = useState<string | null>(null)

  const handleContractService = async (event: FormEvent) => {
    event.preventDefault()
    setContractServerError(null)
    if (!membership || !contractServiceId) {
      setContractServerError('Selecciona un servicio.')
      return
    }

    const payload: MembershipServiceCreatePayload = { service_id: Number(contractServiceId) }

    setIsContracting(true)
    try {
      const created = await apiFetch<ApiMembershipService>(`/memberships/${membership.id}/services`, {
        method: 'POST',
        body: payload,
      })
      setContractedServices((prev) => [...prev, created])
      const service = allServices.find((s) => s.id === created.service_id)
      setContractToast(`"${service?.name ?? 'Servicio'}" contratado correctamente.`)
      setShowContractForm(false)
      setContractServiceId('')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        setContractServerError(
          err.status === 403 ? 'No tienes permiso para contratar servicios para este cliente.' : err.message,
        )
      } else {
        setContractServerError('Ocurrió un error inesperado. Intenta de nuevo.')
      }
    } finally {
      setIsContracting(false)
    }
  }

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

  // Desglose opcional (Entrega 3, Fase 2): si el admin marca el plan y/o
  // algún extra contratado, el monto se calcula solo a partir de ahí y el
  // pago se registra con `items`. Sin nada marcado, el formulario se
  // comporta exactamente como en Entrega 2 (monto libre, sin desglose).
  const [breakdownPlanChecked, setBreakdownPlanChecked] = useState(false)
  const [breakdownServiceIds, setBreakdownServiceIds] = useState<Set<number>>(new Set())

  const breakdownActive = breakdownPlanChecked || breakdownServiceIds.size > 0
  const breakdownTotal =
    (breakdownPlanChecked && plan ? Number(plan.price) : 0) +
    contractedServices
      .filter((ms) => breakdownServiceIds.has(ms.id))
      .reduce((sum, ms) => sum + ('price_at_purchase' in ms ? Number(ms.price_at_purchase) : 0), 0)

  const toggleBreakdownService = (membershipServiceId: number) => {
    setBreakdownServiceIds((prev) => {
      const next = new Set(prev)
      if (next.has(membershipServiceId)) next.delete(membershipServiceId)
      else next.add(membershipServiceId)
      return next
    })
  }

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
    setBreakdownPlanChecked(false)
    setBreakdownServiceIds(new Set())
  }

  const handleRegisterPayment = async (event: FormEvent) => {
    event.preventDefault()
    setPaymentServerError(null)
    if (!membership) return

    const amountValue = breakdownActive ? breakdownTotal : Number(paymentAmount)

    const nextErrors: PaymentFormErrors = {}
    if (!amountValue || Number.isNaN(amountValue) || amountValue <= 0) {
      nextErrors.amount = breakdownActive
        ? 'El desglose seleccionado suma $0 -- marca al menos un concepto con precio.'
        : 'Ingresa un monto mayor a 0.'
    }
    if (!paymentDate) nextErrors.paymentDate = 'Selecciona una fecha de pago.'
    if (Object.keys(nextErrors).length > 0) {
      setPaymentErrors(nextErrors)
      return
    }

    const items: PaymentItemCreatePayload[] = []
    if (breakdownActive) {
      if (breakdownPlanChecked && plan) {
        items.push({ concept: 'plan', amount: Number(plan.price) })
      }
      contractedServices
        .filter((ms) => breakdownServiceIds.has(ms.id))
        .forEach((ms) => {
          if ('price_at_purchase' in ms) {
            items.push({ concept: 'servicio', amount: Number(ms.price_at_purchase), service_id: ms.service_id })
          }
        })
    }

    const payload: PaymentCreatePayload = {
      membership_id: membership.id,
      amount: amountValue,
      payment_date: paymentDate,
      method: paymentMethod,
      notes: paymentNotes.trim() || null,
      items,
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

  // --- Dieta (RF009, módulo Dietas) ----------------------------------------
  // Mismo patrón que "Rutina" arriba: historial real vía
  // `GET /diets/assignments/clients/{id}` (ownership por dato ya resuelto en
  // el backend). Un `DietPlan` no tiene sub-items (a diferencia de
  // `Routine`/`RoutineExercise`), así que no hace falta cargar nada por
  // asignación.
  const [dietAssignments, setDietAssignments] = useState<ApiDietAssignment[] | null>(null)
  const [dietAssignmentsLoading, setDietAssignmentsLoading] = useState(true)
  const [dietAssignmentsError, setDietAssignmentsError] = useState<string | null>(null)

  const loadDietAssignments = () => {
    setDietAssignmentsLoading(true)
    setDietAssignmentsError(null)
    apiFetch<ApiDietAssignment[]>(`/diets/assignments/clients/${clientProfileId}`)
      .then(setDietAssignments)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setDietAssignmentsError('No tienes permiso para ver las dietas de este cliente.')
            return
          }
          setDietAssignmentsError(err.message)
          return
        }
        setDietAssignmentsError('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setDietAssignmentsLoading(false))
  }

  useEffect(() => {
    loadDietAssignments()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientProfileId])

  // Catálogo de planes de dieta (para el selector del formulario de
  // asignación) -- se carga una sola vez, mismo criterio que el catálogo de
  // rutinas arriba.
  const [dietPlansCatalog, setDietPlansCatalog] = useState<ApiDietPlan[]>([])

  useEffect(() => {
    apiFetch<ApiDietPlan[]>('/diets/plans').then(setDietPlansCatalog).catch(() => setDietPlansCatalog([]))
  }, [])

  const dietPlanById = useMemo(() => {
    const map = new Map<number, ApiDietPlan>()
    dietPlansCatalog.forEach((p) => map.set(p.id, p))
    return map
  }, [dietPlansCatalog])

  // --- Asignar dieta (admin/entrenador dueño del cliente) -------------------
  const [showAssignDietForm, setShowAssignDietForm] = useState(false)
  const [assignDietPlanId, setAssignDietPlanId] = useState('')
  const [assignDietDate, setAssignDietDate] = useState(todayIso)
  const [assignDietServerError, setAssignDietServerError] = useState<string | null>(null)
  const [isAssigningDiet, setIsAssigningDiet] = useState(false)
  const [assignDietToast, setAssignDietToast] = useState<string | null>(null)

  const resetAssignDietForm = () => {
    setAssignDietPlanId('')
    setAssignDietDate(todayIso())
    setAssignDietServerError(null)
  }

  const handleAssignDietSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setAssignDietServerError(null)

    if (!assignDietPlanId) {
      setAssignDietServerError('Selecciona un plan de dieta.')
      return
    }
    if (!assignDietDate) {
      setAssignDietServerError('Selecciona una fecha de asignación.')
      return
    }

    const payload: DietAssignmentCreatePayload = {
      diet_plan_id: Number(assignDietPlanId),
      client_id: clientProfileId,
      assigned_date: assignDietDate,
    }

    setIsAssigningDiet(true)
    try {
      const created = await apiFetch<ApiDietAssignment>('/diets/assignments', { method: 'POST', body: payload })
      setDietAssignments((prev) => [created, ...(prev ?? [])])
      setAssignDietToast('Dieta asignada correctamente.')
      setShowAssignDietForm(false)
      resetAssignDietForm()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setAssignDietServerError('No tienes permiso para asignar dietas a este cliente.')
          return
        }
        setAssignDietServerError(err.message)
        return
      }
      setAssignDietServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsAssigningDiet(false)
    }
  }

  // --- Progreso corporal (RF010/RF011, módulo Progreso Corporal) ----------
  // Mismo patrón que "Rutina"/"Dieta" arriba: historial real vía
  // `GET /progress/clients/{id}` (ownership por dato ya resuelto en el
  // backend). Si es `entrenador` o `admin`, puede registrar un nuevo
  // registro de progreso para este cliente.
  const [progressRecords, setProgressRecords] = useState<ApiBodyProgress[] | null>(null)
  const [progressLoading, setProgressLoading] = useState(true)
  const [progressError, setProgressError] = useState<string | null>(null)

  const loadProgress = () => {
    setProgressLoading(true)
    setProgressError(null)
    apiFetch<ApiBodyProgress[]>(`/progress/clients/${clientProfileId}`)
      .then(setProgressRecords)
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          if (err.isUnauthorized) {
            logout()
            navigate('/login', { replace: true })
            return
          }
          if (err.status === 403) {
            setProgressError('No tienes permiso para ver el progreso de este cliente.')
            return
          }
          setProgressError(err.message)
          return
        }
        setProgressError('Ocurrió un error inesperado. Intenta de nuevo.')
      })
      .finally(() => setProgressLoading(false))
  }

  useEffect(() => {
    loadProgress()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientProfileId])

  const [showProgressForm, setShowProgressForm] = useState(false)
  const [progressDate, setProgressDate] = useState(todayIso)
  const [progressWeightKg, setProgressWeightKg] = useState('')
  const [progressHeightCm, setProgressHeightCm] = useState('')
  const [progressBodyFatPct, setProgressBodyFatPct] = useState('')
  const [progressWaistCm, setProgressWaistCm] = useState('')
  const [progressNotes, setProgressNotes] = useState('')
  const [progressServerError, setProgressServerError] = useState<string | null>(null)
  const [isSubmittingProgress, setIsSubmittingProgress] = useState(false)
  const [progressToast, setProgressToast] = useState<string | null>(null)

  const resetProgressForm = () => {
    setProgressDate(todayIso())
    setProgressWeightKg('')
    setProgressHeightCm('')
    setProgressBodyFatPct('')
    setProgressWaistCm('')
    setProgressNotes('')
    setProgressServerError(null)
  }

  const handleRegisterProgressSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setProgressServerError(null)

    const weightValue = Number(progressWeightKg)
    if (!progressWeightKg || Number.isNaN(weightValue) || weightValue <= 0) {
      setProgressServerError('Ingresa un peso válido (mayor a 0).')
      return
    }
    if (!progressDate) {
      setProgressServerError('Selecciona la fecha del registro.')
      return
    }

    const payload: BodyProgressCreatePayload = {
      client_id: clientProfileId,
      record_date: progressDate,
      weight_kg: weightValue,
      height_cm: progressHeightCm.trim() ? Number(progressHeightCm) : null,
      body_fat_pct: progressBodyFatPct.trim() ? Number(progressBodyFatPct) : null,
      waist_cm: progressWaistCm.trim() ? Number(progressWaistCm) : null,
      notes: progressNotes.trim() || null,
    }

    setIsSubmittingProgress(true)
    try {
      const created = await apiFetch<ApiBodyProgress>('/progress', { method: 'POST', body: payload })
      setProgressRecords((prev) => [...(prev ?? []), created].sort((a, b) => a.record_date.localeCompare(b.record_date)))
      setProgressToast('Registro de progreso guardado.')
      setShowProgressForm(false)
      resetProgressForm()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.isUnauthorized) {
          logout()
          navigate('/login', { replace: true })
          return
        }
        if (err.status === 403) {
          setProgressServerError('No tienes permiso para registrar progreso de este cliente.')
          return
        }
        setProgressServerError(err.message)
        return
      }
      setProgressServerError('Ocurrió un error inesperado. Intenta de nuevo.')
    } finally {
      setIsSubmittingProgress(false)
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
        {isAdmin && (
          <button
            type="button"
            className="btn btn-ghost client-detail__delete-btn"
            onClick={() => setShowDeleteConfirm(true)}
          >
            Eliminar cliente
          </button>
        )}
      </div>

      {deleteError && <Toast message={deleteError} tone="danger" onDismiss={() => setDeleteError(null)} />}

      <ConfirmDialog
        open={showDeleteConfirm}
        title={`¿Eliminar a ${profile.full_name}?`}
        description={
          // CU04 (flujo alterno): una advertencia más específica cuando hay
          // membresía activa o pagos registrados -- es exactamente el dato
          // que se pierde (CASCADE), no solo "el perfil".
          membership && getMembershipDisplayStatus(membership) === 'activa'
            ? `Este cliente tiene una membresía activa (${plan?.name ?? 'plan'}) y ${payments.length} pago${payments.length === 1 ? '' : 's'} registrado${payments.length === 1 ? '' : 's'}. Al eliminarlo se borran también su membresía, pagos, extras, rutinas, dietas y progreso. Esta acción no se puede deshacer.`
            : payments.length > 0
              ? `Este cliente tiene ${payments.length} pago${payments.length === 1 ? '' : 's'} registrado${payments.length === 1 ? '' : 's'}. Se borra su perfil junto con sus membresías, pagos, rutinas, dietas y progreso registrados. Esta acción no se puede deshacer.`
              : 'Se borra su perfil junto con sus membresías, pagos, rutinas, dietas y progreso registrados. Esta acción no se puede deshacer.'
        }
        confirmLabel={isDeleting ? 'Eliminando…' : 'Eliminar'}
        onConfirm={handleDeleteClient}
        onCancel={() => setShowDeleteConfirm(false)}
      />

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
                <>
                  {changePlanToast && <Toast message={changePlanToast} onDismiss={() => setChangePlanToast(null)} />}

                  {isAdmin && (
                    <div className="client-detail__membership-header">
                      <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={() => {
                          if (showChangePlanForm) {
                            resetChangePlanFlow()
                          } else {
                            setShowChangePlanForm(true)
                          }
                        }}
                      >
                        {showChangePlanForm ? 'Cancelar cambio de plan' : 'Cambiar plan'}
                      </button>
                    </div>
                  )}

                  {isAdmin && showChangePlanForm && !changePlanPreview && (
                    <form className="card client-detail__change-plan-form" onSubmit={handlePreviewChangePlan}>
                      {changePlanError && (
                        <ErrorMessage title="No se pudo calcular el cambio" message={changePlanError} />
                      )}
                      {changeablePlans.length === 0 ? (
                        <p className="client-detail__empty">
                          No hay otro plan activo disponible para cambiarse.
                        </p>
                      ) : (
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="changePlanTarget">
                            Nuevo plan
                          </label>
                          <select
                            id="changePlanTarget"
                            className="input"
                            value={changePlanTargetId}
                            onChange={(e) => setChangePlanTargetId(e.target.value)}
                          >
                            <option value="">Selecciona un plan</option>
                            {changeablePlans.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name} — ${Number(p.price).toLocaleString('es-MX')}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      <div className="client-detail__assign-actions">
                        <button
                          type="submit"
                          className="btn btn-primary"
                          disabled={isPreviewingPlanChange || changeablePlans.length === 0}
                        >
                          {isPreviewingPlanChange ? 'Calculando…' : 'Ver resumen'}
                        </button>
                      </div>
                    </form>
                  )}

                  {isAdmin && changePlanPreview && (
                    <div className="card client-detail__change-plan-summary">
                      {changePlanError && (
                        <ErrorMessage title="No se pudo confirmar el cambio" message={changePlanError} />
                      )}
                      <p className="client-detail__change-plan-headline">
                        {changePlanPreview.old_plan_name} (${Number(changePlanPreview.old_plan_price).toLocaleString('es-MX')})
                        {' → '}
                        {changePlanPreview.new_plan_name} (${Number(changePlanPreview.new_plan_price).toLocaleString('es-MX')})
                        <span className="client-detail__change-plan-diff">
                          {Number(changePlanPreview.price_difference) >= 0 ? ' +' : ' '}
                          ${Number(changePlanPreview.price_difference).toLocaleString('es-MX')} / mes
                        </span>
                      </p>

                      {changePlanPreview.cancelled_extras.length > 0 && (
                        <div className="client-detail__change-plan-block">
                          <span className="field-label">
                            Se cancelarán por estar incluidos en el nuevo plan
                          </span>
                          <ul className="client-detail__services-list">
                            {changePlanPreview.cancelled_extras.map((e) => (
                              <li key={e.membership_service_id}>
                                {e.service_name} — ya pagado: ${Number(e.price_at_purchase).toLocaleString('es-MX')}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {changePlanPreview.kept_extras.length > 0 && (
                        <div className="client-detail__change-plan-block">
                          <span className="field-label">Se conservan</span>
                          <ul className="client-detail__services-list">
                            {changePlanPreview.kept_extras.map((e) => (
                              <li key={e.membership_service_id}>{e.service_name}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {changePlanPreview.newly_contractable_services.length > 0 && (
                        <div className="client-detail__change-plan-block">
                          <span className="field-label">
                            Dejarán de estar incluidos (se podrán contratar como extra)
                          </span>
                          <ul className="client-detail__services-list">
                            {changePlanPreview.newly_contractable_services.map((s) => (
                              <li key={s.service_id}>
                                {s.service_name} — ${Number(s.price).toLocaleString('es-MX')}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      <div className="client-detail__field">
                        <label className="field-label" htmlFor="changePlanNotes">
                          Notas (acuerdo de reembolso o saldo a favor, opcional)
                        </label>
                        <textarea
                          id="changePlanNotes"
                          className="input"
                          rows={2}
                          value={changePlanNotes}
                          onChange={(e) => setChangePlanNotes(e.target.value)}
                          placeholder="Ej. se acuerda saldo a favor de $450 para el próximo pago"
                        />
                      </div>

                      <div className="client-detail__assign-actions">
                        <button type="button" className="btn btn-ghost" onClick={resetChangePlanFlow}>
                          Cancelar
                        </button>
                        <button
                          type="button"
                          className="btn btn-primary"
                          onClick={handleConfirmChangePlan}
                          disabled={isConfirmingPlanChange}
                        >
                          {isConfirmingPlanChange ? 'Confirmando…' : 'Confirmar cambio'}
                        </button>
                      </div>
                    </div>
                  )}

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

                  {/* Entrega 3, Fase 2 -- amplía RF004/RF005: qué incluye el
                      plan (catálogo) vs. qué contrató el cliente aparte
                      (precio congelado). */}
                  <div className="client-detail__services-section">
                    {contractToast && <Toast message={contractToast} onDismiss={() => setContractToast(null)} />}

                    {includedServices.length > 0 && (
                      <div className="client-detail__services-block">
                        <span className="field-label">Servicios incluidos en el plan</span>
                        <ul className="client-detail__services-list">
                          {includedServices.map((s) => (
                            <li key={s.id}>{s.name}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="client-detail__services-block">
                      <div className="client-detail__services-block-header">
                        <span className="field-label">Extras contratados</span>
                        {isAdmin && (
                          <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => setShowContractForm((prev) => !prev)}
                          >
                            {showContractForm ? 'Cancelar' : '+ Contratar extra'}
                          </button>
                        )}
                      </div>

                      {isAdmin && showContractForm && (
                        <form className="client-detail__assign-form" onSubmit={handleContractService}>
                          {contractServerError && (
                            <ErrorMessage title="No se pudo contratar el servicio" message={contractServerError} />
                          )}
                          {contractableServices.length === 0 ? (
                            <p className="client-detail__empty">
                              No hay servicios disponibles para contratar aparte -- ya están todos incluidos en el
                              plan, ya contratados, o inactivos.
                            </p>
                          ) : (
                            <div className="client-detail__field">
                              <label className="field-label" htmlFor="contractServiceId">
                                Servicio
                              </label>
                              <select
                                id="contractServiceId"
                                className="input"
                                value={contractServiceId}
                                onChange={(e) => setContractServiceId(e.target.value)}
                              >
                                <option value="">Selecciona un servicio</option>
                                {contractableServices.map((s) => (
                                  <option key={s.id} value={s.id}>
                                    {s.name} — ${Number(s.price).toLocaleString('es-MX')}
                                  </option>
                                ))}
                              </select>
                            </div>
                          )}
                          <div className="client-detail__assign-actions">
                            <button
                              type="submit"
                              className="btn btn-primary"
                              disabled={isContracting || contractableServices.length === 0}
                            >
                              {isContracting ? 'Contratando…' : 'Contratar'}
                            </button>
                          </div>
                        </form>
                      )}

                      {servicesLoading ? (
                        <LoadingState label="Cargando extras…" variant="skeleton" rows={2} />
                      ) : contractedServices.length === 0 ? (
                        <p className="client-detail__empty">Sin extras contratados.</p>
                      ) : (
                        <table className="client-detail__table">
                          <thead>
                            <tr>
                              <th>Servicio</th>
                              {isAdmin && <th>Precio</th>}
                              <th>Vigencia</th>
                              <th>Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {contractedServices.map((ms) => {
                              const service = allServices.find((s) => s.id === ms.service_id)
                              return (
                                <tr key={ms.id}>
                                  <td>{service?.name ?? `Servicio #${ms.service_id}`}</td>
                                  {isAdmin && (
                                    <td>
                                      {'price_at_purchase' in ms
                                        ? `$${Number(ms.price_at_purchase).toLocaleString('es-MX')}`
                                        : '—'}
                                    </td>
                                  )}
                                  <td>
                                    {ms.start_date} — {ms.end_date}
                                  </td>
                                  <td>
                                    <StatusPill status={ms.status} />
                                  </td>
                                </tr>
                              )
                            })}
                          </tbody>
                        </table>
                      )}
                    </div>
                  </div>
                </>
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

                      {(plan || contractedServices.length > 0) && (
                        <div className="client-detail__breakdown">
                          <span className="field-label">Desglose (opcional) -- marca para calcular el monto</span>
                          <ul className="client-detail__breakdown-list">
                            {plan && (
                              <li>
                                <label>
                                  <input
                                    type="checkbox"
                                    checked={breakdownPlanChecked}
                                    onChange={(e) => setBreakdownPlanChecked(e.target.checked)}
                                  />
                                  Plan {plan.name} — ${Number(plan.price).toLocaleString('es-MX')}
                                </label>
                              </li>
                            )}
                            {activeContractedServices.map((ms) => {
                              const service = allServices.find((s) => s.id === ms.service_id)
                              const price = 'price_at_purchase' in ms ? Number(ms.price_at_purchase) : null
                              if (price == null) return null
                              return (
                                <li key={ms.id}>
                                  <label>
                                    <input
                                      type="checkbox"
                                      checked={breakdownServiceIds.has(ms.id)}
                                      onChange={() => toggleBreakdownService(ms.id)}
                                    />
                                    {service?.name ?? `Servicio #${ms.service_id}`} — ${price.toLocaleString('es-MX')}
                                  </label>
                                </li>
                              )
                            })}
                          </ul>
                        </div>
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
                            value={breakdownActive ? breakdownTotal.toFixed(2) : paymentAmount}
                            disabled={breakdownActive}
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
                            <th>Desglose</th>
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
                              <td>
                                {p.items.length === 0
                                  ? '—'
                                  : p.items
                                      .map((item) =>
                                        item.concept === 'plan'
                                          ? `Plan ($${Number(item.amount).toLocaleString('es-MX')})`
                                          : `${allServices.find((s) => s.id === item.service_id)?.name ?? 'Servicio'} ($${Number(item.amount).toLocaleString('es-MX')})`,
                                      )
                                      .join(' + ')}
                              </td>
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

          {/* Conectado a la API real (RF009) -- ver useEffect de
              `dietAssignments`/`dietPlansCatalog` arriba. */}
          {activeTab === 'dieta' && (
            <div className="client-detail__routine-tab">
              {assignDietToast && (
                <Toast message={assignDietToast} onDismiss={() => setAssignDietToast(null)} />
              )}

              {dietAssignmentsLoading ? (
                <LoadingState label="Cargando dietas…" variant="skeleton" rows={3} />
              ) : dietAssignmentsError ? (
                <ErrorMessage message={dietAssignmentsError} onRetry={loadDietAssignments} />
              ) : (
                <>
                  {isStaff && showAssignDietForm && (
                    <form className="client-detail__assign-form" onSubmit={handleAssignDietSubmit}>
                      {assignDietServerError && (
                        <ErrorMessage title="No se pudo asignar la dieta" message={assignDietServerError} />
                      )}

                      {dietPlansCatalog.length === 0 ? (
                        <p className="client-detail__empty">
                          Todavía no hay planes de dieta en el catálogo -- crea uno primero desde{' '}
                          <Link to="/dietas">Dietas</Link>.
                        </p>
                      ) : (
                        <div className="client-detail__assign-row">
                          <div className="client-detail__field">
                            <label className="field-label" htmlFor="assignDietSelect">
                              Plan de dieta
                            </label>
                            <select
                              id="assignDietSelect"
                              className="input"
                              value={assignDietPlanId}
                              onChange={(e) => setAssignDietPlanId(e.target.value)}
                              required
                            >
                              <option value="">Selecciona un plan</option>
                              {dietPlansCatalog.map((p) => (
                                <option key={p.id} value={p.id}>
                                  {p.name}
                                </option>
                              ))}
                            </select>
                          </div>
                          <div className="client-detail__field">
                            <label className="field-label" htmlFor="assignDietDate">
                              Fecha de asignación
                            </label>
                            <input
                              id="assignDietDate"
                              type="date"
                              className="input"
                              value={assignDietDate}
                              onChange={(e) => setAssignDietDate(e.target.value)}
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
                            setShowAssignDietForm(false)
                            resetAssignDietForm()
                          }}
                        >
                          Cancelar
                        </button>
                        <button
                          type="submit"
                          className="btn btn-primary"
                          disabled={isAssigningDiet || dietPlansCatalog.length === 0}
                        >
                          {isAssigningDiet ? 'Asignando…' : 'Asignar dieta'}
                        </button>
                      </div>
                    </form>
                  )}

                  {!dietAssignments || dietAssignments.length === 0 ? (
                    !showAssignDietForm && (
                      <EmptyState
                        title="Este cliente no tiene un plan de dieta asignado"
                        description="Asigna un plan del catálogo para que empiece a seguirlo."
                        actionLabel={isStaff ? 'Asignar dieta' : undefined}
                        onAction={isStaff ? () => setShowAssignDietForm(true) : undefined}
                      />
                    )
                  ) : (
                    <div className="client-detail__stack">
                      {isStaff && !showAssignDietForm && (
                        <div className="client-detail__payments-toolbar">
                          <button type="button" className="btn btn-ghost" onClick={() => setShowAssignDietForm(true)}>
                            + Asignar dieta
                          </button>
                        </div>
                      )}
                      {dietAssignments.map((da) => {
                        const plan = dietPlanById.get(da.diet_plan_id)
                        return (
                          <div key={da.id} className="client-detail__sub-card">
                            <div className="client-detail__sub-card-header">
                              <div>
                                <h3>{plan?.name ?? `Plan #${da.diet_plan_id}`}</h3>
                                <p>{plan?.description}</p>
                              </div>
                              <StatusPill status={da.status} />
                            </div>
                            <p className="client-detail__diet-meta">
                              {plan?.calories_target ? `${plan.calories_target} kcal / día` : 'Sin objetivo calórico definido'}
                              {' · '}asignado el {da.assigned_date}
                              {da.notes ? ` · ${da.notes}` : ''}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {activeTab === 'progreso' && (
            <div className="client-detail__progress-tab">
              {progressToast && <Toast message={progressToast} onDismiss={() => setProgressToast(null)} />}

              {progressLoading ? (
                <LoadingState label="Cargando progreso…" variant="skeleton" rows={3} />
              ) : progressError ? (
                <ErrorMessage message={progressError} onRetry={loadProgress} />
              ) : (
                <>
                  {isStaff && showProgressForm && (
                    <form className="client-detail__assign-form" onSubmit={handleRegisterProgressSubmit}>
                      {progressServerError && (
                        <ErrorMessage title="No se pudo guardar el registro" message={progressServerError} />
                      )}
                      <div className="client-detail__assign-row">
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressDate">
                            Fecha
                          </label>
                          <input
                            id="progressDate"
                            type="date"
                            className="input"
                            value={progressDate}
                            onChange={(e) => setProgressDate(e.target.value)}
                          />
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressWeightKg">
                            Peso (kg)
                          </label>
                          <input
                            id="progressWeightKg"
                            type="number"
                            min={0}
                            step="0.1"
                            className="input"
                            value={progressWeightKg}
                            onChange={(e) => setProgressWeightKg(e.target.value)}
                            placeholder="78.5"
                          />
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressHeightCm">
                            Estatura (cm, opcional)
                          </label>
                          <input
                            id="progressHeightCm"
                            type="number"
                            min={0}
                            step="0.1"
                            className="input"
                            value={progressHeightCm}
                            onChange={(e) => setProgressHeightCm(e.target.value)}
                          />
                        </div>
                      </div>
                      <div className="client-detail__assign-row">
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressBodyFatPct">
                            % grasa corporal (opcional)
                          </label>
                          <input
                            id="progressBodyFatPct"
                            type="number"
                            min={0}
                            max={100}
                            step="0.1"
                            className="input"
                            value={progressBodyFatPct}
                            onChange={(e) => setProgressBodyFatPct(e.target.value)}
                          />
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressWaistCm">
                            Cintura (cm, opcional)
                          </label>
                          <input
                            id="progressWaistCm"
                            type="number"
                            min={0}
                            step="0.1"
                            className="input"
                            value={progressWaistCm}
                            onChange={(e) => setProgressWaistCm(e.target.value)}
                          />
                        </div>
                        <div className="client-detail__field">
                          <label className="field-label" htmlFor="progressNotes">
                            Notas (opcional)
                          </label>
                          <input
                            id="progressNotes"
                            className="input"
                            value={progressNotes}
                            onChange={(e) => setProgressNotes(e.target.value)}
                          />
                        </div>
                      </div>
                      <div className="client-detail__assign-actions">
                        <button
                          type="button"
                          className="btn btn-ghost"
                          onClick={() => {
                            setShowProgressForm(false)
                            resetProgressForm()
                          }}
                        >
                          Cancelar
                        </button>
                        <button type="submit" className="btn btn-primary" disabled={isSubmittingProgress}>
                          {isSubmittingProgress ? 'Guardando…' : 'Guardar registro'}
                        </button>
                      </div>
                    </form>
                  )}

                  {!progressRecords || progressRecords.length === 0 ? (
                    !showProgressForm && (
                      <EmptyState
                        title="Sin registros de progreso corporal"
                        description={
                          isStaff
                            ? 'Registra el primer avance de este cliente.'
                            : 'Todavía no tienes registros de progreso corporal.'
                        }
                        actionLabel={isStaff ? 'Registrar progreso' : undefined}
                        onAction={isStaff ? () => setShowProgressForm(true) : undefined}
                      />
                    )
                  ) : (
                    <div className="client-detail__progress">
                      {isStaff && !showProgressForm && (
                        <div className="client-detail__assign-actions">
                          <button type="button" className="btn btn-primary" onClick={() => setShowProgressForm(true)}>
                            + Registrar progreso
                          </button>
                        </div>
                      )}
                      <div className="client-detail__progress-chart">
                        <ProgressChart
                          points={progressRecords.map((p) => ({ date: p.record_date, value: Number(p.weight_kg) }))}
                          unit="kg"
                        />
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
                          {[...progressRecords].reverse().map((p) => (
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
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </Tabs>
      </div>
    </div>
  )
}
