import './StatNumber.css'

interface StatNumberProps {
  value: string | number
  label: string
  suffix?: string
  tone?: 'default' | 'success' | 'warning' | 'danger'
}

/**
 * El "protagonista visual" del sistema: números grandes en Permanent
 * Marker (trazo de marcador real), en blanco cálido — el tamaño y la
 * tipografía cargan la jerarquía, no el color de marca (ver theme.css,
 * nota de adaptación punto 1 y 2). Todo el resto de la UI se mantiene
 * disciplinado (Helvetica Neue, tamaños moderados) para que este elemento
 * destaque.
 */
export function StatNumber({ value, label, suffix, tone = 'default' }: StatNumberProps) {
  return (
    <div className="stat-number" data-tone={tone}>
      <div className="stat-number__value">
        {value}
        {suffix ? <span className="stat-number__suffix">{suffix}</span> : null}
      </div>
      <div className="stat-number__label">{label}</div>
    </div>
  )
}
