import './ProgressChart.css'

interface ProgressChartPoint {
  date: string // ISO date
  value: number
}

interface ProgressChartProps {
  points: ProgressChartPoint[]
  unit: string
  color?: string
  height?: number
}

const formatShortDate = (iso: string): string => {
  const [, month, day] = iso.split('-')
  const months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  const monthIndex = Number(month) - 1
  const monthLabel = months[monthIndex] ?? month
  return `${day}/${monthLabel}`
}

/**
 * Gráfica de evolución en SVG propio (sin librería externa) — RF011.
 * Deliberadamente simple: una sola serie, ejes mínimos, sin animaciones
 * de entrada por default (el movimiento se reserva para el hover).
 */
export function ProgressChart({ points, unit, color = 'var(--color-text)', height = 220 }: ProgressChartProps) {
  if (points.length === 0) {
    return <div className="progress-chart__empty">Sin registros de progreso todavía.</div>
  }

  const width = 640
  const paddingX = 36
  const paddingY = 28
  const values = points.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const range = max - min || 1
  const stepX = points.length > 1 ? (width - paddingX * 2) / (points.length - 1) : 0

  const coords = points.map((p, i) => {
    const x = paddingX + stepX * i
    const y = paddingY + (1 - (p.value - min) / range) * (height - paddingY * 2)
    return { x, y, ...p }
  })

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ')
  const areaPath = `${linePath} L ${coords[coords.length - 1]!.x.toFixed(1)} ${height - paddingY} L ${coords[0]!.x.toFixed(1)} ${height - paddingY} Z`

  const first = values[0]!
  const last = values[values.length - 1]!
  const delta = last - first

  return (
    <div className="progress-chart">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Evolución de ${unit}: de ${first} a ${last}`}
        className="progress-chart__svg"
      >
        <defs>
          <linearGradient id="progress-chart-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* líneas guía horizontales, discretas */}
        {[0.25, 0.5, 0.75].map((f) => (
          <line
            key={f}
            x1={paddingX}
            x2={width - paddingX}
            y1={paddingY + f * (height - paddingY * 2)}
            y2={paddingY + f * (height - paddingY * 2)}
            className="progress-chart__gridline"
          />
        ))}

        <path d={areaPath} fill="url(#progress-chart-fill)" stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />

        {coords.map((c) => (
          <g key={c.date}>
            <circle cx={c.x} cy={c.y} r={4} fill={color} stroke="var(--color-surface)" strokeWidth={2} />
            <text x={c.x} y={height - 8} textAnchor="middle" className="progress-chart__axis-label">
              {formatShortDate(c.date)}
            </text>
          </g>
        ))}
      </svg>

      <div className="progress-chart__summary">
        <div>
          <span className="progress-chart__summary-value">
            {last} {unit}
          </span>
          <span className="progress-chart__summary-label">Último registro</span>
        </div>
        <div className={`progress-chart__delta ${delta <= 0 ? 'progress-chart__delta--down' : 'progress-chart__delta--up'}`}>
          {delta > 0 ? '+' : ''}
          {delta.toFixed(1)} {unit} desde el primer registro
        </div>
      </div>
    </div>
  )
}
