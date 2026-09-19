/**
 * Modelo de datos del frontend — SmartGym v2 / Stronger Aragón
 *
 * Estos tipos reflejan 1:1 el modelo lógico de 13 entidades aprobado por
 * Isai en `DECISIONES.md` (raíz del repo, sección "2026-09-12 — Modelo de
 * datos y estructura hexagonal para Entrega 1").
 *
 * Reglas heredadas de esa decisión (NO cambiar sin actualizar DECISIONES.md):
 * - Los campos tipo `role` / `status` / `method` / `type` son VARCHAR + CHECK
 *   en Postgres (no ENUM nativo) -> aquí se modelan como *string literal
 *   unions*, que es el equivalente de TypeScript a un CHECK constraint.
 * - `trainer_id` es FK 1:n simple en `ClientProfile` (no hay tabla puente
 *   entrenador<->cliente).
 * - `password_hash` existe en `User` desde ya, aunque el login funcional no
 *   se implementa en Entrega 1 (la pantalla de Login es solo UI).
 * - `height_cm` vive en `BodyProgress`, NO en `ClientProfile` (punto menor
 *   confirmado en DECISIONES.md, no mover por criterio propio).
 *
 * En Entrega 2, cuando exista la API real, estos mismos tipos deberían poder
 * usarse casi sin cambios contra las respuestas del backend (swap de fuente
 * de datos, no reescritura de pantallas).
 */

// ---------------------------------------------------------------------------
// Enums modelados como VARCHAR + CHECK (string literal unions)
// ---------------------------------------------------------------------------

/** Roles diferenciados de RF001/RF002. */
export type UserRole = 'admin' | 'entrenador' | 'cliente'

/**
 * Estado de una membresía. Alimenta RF006 (detección de vencidas / por vencer).
 * "Por vencer" NO es un valor de este enum: es un cálculo derivado de
 * `end_date` vs. la fecha actual (ver `isMembershipExpiringSoon` en
 * `src/utils/membership.ts`), no un estado persistido — ver DECISIONES.md,
 * arbitraje del 2026-09-12.
 */
export type MembershipStatus = 'activa' | 'vencida' | 'cancelada' | 'pendiente'

/** Método de pago registrado en RF005. */
export type PaymentMethod = 'efectivo' | 'tarjeta' | 'transferencia'

/** Estado de un pago (RF005). */
export type PaymentStatus = 'completado' | 'pendiente' | 'rechazado'

/** Estado de una asignación de rutina o dieta a un cliente (RF007-RF009). */
export type AssignmentStatus = 'activa' | 'completada' | 'cancelada'

/** Tipo de notificación (RF006). */
export type NotificationType =
  | 'membresia_por_vencer'
  | 'membresia_vencida'
  | 'pago_registrado'
  | 'rutina_asignada'
  | 'dieta_asignada'
  | 'sistema'

/** Nombre de plan de membresía (RF004). Igual que status, VARCHAR + CHECK. */
export type MembershipPlanName = 'Básica' | 'VIP' | 'Premium'

// ---------------------------------------------------------------------------
// 1. User — cuenta de acceso con rol (admin / entrenador / cliente)
// ---------------------------------------------------------------------------
export interface User {
  id: number
  full_name: string
  email: string
  /** Presente desde ya en el modelo aunque el login no sea funcional todavía. */
  password_hash: string
  role: UserRole
  is_active: boolean
  created_at: string // ISO datetime
}

// ---------------------------------------------------------------------------
// 2. ClientProfile — separado de User para no arrastrar columnas de cliente
//    en cuentas de admin/entrenador (evita modelo anémico, RF003)
// ---------------------------------------------------------------------------
export interface ClientProfile {
  id: number
  /** FK -> User.id (la cuenta de acceso del cliente, role = 'cliente'). */
  user_id: number
  /** FK -> User.id (role = 'entrenador'). 1:n, nullable si aún no se asigna. */
  trainer_id: number | null
  phone: string
  birth_date: string // ISO date (YYYY-MM-DD)
  address: string
  /** Texto libre, ej. "María López - 555-1234" (ver DECISIONES.md, 2026-09-12). */
  emergency_contact: string | null
  created_at: string
}

// ---------------------------------------------------------------------------
// 3. MembershipPlan — catálogo Básica / VIP / Premium (RF004)
// ---------------------------------------------------------------------------
export interface MembershipPlan {
  id: number
  name: MembershipPlanName
  description: string
  price: number
  duration_days: number
  benefits: string[]
}

