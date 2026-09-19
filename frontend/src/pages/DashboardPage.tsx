import { Link } from 'react-router-dom'
import { StatNumber } from '../components/ui/StatNumber'
import { StatusPill } from '../components/ui/StatusPill'
import {
  clients,
  findMembershipPlan,
  getClientDisplayName,
  getMembershipDisplayStatusMock,
  getNotificationsForUser,
  memberships,
  MOCK_TODAY,
  payments,
} from '../mocks/data'
import { isMembershipExpiringSoon } from '../utils/membership'
import './DashboardPage.css'

const CURRENT_MONTH_PREFIX = '2025-09'

export function DashboardPage() {
  const activeClients = clients.filter((c) => c.is_active).length
  const monthIncome = payments
    .filter((p) => p.payment_date.startsWith(CURRENT_MONTH_PREFIX))
    .reduce((sum, p) => sum + p.amount, 0)
  // "Por vencer" se calcula sobre end_date, no es un status persistido
  // (ver DECISIONES.md, arbitraje del 2026-09-12).
  const expiring = memberships.filter((m) => isMembershipExpiringSoon(m, MOCK_TODAY))
  const expired = memberships.filter((m) => m.status === 'vencida')

  const attentionList = [...expired, ...expiring].sort((a, b) => a.end_date.localeCompare(b.end_date))
  const recentNotifications = getNotificationsForUser(1).slice(0, 5)

  return (
    <div className="dashboard">
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

      <div className="dashboard__grid">
        <section className="card dashboard__panel">
          <div className="dashboard__panel-header">
            <h2 className="section-title">Requiere atención</h2>
            <Link to="/membresias" className="dashboard__panel-link">
              Ver membresías
            </Link>
          </div>

          {attentionList.length === 0 ? (
            <p className="dashboard__empty">No hay membresías vencidas ni próximas a vencer.</p>
          ) : (
            <table className="dashboard__table">
              <thead>
                <tr>
                  <th>Cliente</th>
                  <th>Plan</th>
                  <th>Vence</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {attentionList.map((m) => {
                  const plan = findMembershipPlan(m.plan_id)
                  return (
                    <tr key={m.id}>
                      <td>
                        <Link to={`/clientes/${m.client_id}`} className="dashboard__row-link">
                          {getClientDisplayName(m.client_id)}
                        </Link>
                      </td>
                      <td>{plan?.name}</td>
                      <td>{m.end_date}</td>
                      <td>
                        <StatusPill status={getMembershipDisplayStatusMock(m)} />
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </section>

        <section className="card dashboard__panel">
          <div className="dashboard__panel-header">
            <h2 className="section-title">Notificaciones recientes</h2>
          </div>
          <ul className="dashboard__notifications">
            {recentNotifications.map((n) => (
              <li key={n.id} className="dashboard__notification" data-unread={!n.is_read}>
                <span className="dashboard__notification-dot" />
                <div>
                  <p>{n.message}</p>
                  <span className="dashboard__notification-date">
                    {new Date(n.created_at).toLocaleDateString('es-MX', { day: '2-digit', month: 'short' })}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  )
}
