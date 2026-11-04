import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ApiError, apiFetch } from '../api/client'
import { useAppShell } from '../components/layout/AppShellContext'
import { IconBarbell, IconBowl, IconCard, IconTrend, IconUsers } from '../components/layout/icons'
import { useResultsPanel } from '../components/layout/useResultsPanel'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { QuickActionCard } from '../components/ui/QuickActionCard'
import { StatNumber } from '../components/ui/StatNumber'
import { StatusPill } from '../components/ui/StatusPill'
import { useAuth } from '../hooks/useAuth'
import type {
  ApiAuditLog,
  ApiBodyProgress,
  ApiClientProfile,
  ApiMembership,
  ApiMembershipPlan,
  ApiNotification,
  ApiPayment,
} from '../types/api'
import type { UserRole } from '../types/models'
import { getMembershipDisplayStatus, isMembershipExpiringSoon, pickCurrentMembership } from '../utils/membership'
import './DashboardPage.css'

const MONTH_NAMES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]

interface QuickAction {
  to: string
  title: string
  description: string
  icon: ReactNode
  tone?: 'primary' | 'neutral'
}

const ACTIONS_BY_ROLE: Record<UserRole, QuickAction[]> = {
  admin: [
    {
      to: '/clientes/nuevo',
      title: 'Registrar cliente',
      description: 'Alta de cliente, membresía y pago inicial.',
      icon: <IconUsers />,
      tone: 'primary',
    },
    {
      to: '/membresias',
      title: 'Registrar pago',
      description: 'Cobra una membresía desde el listado de clientes.',
      icon: <IconCard />,
    },
    {
      to: '/membresias',
      title: 'Ver vencimientos',
      description: 'Revisa membresías vencidas y por vencer.',
      icon: <IconTrend />,
    },
  ],
  entrenador: [
    {
      to: '/clientes',
      title: 'Mis clientes',
      description: 'Consulta el padrón de clientes asignados.',
      icon: <IconUsers />,
      tone: 'primary',
    },
    {
      to: '/rutinas',
      title: 'Asignar rutina',
      description: 'Crea o asigna una rutina de entrenamiento.',
      icon: <IconBarbell />,
    },
    {
      to: '/dietas',
      title: 'Asignar dieta',
      description: 'Asigna un plan de alimentación a un cliente.',
      icon: <IconBowl />,
    },
  ],
  cliente: [
    {
      to: '/rutinas',
      title: 'Mi rutina',
      description: 'Consulta tu rutina de entrenamiento asignada.',
      icon: <IconBarbell />,
      tone: 'primary',
    },
    {
      to: '/dietas',
      title: 'Mi dieta',
      description: 'Consulta tu plan de alimentación asignado.',
      icon: <IconBowl />,
    },
    {
      to: '/progreso',
      title: 'Mi progreso',
      description: 'Revisa tu evolución de peso y medidas.',
      icon: <IconTrend />,
    },
    {
      to: '/membresias',
      title: 'Mi membresía',
      description: 'Consulta el estado de tu membresía (solo lectura).',
      icon: <IconCard />,
    },
  ],
}

const ROLE_LABEL: Record<UserRole, string> = {
  admin: 'Administración / Recepción',
  entrenador: 'Entrenador',
  cliente: 'Cliente (solo lectura)',
}

/** Ventana de aviso usada por `GET /memberships/expiring` -- igual a `EXPIRING_SOON_WINDOW_DAYS` de `utils/membership.ts`. */
const DAYS_AHEAD = 7

