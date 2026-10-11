import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useAppShell } from '../components/layout/AppShellContext'
import { IconBarbell, IconBowl, IconCard, IconTrend, IconUsers } from '../components/layout/icons'
import { useResultsPanel } from '../components/layout/useResultsPanel'
import { EmptyState } from '../components/ui/EmptyState'
import { QuickActionCard } from '../components/ui/QuickActionCard'
import { StatNumber } from '../components/ui/StatNumber'
import { StatusPill } from '../components/ui/StatusPill'
import {
  auditLogs,
  clients,
  findClientProfile,
  findMembershipByClient,
  findMembershipPlan,
  getBodyProgressForClient,
  getClientDisplayName,
  getMembershipDisplayStatusMock,
  getNotificationsForUser,
  getTrainerDisplayName,
  memberships,
  MOCK_TODAY,
  payments,
} from '../mocks/data'
import type { Membership, UserRole } from '../types/models'
import { isMembershipExpiringSoon } from '../utils/membership'
import './DashboardPage.css'

const CURRENT_MONTH_PREFIX = '2026-09'

/**
 * No existe todavía sesión real de cliente (la construye el proceso de
 * autenticación en paralelo) — para demostrar "resumen del cliente actual"
 * en la zona Resultados cuando el rol mock es "cliente", se fija este id
 * de ejemplo (Karla Jiménez, ya tiene membresía/rutina/dieta/progreso
 * completos en mocks/data.ts). Punto de integración: reemplazar por el
 * client_id real de la sesión.
 */
const DEMO_CLIENT_ID = 100

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

export function DashboardPage() {
  const { mockRole } = useAppShell()

  const activeClients = clients.filter((c) => c.is_active).length
  const monthIncome = payments
    .filter((p) => p.payment_date.startsWith(CURRENT_MONTH_PREFIX))
    .reduce((sum, p) => sum + p.amount, 0)
  // "Por vencer" se calcula sobre end_date, no es un status persistido
  // (ver DECISIONES.md, arbitraje del 2026-09-12).
  const expiring = memberships.filter((m) => isMembershipExpiringSoon(m, MOCK_TODAY))
  const expired = memberships.filter((m) => m.status === 'vencida')

  useResultsPanel(<ResultsContent role={mockRole} expiring={expiring} expired={expired} />)

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

      <div className="dashboard__secondary">
        <span className="eyebrow">En números</span>
        <div className="dashboard__stats">
          <div className="card dashboard__stat-card">
            <StatNumber value={activeClients} label="Clientes activos" />
          </div>
          <div className="card dashboard__stat-card">
            <StatNumber value={`$${monthIncome.toLocaleString('es-MX')}`} label="Ingresos de septiembre" />
          </div>
          <div className="card dashboard__stat-card">
            <StatNumber value={expiring.length} label="Membresías por vencer" tone="warning" />
          </div>
          <div className="card dashboard__stat-card">
            <StatNumber value={expired.length} label="Membresías vencidas" tone="danger" />
          </div>
        </div>
      </div>
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
  expiring,
  expired,
}: {
  role: UserRole
  expiring: Membership[]
  expired: Membership[]
}) {
  if (role === 'cliente') {
    const profile = findClientProfile(DEMO_CLIENT_ID)
    const membership = findMembershipByClient(DEMO_CLIENT_ID)
    const plan = membership ? findMembershipPlan(membership.plan_id) : undefined
    const progress = getBodyProgressForClient(DEMO_CLIENT_ID)
    const lastProgress = progress[progress.length - 1]

    return (
      <div className="dashboard-results">
        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi membresía</h3>
          {membership && plan ? (
            <div className="dashboard-results__row">
              <StatusPill status={getMembershipDisplayStatusMock(membership)} />
              <p>
                Plan {plan.name} · vence el {membership.end_date}
              </p>
            </div>
          ) : (
            <EmptyState compact title="Sin membresía activa" description="Acércate a recepción para reactivarla." />
          )}
        </section>

        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi progreso más reciente</h3>
          {lastProgress ? (
            <p className="dashboard-results__text">
              {lastProgress.weight_kg} kg registrados el {lastProgress.record_date}
            </p>
          ) : (
            <EmptyState compact title="Sin registros" description="Todavía no hay mediciones guardadas." />
          )}
        </section>

        <section className="dashboard-results__section">
          <h3 className="dashboard-results__heading">Mi entrenador</h3>
          <p className="dashboard-results__text">{getTrainerDisplayName(profile?.trainer_id ?? null)}</p>
        </section>
      </div>
    )
  }

  const attentionList = [...expired, ...expiring].sort((a, b) => a.end_date.localeCompare(b.end_date)).slice(0, 5)
  const recentNotifications = getNotificationsForUser(1).slice(0, 4)
  const lastAction = [...auditLogs].sort((a, b) => b.created_at.localeCompare(a.created_at))[0]

  return (
    <div className="dashboard-results">
      <section className="dashboard-results__section">
        <div className="dashboard-results__section-header">
          <h3 className="dashboard-results__heading">Alertas de membresía</h3>
          <Link to="/membresias" className="dashboard-results__link">
            Ver todas
          </Link>
        </div>
        {attentionList.length === 0 ? (
          <EmptyState compact title="Sin pendientes" description="No hay membresías vencidas ni por vencer." />
        ) : (
          <ul className="dashboard-results__list">
            {attentionList.map((m) => (
              <li key={m.id} className="dashboard-results__item">
                <Link to={`/clientes/${m.client_id}`} className="dashboard-results__item-name">
                  {getClientDisplayName(m.client_id)}
                </Link>
                <StatusPill status={getMembershipDisplayStatusMock(m)} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="dashboard-results__section">
        <h3 className="dashboard-results__heading">Elementos recientes</h3>
        {recentNotifications.length === 0 ? (
          <EmptyState compact title="Sin notificaciones" />
        ) : (
          <ul className="dashboard-results__notifications">
            {recentNotifications.map((n) => (
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

      <section className="dashboard-results__section">
        <h3 className="dashboard-results__heading">Última acción registrada</h3>
        {lastAction ? (
          <p className="dashboard-results__text">
            {lastAction.details ?? `${lastAction.action} · ${lastAction.entity_type}`}
          </p>
        ) : (
          <EmptyState compact title="Sin actividad" />
        )}
      </section>
    </div>
  )
}
