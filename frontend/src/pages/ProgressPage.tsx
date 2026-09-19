import { useMemo, useState } from 'react'
import { ProgressChart } from '../components/ui/ProgressChart'
import { StatNumber } from '../components/ui/StatNumber'
import { bodyProgress, getBodyProgressForClient, getClientDisplayName } from '../mocks/data'
import type { BodyProgress } from '../types/models'
import './ProgressPage.css'

type MetricKey = 'weight_kg' | 'body_fat_pct' | 'waist_cm'

const METRICS: { key: MetricKey; label: string; unit: string }[] = [
  { key: 'weight_kg', label: 'Peso', unit: 'kg' },
  { key: 'body_fat_pct', label: '% de grasa corporal', unit: '%' },
  { key: 'waist_cm', label: 'Cintura', unit: 'cm' },
]

const clientIdsWithProgress = Array.from(new Set(bodyProgress.map((p) => p.client_id)))

export function ProgressPage() {
  const [clientId, setClientId] = useState<number>(clientIdsWithProgress[0] ?? 0)
  const [metricKey, setMetricKey] = useState<MetricKey>('weight_kg')

  const records = useMemo(() => getBodyProgressForClient(clientId), [clientId])
  const metric = METRICS.find((m) => m.key === metricKey)!

  const points = records
    .filter((r) => r[metricKey] !== null)
    .map((r) => ({ date: r.record_date, value: r[metricKey] as number }))

  const latest: BodyProgress | undefined = records[records.length - 1]

  return (
    <div className="progress-page">
      <div className="progress-page__controls card">
        <div>
          <label className="field-label" htmlFor="progress-client">
            Cliente
          </label>
          <select
            id="progress-client"
            className="input"
            value={clientId}
            onChange={(e) => setClientId(Number(e.target.value))}
          >
            {clientIdsWithProgress.map((id) => (
              <option key={id} value={id}>
                {getClientDisplayName(id)}
              </option>
            ))}
          </select>
        </div>

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
          {latest && (
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
    </div>
  )
}