export function DashboardPage() {
  const { mockRole } = useAppShell()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  // --- Pagos del mes y última acción de bitácora (admin/entrenador) ------
  // `ClientProfile` nunca tuvo un campo `is_active` -- eso era un concepto
  // del mock de Entrega 1 sin equivalente real en el modelo de datos (ver
  // `MODELO-DATOS.md`); "Clientes activos" se reemplaza por el conteo real
  // del padrón ya cargado (`clientById`, ver abajo), sin inventar un estado
  // que la base de datos no tiene.
  const currentMonthPrefix = new Date().toISOString().slice(0, 7)
  const currentMonthName = MONTH_NAMES[new Date().getMonth()]

  const [monthPayments, setMonthPayments] = useState<ApiPayment[] | null>(null)
  const [paymentsLoading, setPaymentsLoading] = useState(true)

  // Bitácora (RF015): solo `admin` -- `GET /audit-logs` responde 403 a
  // entrenador/cliente (ver routers/notifications.py). `limit=1` basta: el
  // repositorio ya ordena por `created_at` descendente.
  const [lastAuditLog, setLastAuditLog] = useState<ApiAuditLog | null>(null)
  const [lastAuditLoading, setLastAuditLoading] = useState(false)

  useEffect(() => {
    if (mockRole === 'cliente') {
      setPaymentsLoading(false)
      return
    }
    setPaymentsLoading(true)
    apiFetch<ApiPayment[]>('/payments')
      .then(setMonthPayments)
      .catch(() => setMonthPayments([]))
      .finally(() => setPaymentsLoading(false))

    if (mockRole === 'admin') {
      setLastAuditLoading(true)
      apiFetch<ApiAuditLog[]>('/audit-logs?limit=1')
        .then((logs) => setLastAuditLog(logs[0] ?? null))
        .catch(() => setLastAuditLog(null))
        .finally(() => setLastAuditLoading(false))
    }
  }, [mockRole])

  const monthIncome = (monthPayments ?? [])
    .filter((p) => p.payment_date.startsWith(currentMonthPrefix))
    .reduce((sum, p) => sum + Number(p.amount), 0)

  // --- Alertas de membresía reales (RF006) -------------------------------
  // `GET /memberships/expiring` ya trae mezcladas las vencidas (status
  // persistido) y las por vencer (activa, end_date dentro de la ventana) --
  // se separan aquí con el mismo criterio de `utils/membership.ts` que ya
  // usa el resto del proyecto, nunca un criterio nuevo inventado aquí.
  const [expiringMemberships, setExpiringMemberships] = useState<ApiMembership[] | null>(null)
  const [expiringLoading, setExpiringLoading] = useState(true)
  const [expiringError, setExpiringError] = useState<string | null>(null)

  // Mapa en memoria cliente -> nombre, mismo patrón ya usado por
  // `MembershipsPage.tsx` (sin N+1): admin/entrenador cargan `GET /clients`
  // completo (ya filtrado por ownership en el backend); `cliente` no tiene
  // acceso a esa lista (403), así que usa `GET /clients/me`.
  const [alertClients, setAlertClients] = useState<ApiClientProfile[] | null>(null)
  const [alertClientsLoading, setAlertClientsLoading] = useState(true)
  const [alertClientsError, setAlertClientsError] = useState<string | null>(null)

  const [recentNotifications, setRecentNotifications] = useState<ApiNotification[] | null>(null)
  const [notificationsLoading, setNotificationsLoading] = useState(true)

  const handleSectionError = (err: unknown, onOther: (message: string) => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        navigate('/login', { replace: true })
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  const loadExpiring = () => {
    setExpiringLoading(true)
    setExpiringError(null)
    apiFetch<ApiMembership[]>(`/memberships/expiring?days_ahead=${DAYS_AHEAD}`)
      .then(setExpiringMemberships)
      .catch((err: unknown) => handleSectionError(err, setExpiringError))
      .finally(() => setExpiringLoading(false))
  }

  const loadAlertClients = () => {
    setAlertClientsLoading(true)
    setAlertClientsError(null)
    const request =
      user?.role === 'cliente'
        ? apiFetch<ApiClientProfile>('/clients/me').then((profile) => [profile])
        : apiFetch<ApiClientProfile[]>('/clients')
    request
      .then(setAlertClients)
      .catch((err: unknown) => handleSectionError(err, setAlertClientsError))
      .finally(() => setAlertClientsLoading(false))
  }

  useEffect(() => {
    loadExpiring()
    loadAlertClients()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!user) {
      setRecentNotifications([])
      setNotificationsLoading(false)
      return
    }
    setNotificationsLoading(true)
    apiFetch<ApiNotification[]>(`/notifications/users/${user.id}`)
      .then(setRecentNotifications)
      .catch(() => setRecentNotifications([]))
      .finally(() => setNotificationsLoading(false))
  }, [user])

  const clientById = useMemo(() => {
    const map = new Map<number, ApiClientProfile>()
    alertClients?.forEach((c) => map.set(c.id, c))
    return map
  }, [alertClients])

  const expiringSoon = (expiringMemberships ?? []).filter((m) => isMembershipExpiringSoon(m))
  const expiredReal = (expiringMemberships ?? []).filter((m) => m.status === 'vencida')

  // --- Resumen propio del cliente (RF011/RF013) --------------------------
  // `alertClients` ya trae el perfil propio cuando `user.role === 'cliente'`
  // (ver `loadAlertClients` arriba, usa `GET /clients/me`) -- se reusa en
  // vez de pedirlo otra vez. Si quien previsualiza "Cliente" con el switch
  // de desarrollo es en realidad un admin/entrenador, no hay perfil propio
  // que mostrar (esa cuenta no es un cliente real) y las secciones de abajo
  // lo dicen explícitamente en vez de mostrar datos inventados.
  const ownProfile = user?.role === 'cliente' ? (alertClients?.[0] ?? null) : null

  const [ownMembership, setOwnMembership] = useState<ApiMembership | null>(null)
  const [ownPlan, setOwnPlan] = useState<ApiMembershipPlan | null>(null)
  const [ownMembershipLoading, setOwnMembershipLoading] = useState(false)
  const [ownProgress, setOwnProgress] = useState<ApiBodyProgress[] | null>(null)
  const [ownProgressLoading, setOwnProgressLoading] = useState(false)

  useEffect(() => {
    if (!ownProfile) {
      setOwnMembership(null)
      setOwnPlan(null)
      setOwnProgress(null)
      return
    }

    setOwnMembershipLoading(true)
    Promise.all([
      apiFetch<ApiMembership[]>('/memberships'),
      apiFetch<ApiMembershipPlan[]>('/membership-plans'),
    ])
      .then(([memberships, plans]) => {
        const current = pickCurrentMembership(memberships) ?? null
        setOwnMembership(current)
        setOwnPlan(current ? (plans.find((p) => p.id === current.plan_id) ?? null) : null)
      })
      .catch(() => {
        setOwnMembership(null)
        setOwnPlan(null)
      })
      .finally(() => setOwnMembershipLoading(false))

    setOwnProgressLoading(true)
    apiFetch<ApiBodyProgress[]>(`/progress/clients/${ownProfile.id}`)
      .then(setOwnProgress)
      .catch(() => setOwnProgress([]))
      .finally(() => setOwnProgressLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ownProfile?.id])

  useResultsPanel(
    () => (
      <ResultsContent
        role={mockRole}
        expiringSoon={expiringSoon}
        expired={expiredReal}
        expiringLoading={expiringLoading}
        expiringError={expiringError}
        onRetryExpiring={() => {
          loadExpiring()
          loadAlertClients()
        }}
        clientById={clientById}
        clientsLoading={alertClientsLoading}
        clientsError={alertClientsError}
        recentNotifications={recentNotifications ?? []}
        notificationsLoading={notificationsLoading}
        ownProfile={ownProfile}
        ownMembership={ownMembership}
        ownPlan={ownPlan}
        ownMembershipLoading={ownMembershipLoading}
        ownProgress={ownProgress}
        ownProgressLoading={ownProgressLoading}
        lastAuditLog={lastAuditLog}
        lastAuditLoading={lastAuditLoading}
      />
    ),
    [
      mockRole,
      expiringMemberships,
      expiringLoading,
      expiringError,
      clientById,
      alertClientsLoading,
      alertClientsError,
      recentNotifications,
      notificationsLoading,
      ownProfile,
      ownMembership,
      ownPlan,
      ownMembershipLoading,
      ownProgress,
      ownProgressLoading,
      lastAuditLog,
      lastAuditLoading,
    ],
  )

  const actions = ACTIONS_BY_ROLE[mockRole]

  return (
    <div className="dashboard">
      <div className="dashboard__intro">
        <div>
          <h2 className="section-title">¿Qué puedes hacer hoy?</h2>
          <p className="dashboard__role">Vista: {ROLE_LABEL[mockRole]}</p>
        </div>
      </div>

      <div className="dashboard__actions">
        {actions.map((action) => (
          <QuickActionCard key={action.title} {...action} />
        ))}
      </div>

      {/* RF013: el cliente consulta SU PROPIA información, nunca métricas de
          negocio del gimnasio completo (clientes activos, ingresos del mes,
          etc.) -- esta sección es exclusiva de admin/entrenador. */}
      {mockRole !== 'cliente' && (
        <div className="dashboard__secondary">
          <span className="eyebrow">En números</span>
          <div className="dashboard__stats">
            <div className="card dashboard__stat-card">
              <StatNumber
                value={alertClientsLoading ? '…' : clientById.size}
                label={mockRole === 'admin' ? 'Clientes' : 'Mis clientes asignados'}
              />
            </div>
            <div className="card dashboard__stat-card">
              <StatNumber
                value={paymentsLoading ? '…' : `$${monthIncome.toLocaleString('es-MX')}`}
                label={`Ingresos de ${currentMonthName}`}
              />
            </div>
            <div className="card dashboard__stat-card">
              <StatNumber
                value={expiringLoading ? '…' : expiringError ? '—' : expiringSoon.length}
                label="Membresías por vencer"
                tone="warning"
              />
            </div>
            <div className="card dashboard__stat-card">
              <StatNumber
                value={expiringLoading ? '…' : expiringError ? '—' : expiredReal.length}
                label="Membresías vencidas"
                tone="danger"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * Contenido de la columna "Resultados" (zona derecha) — varía por rol mock:
 * admin/entrenador ven alertas operativas (vencimientos, notificaciones,
 * última acción); cliente ve el resumen de su propia cuenta.
 */
function ResultsContent({
  role,
  expiringSoon,
  expired,
  expiringLoading,
  expiringError,
  onRetryExpiring,
  clientById,
  clientsLoading,
  clientsError,
  recentNotifications,
  notificationsLoading,
  ownProfile,
  ownMembership,
  ownPlan,
  ownMembershipLoading,
  ownProgress,
  ownProgressLoading,
  lastAuditLog,
  lastAuditLoading,
}: {
  role: UserRole
  expiringSoon: ApiMembership[]
  expired: ApiMembership[]
  expiringLoading: boolean
  expiringError: string | null
  onRetryExpiring: () => void
  clientById: Map<number, ApiClientProfile>
  clientsLoading: boolean
  clientsError: string | null
  recentNotifications: ApiNotification[]
  notificationsLoading: boolean
  ownProfile: ApiClientProfile | null
  ownMembership: ApiMembership | null
  ownPlan: ApiMembershipPlan | null
  ownMembershipLoading: boolean
  ownProgress: ApiBodyProgress[] | null
  ownProgressLoading: boolean
  lastAuditLog: ApiAuditLog | null
  lastAuditLoading: boolean
}) {
  if (role === 'cliente') {
    // Sin perfil propio: quien está previsualizando "Cliente" con el switch
    // de desarrollo es en realidad una cuenta admin/entrenador sin
    // ClientProfile -- no hay datos reales que mostrar, se dice así en vez
    // de inventar un cliente de ejemplo.
    if (!ownProfile) {
      return (
        <div className="dashboard-results">
          <EmptyState
            compact
            title="Sin perfil de cliente"
            description="Esta cuenta no tiene un perfil de cliente propio (vista de prueba)."
          />
        </div>
      )
    }

    const lastProgress = ownProgress && ownProgress.length > 0 ? ownProgress[ownProgress.length - 1] : null

    return (
      <div className="dashboard-results">
        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi membresía</h3>
          {ownMembershipLoading ? (
            <LoadingState label="Cargando…" />
          ) : ownMembership && ownPlan ? (
            <div className="dashboard-results__row">
              <StatusPill status={getMembershipDisplayStatus(ownMembership)} />
              <p>
                Plan {ownPlan.name} · vence el {ownMembership.end_date}
              </p>
            </div>
          ) : (
            <EmptyState compact title="Sin membresía activa" description="Acércate a recepción para reactivarla." />
          )}
        </section>

        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi progreso más reciente</h3>
          {ownProgressLoading ? (
            <LoadingState label="Cargando…" />
          ) : lastProgress ? (
            <p className="dashboard-results__text">
              {Number(lastProgress.weight_kg)} kg registrados el {lastProgress.record_date}
            </p>
          ) : (
            <EmptyState compact title="Sin registros" description="Todavía no hay mediciones guardadas." />
          )}
        </section>

        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi entrenador</h3>
          <p className="dashboard-results__text">{ownProfile.trainer_name ?? 'Sin asignar'}</p>
        </section>
      </div>
    )
  }

  const attentionList = [...expired, ...expiringSoon]
    .sort((a, b) => a.end_date.localeCompare(b.end_date))
    .slice(0, 5)
  const sectionLoading = expiringLoading || clientsLoading
  const sectionError = expiringError ?? clientsError
  const recentForList = recentNotifications.slice(0, 4)

  return (
    <div className="dashboard-results">
      <section className="dashboard-results__section">
        <div className="dashboard-results__section-header">
          <h3 className="dashboard-results__heading">Alertas de membresía</h3>
          <Link to="/membresias" className="dashboard-results__link">
            Ver todas
          </Link>
        </div>
        {sectionLoading ? (
          <LoadingState label="Cargando alertas…" />
        ) : sectionError ? (
          <ErrorMessage message={sectionError} onRetry={onRetryExpiring} />
        ) : attentionList.length === 0 ? (
          <EmptyState compact title="Sin pendientes" description="No hay membresías vencidas ni por vencer." />
        ) : (
          <ul className="dashboard-results__list">
            {attentionList.map((m) => (
              <li key={m.id} className="dashboard-results__item">
                <Link to={`/clientes/${m.client_id}`} className="dashboard-results__item-name">
                  {clientById.get(m.client_id)?.full_name ?? 'Cliente no disponible'}
                </Link>
                <StatusPill status={getMembershipDisplayStatus(m)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="dashboard-results__section">
        <h3 className="dashboard-results__heading">Elementos recientes</h3>
        {notificationsLoading ? (
          <LoadingState label="Cargando notificaciones…" />
        ) : recentForList.length === 0 ? (
          <EmptyState compact title="Sin notificaciones" />
        ) : (
          <ul className="dashboard-results__notifications">
            {recentForList.map((n) => (
              <li key={n.id} className="dashboard-results__notification" data-unread={!n.is_read}>
                <span className="dashboard-results__notification-dot" />
                <div>
                  <p>{n.message}</p>
                  <span className="dashboard-results__notification-date">
                    {new Date(n.created_at).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' })}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Bitácora (RF015): solo admin -- GET /audit-logs devuelve 403 a
          entrenador/cliente, ver routers/notifications.py. */}
      {role === 'admin' && (
        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Última acción registrada</h3>
          {lastAuditLoading ? (
            <LoadingState label="Cargando…" />
          ) : lastAuditLog ? (
            <p className="dashboard-results__text">
              {lastAuditLog.details ?? `${lastAuditLog.action} · ${lastAuditLog.entity_type}`}
            </p>
          ) : (
            <EmptyState compact title="Sin actividad" />
          )}
        </section>
      )}
    </div>
  )
}
