import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiFetch, ApiError } from '../api/client'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatusPill } from '../components/ui/StatusPill'
import { Tabs } from '../components/ui/Tabs'
import { useAuth } from '../hooks/useAuth'
import {
  findDietPlan,
  findExercise,
  findMembershipByClient,
  findMembershipPlan,
  findRoutine,
  getBodyProgressForClient,
  getDietAssignmentsForClient,
  getMembershipDisplayStatusMock,
  getPaymentsForMembership,
  getRoutineAssignmentsForClient,
  getRoutineExercises,
} from '../mocks/data'
import type { ApiClientProfile } from '../types/api'
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
  const navigate = useNavigate()
  const { logout } = useAuth()
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

  // TODO(módulos Membresías/Pagos/Rutinas/Dietas/Progreso, todavía no
  // construidos): el resto de pestañas sigue usando los mismos datos mock
  // de Entrega 1, indexados por `clientProfileId` de ejemplo -- no
  // corresponden necesariamente al cliente real de esta pantalla. Se
  // reemplazan por llamadas reales cuando cada módulo exista.
  const membership = findMembershipByClient(clientProfileId)
  const plan = membership ? findMembershipPlan(membership.plan_id) : undefined
  const payments = membership ? getPaymentsForMembership(membership.id) : []
  const routineAssignments = getRoutineAssignmentsForClient(clientProfileId)
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
            {/* TODO(módulo Membresías): placeholder mock, ver nota arriba. */}
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

          {/* TODO(módulo Membresías, todavía no construido): pestaña mock. */}
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

          {/* TODO(módulo Pagos, todavía no construido): pestaña mock. */}
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

          {/* TODO(módulo Rutinas, todavía no construido): pestaña mock. */}
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
