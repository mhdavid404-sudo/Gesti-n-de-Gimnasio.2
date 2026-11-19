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

/**
 * Criterio compartido para elegir "la" membresía a mostrar cuando un
 * cliente tiene más de una (módulo Memberships, Entrega 2, datos reales de
 * la API — `GET /memberships` puede devolver historial completo, no solo
 * la vigente): se prefiere la que esté `activa`; si no hay ninguna activa,
 * se toma la de `end_date` más lejana (la más reciente/relevante del
 * historial). Usado por `ClientsListPage.tsx` (columna Plan/Membresía) y
 * `ClientDetailPage.tsx` (header + pestaña Membresía) para no duplicar el
 * criterio en dos lugares.
 */
export function pickCurrentMembership<T extends { status: string; end_date: string }>(
  memberships: T[],
): T | undefined {
  if (memberships.length === 0) return undefined
  const activa = memberships.find((m) => m.status === 'activa')
  if (activa) return activa
  return [...memberships].sort((a, b) => b.end_date.localeCompare(a.end_date))[0]
}

/**
 * Suma `days` (días naturales) a una fecha ISO (YYYY-MM-DD) sin líos de zona
 * horaria -- usado para calcular `end_date` a partir de `duration_days` del
 * plan elegido. Centralizado aquí porque lo necesitan dos flujos distintos:
 * asignar una membresía desde el detalle del cliente (`ClientDetailPage.tsx`)
 * y darla de alta junto con el registro inicial del cliente
 * (`ClientFormPage.tsx`) -- antes vivía duplicado solo en el primero.
 */
export function addDaysIso(dateIso: string, days: number): string {
  const date = new Date(`${dateIso}T00:00:00`)
  date.setDate(date.getDate() + days)
  return date.toISOString().slice(0, 10)
}

/**
 * BUG-12 (ver DECISIONES.md): una membresía solo se puede renovar si está
 * `vencida`, o `activa` y dentro de la ventana de aviso (mismo umbral que
 * "por vencer") -- el backend (`RenewAndChargeMembershipUseCase`) es quien
 * valida esto de verdad; esta función solo sirve para decidir si el botón
 * "Renovar" se muestra habilitado o deshabilitado-con-explicación.
 */
export function canRenewMembership(
  membership: Pick<Membership, 'status' | 'end_date'>,
  referenceDate: Date = new Date(),
): boolean {
  if (membership.status === 'vencida') return true
  return isMembershipExpiringSoon(membership, referenceDate)
}

/**
 * Previsualiza el `end_date` que resultaría de renovar AHORA (mismo cálculo
 * que el backend: extiende desde `end_date` si sigue vigente, o desde
 * `todayIso` si ya venció -- nunca acumula sobre una fecha ya pasada). Solo
 * para la vista previa del diálogo de confirmación de "Renovar"; el cálculo
 * real y autoritativo ocurre en el backend.
 */
export function previewRenewedEndDate(endDateIso: string, durationDays: number, todayIso: string): string {
  const base = endDateIso >= todayIso ? endDateIso : todayIso
  return addDaysIso(base, durationDays)
}
