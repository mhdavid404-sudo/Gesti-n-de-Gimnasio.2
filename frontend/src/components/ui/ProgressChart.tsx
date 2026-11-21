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

const formatTick = (value: number): string => (Number.isInteger(value) ? String(value) : value.toFixed(1))

/**
 * Calcula marcas "redondas" para el eje Y (estilo hoja de cálculo: 54, 56,
 * 58… en vez de los valores crudos mín/máx) — algoritmo clásico de "nice
 * numbers" para que la gráfica se lea como un plano cartesiano real.
 */
const computeNiceTicks = (min: number, max: number, tickCount = 4): { ticks: number[]; min: number; max: number } => {
  let safeMin = min
  let safeMax = max
  if (safeMin === safeMax) {
    safeMin -= 1
    safeMax += 1
  }

  const range = safeMax - safeMin
  const roughStep = range / tickCount
  const magnitude = 10 ** Math.floor(Math.log10(roughStep))
  const residual = roughStep / magnitude

  let step: number
  if (residual > 5) step = 10 * magnitude
  else if (residual > 2) step = 5 * magnitude
  else if (residual > 1) step = 2 * magnitude
  else step = magnitude

  const niceMin = Math.floor(safeMin / step) * step
  const niceMax = Math.ceil(safeMax / step) * step

  const ticks: number[] = []
  for (let v = niceMin; v <= niceMax + step / 2; v += step) {
    ticks.push(Math.round(v * 1000) / 1000)
  }

  return { ticks, min: niceMin, max: niceMax }
}

/**
 * Gráfica de evolución en SVG propio (sin librería externa) — RF011.
 * Deliberadamente simple: una sola serie, sin animaciones de entrada por
 * default (el movimiento se reserva para el hover), pero con eje Y de
 * valores redondos + líneas guía para que se lea como un plano cartesiano.
 */
export function ProgressChart({ points, unit, color = 'var(--color-text)', height = 220 }: ProgressChartProps) {
  if (points.length === 0) {
    return <div className="progress-chart__empty">Sin registros de progreso todavía.</div>
  }

  const width = 640
  const paddingLeft = 46
  const paddingRight = 16
  const paddingTop = 18
  const paddingBottom = 28
  const values = points.map((p) => p.value)
  const rawMin = Math.min(...values)
  const rawMax = Math.max(...values)
  const { ticks, min, max } = computeNiceTicks(rawMin, rawMax)
  const range = max - min || 1
  const stepX = points.length > 1 ? (width - paddingLeft - paddingRight) / (points.length - 1) : 0

  const plotHeight = height - paddingTop - paddingBottom
  const valueToY = (value: number) => paddingTop + (1 - (value - min) / range) * plotHeight

  const coords = points.map((p, i) => {
    const x = paddingLeft + stepX * i
    const y = valueToY(p.value)
    return { x, y, ...p }
  })

  const linePath = coords.map((c, i) => `${i === 0 ? 'M' : 'L'} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`).join(' ')
  const areaPath = `${linePath} L ${coords[coords.length - 1]!.x.toFixed(1)} ${height - paddingBottom} L ${coords[0]!.x.toFixed(1)} ${height - paddingBottom} Z`

  // Con muchos registros, mostrar una fecha por punto satura el eje X:
  // se muestran como máximo ~6, repartidas, siempre incluyendo la última.
  const maxXLabels = 6
  const xLabelStep = Math.max(1, Math.ceil(points.length / maxXLabels))

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

        {/* eje Y: líneas guía horizontales en valores redondos + su etiqueta numérica */}
        {ticks.map((tick) => {
          const y = valueToY(tick)
          return (
            <g key={tick}>
              <line x1={paddingLeft} x2={width - paddingRight} y1={y} y2={y} className="progress-chart__gridline" />
              <text x={paddingLeft - 8} y={y} textAnchor="end" dominantBaseline="middle" className="progress-chart__axis-label-y">
                {formatTick(tick)}
              </text>
            </g>
          )
        })}

        <path d={areaPath} fill="url(#progress-chart-fill)" stroke="none" />
        <path d={linePath} fill="none" stroke={color} strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" />

        {coords.map((c, i) => (
          <g key={c.date}>
            <circle cx={c.x} cy={c.y} r={4} fill={color} stroke="var(--color-surface)" strokeWidth={2} />
            {(i % xLabelStep === 0 || i === coords.length - 1) && (
              <text x={c.x} y={height - 8} textAnchor="middle" className="progress-chart__axis-label">
                {formatShortDate(c.date)}
              </text>
            )}
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
