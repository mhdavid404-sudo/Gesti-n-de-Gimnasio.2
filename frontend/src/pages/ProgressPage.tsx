import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { apiFetch, ApiError } from '../api/client'
import { EmptyState } from '../components/ui/EmptyState'
import { ErrorMessage } from '../components/ui/ErrorMessage'
import { LoadingState } from '../components/ui/LoadingState'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatNumber } from '../components/ui/StatNumber'
import { Toast } from '../components/ui/Toast'
import { useAuth } from '../hooks/useAuth'
import type { ApiBodyProgress, ApiClientProfile, BodyProgressCreatePayload } from '../types/api'
import './ProgressPage.css'

const todayIso = () => new Date().toISOString().slice(0, 10)

type MetricKey = 'weight_kg' | 'body_fat_pct' | 'waist_cm'

const METRICS: { key: MetricKey; label: string; unit: string }[] = [
  { key: 'weight_kg', label: 'Peso', unit: 'kg' },
  { key: 'body_fat_pct', label: '% de grasa corporal', unit: '%' },
  { key: 'waist_cm', label: 'Cintura', unit: 'cm' },
]

/**
 * Conectado a la API real (RF010, RF011) -- ver docstring de
 * `backend/src/api/v1/routers/progress.py`. Mismo criterio de
 * ownership-por-dato que Rutinas/Dietas: selector de cliente (`GET /clients`,
 * ya scoped por rol) para admin/entrenador, resuelto directo vía
 * `GET /clients/me` para el rol `cliente` -- sin selector, no puede ver el
 * progreso de nadie más (RF013, solo lectura).
 */
