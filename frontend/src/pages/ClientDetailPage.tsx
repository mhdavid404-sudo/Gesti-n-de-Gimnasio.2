import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatusPill } from '../components/ui/StatusPill'
import { Tabs } from '../components/ui/Tabs'
import {
  findClientProfile,
  findDietPlan,
  findExercise,
  findMembershipByClient,
  findMembershipPlan,
  findRoutine,
  findUser,
  getBodyProgressForClient,
  getDietAssignmentsForClient,
  getMembershipDisplayStatusMock,
  getPaymentsForMembership,
  getRoutineAssignmentsForClient,
  getRoutineExercises,
  getTrainerDisplayName,
} from '../mocks/data'
import './ClientDetailPage.css'

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
  const clientProfileId = Number(id)

  const profile = findClientProfile(clientProfileId)
  const user = profile ? findUser(profile.user_id) : undefined

  if (!profile || !user) {
    return (
      <div className="card">
        <p>No se encontró este cliente en los datos de ejemplo.</p>
        <Link to="/clientes" className="btn btn-ghost" style={{ marginTop: 12 }}>
          Volver a clientes
        </Link>
      </div>
    )
  }

  const membership = findMembershipByClient(profile.id)
  const plan = membership ? findMembershipPlan(membership.plan_id) : undefined
  const payments = membership ? getPaymentsForMembership(membership.id) : []
  const routineAssignments = getRoutineAssignmentsForClient(profile.id)
  const dietAssignments = getDietAssignmentsForClient(profile.id)
  const progress = getBodyProgressForClient(profile.id)
  const lastProgress = progress[progress.length - 1]

  return (
    <div className="client-detail">
      <div className="client-detail__header card">
        <div className="client-detail__avatar">
          {user.full_name
            .split(' ')
            .slice(0, 2)
            .map((p) => p[0])
            .join('')}
        </div>
        <div className="client-detail__identity">
          <h2 className="section-title">{user.full_name}</h2>
          <p className="client-detail__email">{user.email}</p>
        </div>
        <div className="client-detail__header-meta">
          <div>
            <span className="eyebrow">Entrenador</span>
            <p>{getTrainerDisplayName(profile.trainer_id)}</p>
          </div>
          <div>
            <span className="eyebrow">Membresía</span>
            {membership ? (
              <StatusPill status={getMembershipDisplayStatusMock(membership)} />
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
                <dd>{profile.phone}</dd>
              </div>
              <div>
                <dt>Fecha de nacimiento</dt>
                <dd>{profile.birth_date}</dd>
              </div>
              <div>
                <dt>Dirección</dt>
                <dd>{profile.address}</dd>
              </div>
              <div>
                <dt>Contacto de emergencia</dt>
                <dd>{profile.emergency_contact ?? '—'}</dd>
              </div>
              <div>
                <dt>Cliente desde</dt>
                <dd>{new Date(profile.created_at).toLocaleDateString('es-MX')}</dd>
              </div>
              <div>
                <dt>Estado de la cuenta</dt>
                <dd>{user.is_active ? 'Activo' : 'Inactivo'}</dd>
              </div>
            </dl>
          )}

          {activeTab === 'membresia' &&
            (membership && plan ? (
              <dl className="client-detail__grid">
                <div>
                  <dt>Plan</dt>
                  <dd>{plan.name}</dd>
                </div>
                <div>
                  <dt>Precio</dt>
                  <dd>${plan.price.toLocaleString('es-MX')} / mes</dd>
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
                    <StatusPill status={getMembershipDisplayStatusMock(membership)} />
                  </dd>
                </div>
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
              </dl>
            ) : (
              <p className="client-detail__empty">Este cliente no tiene una membresía registrada.</p>
            ))}

          {activeTab === 'pagos' &&
            (payments.length > 0 ? (
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
                      <td>${p.amount.toLocaleString('es-MX')}</td>
                      <td className="client-detail__capitalize">{p.method}</td>
                      <td>
                        <StatusPill status={p.status} />
                      </td>
                      <td>{p.notes ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="client-detail__empty">No hay pagos registrados.</p>
            ))}

          {activeTab === 'rutina' &&
            (routineAssignments.length > 0 ? (
              <div className="client-detail__stack">
                {routineAssignments.map((ra) => {
                  const routine = findRoutine(ra.routine_id)
                  const items = getRoutineExercises(ra.routine_id)
                  return (
                    <div key={ra.id} className="client-detail__sub-card">
                      <div className="client-detail__sub-card-header">
                        <div>
                          <h3>{routine?.name}</h3>
                          <p>{routine?.description}</p>
                        </div>
                        <StatusPill status={ra.status} />
                      </div>
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
                            const exercise = findExercise(it.exercise_id)
                            return (
                              <tr key={it.id}>
                                <td>{exercise?.name}</td>
                                <td>{it.sets}</td>
                                <td>{it.reps}</td>
                                <td>{it.rest_seconds}s</td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="client-detail__empty">Este cliente no tiene rutinas asignadas.</p>
            ))}

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
                        {plan?.daily_calories ? `${plan.daily_calories} kcal / día` : 'Sin objetivo calórico definido'}{' '}
                        · asignado el {da.assigned_date}
                      </p>
                    </div>
                  )
                })}
              </div>
            ) : (
              <p className="client-detail__empty">Este cliente no tiene un plan de dieta asignado.</p>
            ))}

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