// ---------------------------------------------------------------------------
// 4. Membership — membresía concreta asignada a un cliente (RF004, RF006)
// ---------------------------------------------------------------------------
export interface Membership {
  id: number
  client_id: number // FK -> ClientProfile.id
  plan_id: number // FK -> MembershipPlan.id
  start_date: string // ISO date
  end_date: string // ISO date
  status: MembershipStatus
  created_at: string
}

// ---------------------------------------------------------------------------
// 5. Payment — pago asociado a una membresía (RF005)
// ---------------------------------------------------------------------------
export interface Payment {
  id: number
  membership_id: number // FK -> Membership.id
  amount: number
  payment_date: string // ISO date
  method: PaymentMethod
  status: PaymentStatus
  registered_by: number // FK -> User.id (quien lo registró)
  notes: string | null
}

// ---------------------------------------------------------------------------
// 6. Exercise — catálogo reutilizable de ejercicios
// ---------------------------------------------------------------------------
export interface Exercise {
  id: number
  name: string
  muscle_group: string
  equipment: string | null
  description: string
}

// ---------------------------------------------------------------------------
// 7. Routine — rutina creada por entrenador/admin (RF007)
// ---------------------------------------------------------------------------
export interface Routine {
  id: number
  name: string
  description: string
  created_by: number // FK -> User.id (invariante: debe ser entrenador o admin)
  created_at: string
}

// ---------------------------------------------------------------------------
// 8. RoutineExercise — tabla puente Routine <-> Exercise (RF008)
// ---------------------------------------------------------------------------
export interface RoutineExercise {
  id: number
  routine_id: number // FK -> Routine.id
  exercise_id: number // FK -> Exercise.id
  sets: number
  reps: number
  rest_seconds: number
  order: number
  notes: string | null
}

// ---------------------------------------------------------------------------
// 9. RoutineAssignment — asignación de una rutina a un cliente (RF007/RF008)
// ---------------------------------------------------------------------------
export interface RoutineAssignment {
  id: number
  routine_id: number // FK -> Routine.id
  client_id: number // FK -> ClientProfile.id
  assigned_by: number // FK -> User.id
  assigned_date: string // ISO date
  status: AssignmentStatus
  notes: string | null
}

// ---------------------------------------------------------------------------
// 10. DietPlan — plan de dieta creado por entrenador/admin (RF009)
// ---------------------------------------------------------------------------
export interface DietPlan {
  id: number
  name: string
  description: string
  daily_calories: number | null
  created_by: number // FK -> User.id
  created_at: string
}

// ---------------------------------------------------------------------------
// 11. DietAssignment — asignación de un plan de dieta a un cliente (RF009)
// ---------------------------------------------------------------------------
export interface DietAssignment {
  id: number
  diet_plan_id: number // FK -> DietPlan.id
  client_id: number // FK -> ClientProfile.id
  assigned_by: number // FK -> User.id
  assigned_date: string // ISO date
  status: AssignmentStatus
  notes: string | null
}

// ---------------------------------------------------------------------------
// 12. BodyProgress — registro de progreso corporal (RF010, RF011)
//     height_cm vive aquí, no en ClientProfile (ver DECISIONES.md).
// ---------------------------------------------------------------------------
export interface BodyProgress {
  id: number
  client_id: number // FK -> ClientProfile.id
  record_date: string // ISO date
  weight_kg: number
  height_cm: number
  body_fat_pct: number | null
  muscle_mass_kg: number | null
  chest_cm: number | null
  waist_cm: number | null
  hip_cm: number | null
  arm_cm: number | null
  notes: string | null
}

// ---------------------------------------------------------------------------
// 13. Notification — RF006 (vencimientos) y otros eventos relevantes
// ---------------------------------------------------------------------------
export interface Notification {
  id: number
  user_id: number // FK -> User.id (destinatario)
  type: NotificationType
  message: string
  is_read: boolean
  created_at: string
}

// ---------------------------------------------------------------------------
// 14. AuditLog — bitácora de eventos del sistema (RF015)
// ---------------------------------------------------------------------------
export interface AuditLog {
  id: number
  user_id: number | null // FK -> User.id (null si fue el propio sistema)
  action: string
  entity_type: string
  entity_id: number | null
  details: string | null
  created_at: string
}