export function ProgressPage() {
  const { user, logout } = useAuth()
  const isStaff = user?.role === 'admin' || user?.role === 'entrenador'
  const isCliente = user?.role === 'cliente'

  const handleAuthError = (err: unknown, onOther: (message: string) => void, onForbidden?: () => void) => {
    if (err instanceof ApiError) {
      if (err.isUnauthorized) {
        logout()
        return
      }
      if (err.status === 403 && onForbidden) {
        onForbidden()
        return
      }
      onOther(err.message)
      return
    }
    onOther('Ocurrió un error inesperado. Intenta de nuevo.')
  }

  // --- Selector de cliente ---------------------------------------------
  const [clients, setClients] = useState<ApiClientProfile[] | null>(null)
  const [clientsLoading, setClientsLoading] = useState(true)
  const [clientsError, setClientsError] = useState<string | null>(null)
  const [selectedClientId, setSelectedClientId] = useState<number | null>(null)
  const [ownClientName, setOwnClientName] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return

    if (isCliente) {
      setClientsLoading(true)
      setClientsError(null)
      apiFetch<ApiClientProfile>('/clients/me')
        .then((profile) => {
          setSelectedClientId(profile.id)
          setOwnClientName(profile.full_name)
        })
        .catch((err: unknown) => handleAuthError(err, setClientsError))
        .finally(() => setClientsLoading(false))
      return
    }

    setClientsLoading(true)
    setClientsError(null)
    apiFetch<ApiClientProfile[]>('/clients')
      .then(setClients)
      .catch((err: unknown) =>
        handleAuthError(err, setClientsError, () => setClientsError('No tienes permiso para ver clientes.')),
      )
      .finally(() => setClientsLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.role])

  const selectedClient = clients?.find((c) => c.id === selectedClientId)

  // --- Registros de progreso del cliente seleccionado --------------------
  const [records, setRecords] = useState<ApiBodyProgress[] | null>(null)
  const [recordsLoading, setRecordsLoading] = useState(false)
  const [recordsError, setRecordsError] = useState<string | null>(null)

  const loadRecords = (clientId: number) => {
    setRecordsLoading(true)
    setRecordsError(null)
    apiFetch<ApiBodyProgress[]>(`/progress/clients/${clientId}`)
      .then(setRecords)
      .catch((err: unknown) =>
        handleAuthError(err, setRecordsError, () => setRecordsError('No tienes acceso al progreso de este cliente.')),
      )
      .finally(() => setRecordsLoading(false))
  }

  useEffect(() => {
    if (selectedClientId == null) {
      setRecords(null)
      return
    }
    loadRecords(selectedClientId)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedClientId])

  // --- Alta de registro (admin/entrenador) --------------------------------
  const [showForm, setShowForm] = useState(false)
  const [recordDate, setRecordDate] = useState(todayIso)
  const [weightKg, setWeightKg] = useState('')
  const [heightCm, setHeightCm] = useState('')
  const [bodyFatPct, setBodyFatPct] = useState('')
  const [muscleMassKg, setMuscleMassKg] = useState('')
  const [chestCm, setChestCm] = useState('')
  const [waistCm, setWaistCm] = useState('')
  const [hipCm, setHipCm] = useState('')
  const [armCm, setArmCm] = useState('')
  const [notes, setNotes] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  const resetForm = () => {
    setRecordDate(todayIso())
    setWeightKg('')
    setHeightCm('')
    setBodyFatPct('')
    setMuscleMassKg('')
    setChestCm('')
    setWaistCm('')
    setHipCm('')
    setArmCm('')
    setNotes('')
    setFormError(null)
  }

  const optionalNumber = (value: string): number | null | undefined => {
    if (!value.trim()) return null
    const n = Number(value)
    return Number.isNaN(n) ? undefined : n
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setFormError(null)
    if (selectedClientId == null) return

    const weightValue = Number(weightKg)
    if (!weightKg || Number.isNaN(weightValue) || weightValue <= 0) {
      setFormError('Ingresa un peso válido (mayor a 0).')
      return
    }
    if (!recordDate) {
      setFormError('Selecciona la fecha del registro.')
      return
    }

    const parsed = {
      height: optionalNumber(heightCm),
      bodyFat: optionalNumber(bodyFatPct),
      muscleMass: optionalNumber(muscleMassKg),
      chest: optionalNumber(chestCm),
      waist: optionalNumber(waistCm),
      hip: optionalNumber(hipCm),
      arm: optionalNumber(armCm),
    }
    if (Object.values(parsed).some((v) => v === undefined)) {
      setFormError('Revisa las medidas opcionales -- deben ser números.')
      return
    }

    const payload: BodyProgressCreatePayload = {
      client_id: selectedClientId,
      record_date: recordDate,
      weight_kg: weightValue,
      height_cm: parsed.height ?? null,
      body_fat_pct: parsed.bodyFat ?? null,
      muscle_mass_kg: parsed.muscleMass ?? null,
      chest_cm: parsed.chest ?? null,
      waist_cm: parsed.waist ?? null,
      hip_cm: parsed.hip ?? null,
      arm_cm: parsed.arm ?? null,
      notes: notes.trim() || null,
    }

    setIsSubmitting(true)
    try {
      const created = await apiFetch<ApiBodyProgress>('/progress', { method: 'POST', body: payload })
      setRecords((prev) => [...(prev ?? []), created].sort((a, b) => a.record_date.localeCompare(b.record_date)))
      setToast('Registro de progreso guardado.')
      resetForm()
      setShowForm(false)
    } catch (err) {
      handleAuthError(err, setFormError, () => setFormError('No tienes permiso para registrar progreso de este cliente.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  // --- Gráfica -------------------------------------------------------------
  const [metricKey, setMetricKey] = useState<MetricKey>('weight_kg')
  const metric = METRICS.find((m) => m.key === metricKey)!

  const numericRecords = useMemo(
    () =>
      (records ?? []).map((r) => ({
        ...r,
        weight_kg: Number(r.weight_kg),
        height_cm: r.height_cm != null ? Number(r.height_cm) : null,
        body_fat_pct: r.body_fat_pct != null ? Number(r.body_fat_pct) : null,
        waist_cm: r.waist_cm != null ? Number(r.waist_cm) : null,
      })),
    [records],
  )

  const points = numericRecords
    .filter((r) => r[metricKey] !== null)
    .map((r) => ({ date: r.record_date, value: r[metricKey] as number }))

  const latest = numericRecords[numericRecords.length - 1]

  return (
    <div className="progress-page">
      {toast && <Toast message={toast} onDismiss={() => setToast(null)} />}

      <section className="card progress-page__client-section">
        {clientsLoading ? (
          <LoadingState label="Cargando clientes…" variant="skeleton" rows={2} />
        ) : clientsError ? (
          <ErrorMessage message={clientsError} />
        ) : isCliente ? (
          <p className="eyebrow progress-page__own-client">{ownClientName ?? 'Tu progreso corporal'}</p>
        ) : (
          <div className="progress-page__client-picker">
            <label className="field-label" htmlFor="progress-client">
              Cliente
            </label>
            <select
              id="progress-client"
              className="input"
              value={selectedClientId ?? ''}
              onChange={(e) => setSelectedClientId(e.target.value ? Number(e.target.value) : null)}
            >
              <option value="">Selecciona un cliente</option>
              {clients?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.full_name}
                </option>
              ))}
            </select>
          </div>
        )}
      </section>

      {selectedClientId == null ? (
        <div className="card">
          <EmptyState title="Selecciona un cliente" description="Elige un cliente arriba para ver su progreso corporal." />
        </div>
      ) : (
        <>
          {isStaff && (
            <div className="progress-page__toolbar">
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  setShowForm((prev) => !prev)
                  if (showForm) resetForm()
                }}
              >
                {showForm ? 'Cancelar' : '+ Registrar progreso'}
              </button>
            </div>
          )}

          {isStaff && showForm && (
            <form className="card progress-page__inline-form" onSubmit={handleSubmit}>
              {formError && <ErrorMessage title="No se pudo guardar el registro" message={formError} />}
              <div className="progress-page__form-row">
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="recordDate">
                    Fecha
                  </label>
                  <input
                    id="recordDate"
                    type="date"
                    className="input"
                    value={recordDate}
                    onChange={(e) => setRecordDate(e.target.value)}
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="weightKg">
                    Peso (kg)
                  </label>
                  <input
                    id="weightKg"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={weightKg}
                    onChange={(e) => setWeightKg(e.target.value)}
                    placeholder="78.5"
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="heightCm">
                    Estatura (cm, opcional)
                  </label>
                  <input
                    id="heightCm"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={heightCm}
                    onChange={(e) => setHeightCm(e.target.value)}
                    placeholder="175"
                  />
                </div>
              </div>
              <div className="progress-page__form-row">
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="bodyFatPct">
                    % grasa corporal (opcional)
                  </label>
                  <input
                    id="bodyFatPct"
                    type="number"
                    min={0}
                    max={100}
                    step="0.1"
                    className="input"
                    value={bodyFatPct}
                    onChange={(e) => setBodyFatPct(e.target.value)}
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="muscleMassKg">
                    Masa muscular (kg, opcional)
                  </label>
                  <input
                    id="muscleMassKg"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={muscleMassKg}
                    onChange={(e) => setMuscleMassKg(e.target.value)}
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="waistCm">
                    Cintura (cm, opcional)
                  </label>
                  <input
                    id="waistCm"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={waistCm}
                    onChange={(e) => setWaistCm(e.target.value)}
                  />
                </div>
              </div>
              <div className="progress-page__form-row">
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="chestCm">
                    Pecho (cm, opcional)
                  </label>
                  <input
                    id="chestCm"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={chestCm}
                    onChange={(e) => setChestCm(e.target.value)}
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="hipCm">
                    Cadera (cm, opcional)
                  </label>
                  <input
                    id="hipCm"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={hipCm}
                    onChange={(e) => setHipCm(e.target.value)}
                  />
                </div>
                <div className="progress-page__field">
                  <label className="field-label" htmlFor="armCm">
                    Brazo (cm, opcional)
                  </label>
                  <input
                    id="armCm"
                    type="number"
                    min={0}
                    step="0.1"
                    className="input"
                    value={armCm}
                    onChange={(e) => setArmCm(e.target.value)}
                  />
                </div>
              </div>
              <div className="progress-page__field">
                <label className="field-label" htmlFor="progressNotes">
                  Notas (opcional)
                </label>
                <input
                  id="progressNotes"
                  className="input"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Ej. mejora de postura, molestia en rodilla…"
                />
              </div>
              <div className="progress-page__form-actions">
                <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Guardando…' : 'Guardar registro'}
                </button>
              </div>
            </form>
          )}

          {recordsLoading ? (
            <div className="card">
              <LoadingState label="Cargando progreso…" variant="skeleton" rows={4} />
            </div>
          ) : recordsError ? (
            <ErrorMessage message={recordsError} onRetry={() => loadRecords(selectedClientId)} />
          ) : !records || records.length === 0 ? (
            <div className="card">
              <EmptyState
                title="Sin registros de progreso corporal"
                description={
                  isStaff
                    ? `${selectedClient?.full_name ?? 'Este cliente'} todavía no tiene registros -- usa "+ Registrar progreso" para agregar el primero.`
                    : 'Todavía no tienes registros de progreso corporal.'
                }
              />
            </div>
          ) : (
            <>
              <div className="progress-page__controls card">
                <div className="progress-page__metric-toggle">
                  {METRICS.map((m) => (
                    <button
                      key={m.key}
                      type="button"
                      className="progress-page__metric-btn"
                      data-active={m.key === metricKey}
                      onClick={() => setMetricKey(m.key)}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="progress-page__grid">
                <div className="card progress-page__chart-card">
                  <h2 className="section-title">{metric.label}</h2>
                  <ProgressChart points={points} unit={metric.unit} />
                </div>

                <div className="progress-page__side">
                  {latest && (
                    <div className="card">
                      <StatNumber value={latest.weight_kg} suffix="kg" label="Peso actual" />
                    </div>
                  )}
                  {latest?.height_cm != null && (
                    <div className="card">
                      <StatNumber value={latest.height_cm} suffix="cm" label="Estatura registrada" />
                    </div>
                  )}
                  {latest?.body_fat_pct != null && (
                    <div className="card">
                      <StatNumber value={latest.body_fat_pct} suffix="%" label="Grasa corporal" tone="warning" />
                    </div>
                  )}
                </div>
              </div>

              <div className="card progress-page__table-wrap">
                <table className="progress-page__table">
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
                    {[...numericRecords].reverse().map((r) => (
                      <tr key={r.id}>
                        <td>{r.record_date}</td>
                        <td>{r.weight_kg} kg</td>
                        <td>{r.body_fat_pct ?? '—'}</td>
                        <td>{r.waist_cm != null ? `${r.waist_cm} cm` : '—'}</td>
                        <td>{r.notes ?? '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
