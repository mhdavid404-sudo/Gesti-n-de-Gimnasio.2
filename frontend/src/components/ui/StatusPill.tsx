import type { AssignmentStatus, PaymentStatus } from '../../types/models'
import type { MembershipDisplayStatus } from '../../utils/membership'
import './StatusPill.css'

/**
 * `MembershipDisplayStatus` ya incluye `por_vencer` como valor calculado
 * (no persistido) — ver `utils/membership.ts` y DECISIONES.md, arbitraje del
 * 2026-09-12.
 */
type Status = MembershipDisplayStatus | AssignmentStatus | PaymentStatus | 'sin_membresia'

const LABELS: Record<Status, string> = {
  activa: 'Activa',
  por_vencer: 'Por vencer',
  vencida: 'Vencida',
  cancelada: 'Cancelada',
  pendiente: 'Pendiente',
  completada: 'Completada',
  completado: 'Completado',
  rechazado: 'Rechazado',
  sin_membresia: 'Sin membresía',
}

const TONES: Record<Status, 'success' | 'warning' | 'danger' | 'neutral'> = {
  activa: 'success',
  por_vencer: 'warning',
  vencida: 'danger',
  cancelada: 'neutral',
  pendiente: 'warning',
  completada: 'success',
  completado: 'success',
  rechazado: 'danger',
  sin_membresia: 'neutral',
}

export function StatusPill({ status }: { status: Status }) {
  return (
    <span className="status-pill" data-tone={TONES[status]}>
      <span className="status-pill__dot" />
      {LABELS[status]}
    </span>
  )
}
