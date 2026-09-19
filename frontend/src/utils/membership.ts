/**
 * Utilidades de vencimiento de membresía.
 *
 * "Por vencer" NO es un valor de `MembershipStatus`: es un hecho relativo al
 * tiempo (`end_date` vs. la fecha actual), no un estado que se decide y
 * persiste. Persistirlo exigiría un job diario que puede desincronizarse de
 * la fecha real, duplicando la fuente de verdad — ver DECISIONES.md,
 * "2026-09-12 — Arbitraje de desalineación de modelo backend↔frontend".
 *
 * Estas funciones centralizan el cálculo para que ninguna pantalla reinvente
 * la ventana de días por su cuenta.
 */
import type { Membership } from '../types/models'

/** Ventana de anticipación para considerar una membresía activa "por vencer". */
export const EXPIRING_SOON_WINDOW_DAYS = 7

/** Días entre hoy (o `referenceDate`) y una fecha ISO (YYYY-MM-DD). Negativo si ya pasó. */
export function daysUntil(dateIso: string, referenceDate: Date = new Date()): number {
  const end = new Date(`${dateIso}T00:00:00`)
  const today = new Date(referenceDate.getFullYear(), referenceDate.getMonth(), referenceDate.getDate())
  const diffMs = end.getTime() - today.getTime()
  return Math.round(diffMs / (1000 * 60 * 60 * 24))
}

/**
 * Una membresía está "por vencer" si sigue `activa` en el backend y su
 * `end_date` cae dentro de la ventana de aviso (y todavía no pasó).
 */
export function isMembershipExpiringSoon(
  membership: Pick<Membership, 'status' | 'end_date'>,
  referenceDate: Date = new Date(),
): boolean {
  if (membership.status !== 'activa') return false
  const days = daysUntil(membership.end_date, referenceDate)
  return days >= 0 && days <= EXPIRING_SOON_WINDOW_DAYS
}

/** Estado extendido solo para presentación: agrega `por_vencer` calculado sobre `activa`. */
export type MembershipDisplayStatus = Membership['status'] | 'por_vencer'

/** Estado a mostrar en UI (badges, tablas): el persistido, salvo que esté por vencer. */
export function getMembershipDisplayStatus(
  membership: Pick<Membership, 'status' | 'end_date'>,
  referenceDate: Date = new Date(),
): MembershipDisplayStatus {
  return isMembershipExpiringSoon(membership, referenceDate) ? 'por_vencer' : membership.status
}
