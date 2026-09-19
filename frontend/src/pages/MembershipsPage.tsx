import { Link } from 'react-router-dom'
import { StatusPill } from '../components/ui/StatusPill'
import {
  findMembershipPlan,
  getClientDisplayName,
  getMembershipDisplayStatusMock,
  membershipPlans,
  memberships,
} from '../mocks/data'
import './MembershipsPage.css'

export function MembershipsPage() {
  return (
    <div className="memberships-page">
      <section>
        <div className="memberships-page__section-header">
          <h2 className="section-title">Planes</h2>
          <span className="eyebrow">Básica / VIP / Premium</span>
        </div>
        <div className="memberships-page__plans">
          {membershipPlans.map((plan) => (
            <article key={plan.id} className="card plan-card" data-plan={plan.name}>
              <span className="plan-card__name">{plan.name}</span>
              <div className="plan-card__price">
                ${plan.price.toLocaleString('es-MX')}
                <span>/mes</span>
              </div>
              <p className="plan-card__description">{plan.description}</p>
              <ul className="plan-card__benefits">
                {plan.benefits.map((b) => (
                  <li key={b}>{b}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="memberships-page__section-header">
          <h2 className="section-title">Membresías activas</h2>
        </div>
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
                const plan = findMembershipPlan(m.plan_id)
                return (
                  <tr key={m.id}>
                    <td>{getClientDisplayName(m.client_id)}</td>
                    <td>{plan?.name}</td>
                    <td>{m.start_date}</td>
                    <td>{m.end_date}</td>
                    <td>
                      <StatusPill status={getMembershipDisplayStatusMock(m)} />
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
      </section>
    </div>
  )
}
