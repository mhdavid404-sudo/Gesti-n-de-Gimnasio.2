import { useState } from 'react'
import type { FormEvent } from 'react'
import { StatusPill } from '../components/ui/StatusPill'
import {
  clientProfiles,
  exercises,
  findExercise,
  findRoutine,
  getClientDisplayName,
  getRoutineExercises,
  routineAssignments as initialAssignments,
  routines,
} from '../mocks/data'
import type { RoutineAssignment } from '../types/models'
import './RoutinesPage.css'

let nextAssignmentId = 900

export function RoutinesPage() {
  const [assignments, setAssignments] = useState<RoutineAssignment[]>(initialAssignments)
  const [clientId, setClientId] = useState<number>(clientProfiles[0]?.id ?? 0)
  const [routineId, setRoutineId] = useState<number>(routines[0]?.id ?? 0)

  const handleAssign = (event: FormEvent) => {
    event.preventDefault()
    nextAssignmentId += 1
    const newAssignment: RoutineAssignment = {
      id: nextAssignmentId,
      routine_id: routineId,
      client_id: clientId,
      assigned_by: 1,
      assigned_date: new Date().toISOString().slice(0, 10),
      status: 'activa',
      notes: null,
    }
    setAssignments((prev) => [newAssignment, ...prev])
  }

  return (
    <div className="routines-page">
      <section>
        <div className="routines-page__section-header">
          <h2 className="section-title">Catálogo de rutinas</h2>
          <span className="eyebrow">{exercises.length} ejercicios en catálogo</span>
        </div>
        <div className="routines-page__catalog">
          {routines.map((routine) => {
            const items = getRoutineExercises(routine.id)
            return (
              <details key={routine.id} className="card routine-card">
                <summary>
                  <span className="routine-card__name">{routine.name}</span>
                  <span className="routine-card__count">{items.length} ejercicios</span>
                </summary>
                <p className="routine-card__description">{routine.description}</p>
                <table className="routines-page__table">
                  <thead>
                    <tr>
                      <th>Ejercicio</th>
                      <th>Grupo muscular</th>
                      <th>Series</th>
                      <th>Reps</th>
                      <th>Descanso</th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((it) => {
                      const exercise = findExercise(it.exercise_id)
                      return (
                        <tr key={it.id}>
                          <td>{exercise?.name}</td>
                          <td>{exercise?.muscle_group}</td>
                          <td>{it.sets}</td>
                          <td>{it.reps}</td>
                          <td>{it.rest_seconds}s</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </details>
            )
          })}
        </div>
      </section>

      <section className="routines-page__assign-section">
        <div className="routines-page__section-header">
          <h2 className="section-title">Asignaciones</h2>
        </div>

        <form className="card routines-page__assign-form" onSubmit={handleAssign}>
          <span className="eyebrow">Nueva asignación</span>
          <div className="routines-page__assign-row">
            <div>
              <label className="field-label" htmlFor="assign-client">
                Cliente
              </label>
              <select
                id="assign-client"
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
              <label className="field-label" htmlFor="assign-routine">
                Rutina
              </label>
              <select
                id="assign-routine"
                className="input"
                value={routineId}
                onChange={(e) => setRoutineId(Number(e.target.value))}
              >
                {routines.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary">
            Asignar rutina
          </button>
        </form>

        <div className="card routines-page__table-wrap">
          <table className="routines-page__table">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Rutina</th>
                <th>Asignada</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {assignments.map((ra) => (
                <tr key={ra.id}>
                  <td>{getClientDisplayName(ra.client_id)}</td>
                  <td>{findRoutine(ra.routine_id)?.name}</td>
                  <td>{ra.assigned_date}</td>
                  <td>
                    <StatusPill status={ra.status} />
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
