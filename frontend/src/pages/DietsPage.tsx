import { useState } from 'react'
import type { FormEvent } from 'react'
import { StatusPill } from '../components/ui/StatusPill'
import {
  clientProfiles,
  dietAssignments as initialAssignments,
  dietPlans,
  findDietPlan,
  getClientDisplayName,
} from '../mocks/data'
import type { DietAssignment } from '../types/models'
import './DietsPage.css'

let nextAssignmentId = 900

export function DietsPage() {
  const [assignments, setAssignments] = useState<DietAssignment[]>(initialAssignments)
  const [clientId, setClientId] = useState<number>(clientProfiles[0]?.id ?? 0)
  const [dietPlanId, setDietPlanId] = useState<number>(dietPlans[0]?.id ?? 0)

  const handleAssign = (event: FormEvent) => {
    event.preventDefault()
    nextAssignmentId += 1
    const newAssignment: DietAssignment = {
      id: nextAssignmentId,
      diet_plan_id: dietPlanId,
      client_id: clientId,
      assigned_by: 1,
      assigned_date: new Date().toISOString().slice(0, 10),
      status: 'activa',
      notes: null,
    }
    setAssignments((prev) => [newAssignment, ...prev])
  }

  return (
    <div className="diets-page">
      <section>
        <div className="diets-page__section-header">
          <h2 className="section-title">Planes de dieta</h2>
        </div>
        <div className="diets-page__catalog">
          {dietPlans.map((plan) => (
            <article key={plan.id} className="card diet-card">
              <span className="diet-card__name">{plan.name}</span>
              <p className="diet-card__description">{plan.description}</p>
              <div className="diet-card__calories">
                {plan.daily_calories ? (
                  <>
                    <strong>{plan.daily_calories}</strong> kcal / día
                  </>
                ) : (
                  'Sin objetivo calórico fijo'
                )}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="diets-page__assign-section">
        <div className="diets-page__section-header">
          <h2 className="section-title">Asignaciones</h2>
        </div>

        <form className="card diets-page__assign-form" onSubmit={handleAssign}>
          <span className="eyebrow">Nueva asignación</span>
          <div className="diets-page__assign-row">
            <div>
              <label className="field-label" htmlFor="diet-client">
                Cliente
              </label>
              <select
                id="diet-client"
                className="input"
                value={clientId}
                onChange={(e) => setClientId(Number(e.target.value))}
              >
                {clientProfiles.map((c) => (
                  <option key={c.id} value={c.id}>
                    {getClientDisplayName(c.id)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="diet-plan">
                Plan
              </label>
              <select
                id="diet-plan"
                className="input"
                value={dietPlanId}
                onChange={(e) => setDietPlanId(Number(e.target.value))}
              >
                {dietPlans.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary">
            Asignar dieta
          </button>
        </form>

        <div className="card diets-page__table-wrap">
          <table className="diets-page__table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Plan</th>
                <th>Asignada</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((da) => (
                <tr key={da.id}>
                  <td>{getClientDisplayName(da.client_id)}</td>
                  <td>{findDietPlan(da.diet_plan_id)?.name}</td>
                  <td>{da.assigned_date}</td>
                  <td>
                    <StatusPill status={da.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
