/**
 * Formas de respuesta REALES del backend (FastAPI) para endpoints ya
 * conectados — separadas de `types/models.ts` (que refleja el modelo
 * lógico de 14 entidades 1:1 con las tablas, pensado originalmente para
 * los datos mock).
 *
 * `ClientProfileRead` del backend embebe deliberadamente `email`/
 * `full_name` (del `User` dueño del perfil) y `trainer_name` (del `User`
 * entrenador) — ver `backend/src/api/v1/schemas/clients.py` y
 * DECISIONES.md, módulo Clientes (Entrega 2) — para que estas pantallas no
 * necesiten 2-3 llamadas extra a `GET /users/{id}` por fila solo para armar
 * una tabla. `types/models.ts` sigue siendo la fuente de verdad del modelo
 * de dominio puro (`ClientProfile` sin esos campos embebidos); este
 * archivo documenta dónde y por qué la respuesta real diverge de eso.
 *
 * `MembershipPlanRead.price` (módulo Memberships, ver
 * `backend/src/api/v1/schemas/memberships.py`) es un `Decimal` en el
 * backend -- Pydantic v2 lo serializa a JSON como STRING (ej. `"399.00"`,
 * no `399`) para no perder precisión. Se tipa aquí como `string` a
 * propósito; todo lo que lo use en el frontend (render, sumas, formulario
 * de edición) debe pasar por `Number(...)` explícito antes de operar con
 * él -- ver `MembershipsPage.tsx`/`ClientDetailPage.tsx`.
 */

export interface ApiClientProfile {
  id: number
  user_id: number
  trainer_id: number | null
  phone: string | null
  birth_date: string | null
  address: string | null
  emergency_contact: string | null
  created_at: string
  updated_at: string
  email: string
  full_name: string
  trainer_name: string | null
}

export interface ClientRegisterPayload {
  email: string
  full_name: string
  trainer_id?: number | null
  phone?: string | null
  birth_date?: string | null
  address?: string | null
  emergency_contact?: string | null
}

export interface ClientRegisterResponse {
  client: ApiClientProfile
  temporary_password: string
}

// ---------------------------------------------------------------------------
// Memberships (RF004) — ver backend/src/api/v1/routers/memberships.py
// ---------------------------------------------------------------------------

export interface ApiMembershipPlan {
  id: number
  name: string
  /** Decimal del backend serializado como string -- ver nota de arriba. */
  price: string
  duration_days: number
  description: string | null
  benefits: string[]
  created_at: string
}

export interface MembershipPlanCreatePayload {
  name: string
  /** Se envía como number: FastAPI/Pydantic acepta int|float|str para un campo Decimal. */
  price: number
  duration_days: number
  description?: string | null
  benefits: string[]
}

export type ApiMembershipStatus = 'activa' | 'vencida' | 'cancelada' | 'pendiente'

export interface ApiMembership {
  id: number
  client_id: number
  plan_id: number
  start_date: string
  end_date: string
  status: ApiMembershipStatus
  created_at: string
}

export interface MembershipCreatePayload {
  client_id: number
  plan_id: number
  start_date: string
  end_date: string
  status?: ApiMembershipStatus
}

// ---------------------------------------------------------------------------
// Payments (RF005) — ver backend/src/api/v1/routers/payments.py
// ---------------------------------------------------------------------------

export type ApiPaymentMethod = 'efectivo' | 'tarjeta' | 'transferencia'
export type ApiPaymentStatus = 'completado' | 'pendiente' | 'rechazado'

export interface ApiPayment {
  id: number
  membership_id: number
  /** Decimal del backend serializado como string -- mismo criterio que `ApiMembershipPlan.price`. */
  amount: string
  payment_date: string
  method: ApiPaymentMethod
  status: ApiPaymentStatus
  /** Id del admin autenticado que registró el pago -- el backend lo rellena solo, nunca se manda en el body. */
  registered_by: number
  notes: string | null
  created_at: string
}

export interface PaymentCreatePayload {
  membership_id: number
  /** Se envía como number: FastAPI/Pydantic acepta int|float|str para un campo Decimal. */
  amount: number
  payment_date: string
  method: ApiPaymentMethod
  status?: ApiPaymentStatus
  notes?: string | null
}

// ---------------------------------------------------------------------------
// Notifications (RF006) — ver backend/src/api/v1/routers/notifications.py
// ---------------------------------------------------------------------------

export type ApiNotificationType =
  | 'membresia_vencida'
  | 'membresia_por_vencer'
  | 'pago_registrado'
  | 'rutina_asignada'
  | 'dieta_asignada'
  | 'sistema'

export interface ApiNotification {
  id: number
  user_id: number
  type: ApiNotificationType
  title: string
  message: string
  is_read: boolean
  created_at: string
}

// ---------------------------------------------------------------------------
// Ejercicios y Rutinas (RF007, RF008) — ver backend/src/api/v1/routers/routines.py
// ---------------------------------------------------------------------------

export interface ApiExercise {
  id: number
  name: string
  muscle_group: string | null
  description: string | null
  equipment: string | null
  created_at: string
}

export interface ExerciseCreatePayload {
  name: string
  muscle_group?: string | null
  description?: string | null
  equipment?: string | null
}

export interface ApiRoutine {
  id: number
  name: string
  /** Id del admin/entrenador autenticado que creó la rutina -- el backend lo rellena solo, nunca se manda en el body. */
  created_by: number
  description: string | null
  created_at: string
}

export interface RoutineCreatePayload {
  name: string
  description?: string | null
}

export interface ApiRoutineExercise {
  id: number
  routine_id: number
  exercise_id: number
  sets: number
  reps: number
  order_index: number
  rest_seconds: number | null
  notes: string | null
}

export interface RoutineExerciseCreatePayload {
  exercise_id: number
  sets: number
  reps: number
  order_index: number
  rest_seconds?: number | null
  notes?: string | null
}

export type ApiRoutineAssignmentStatus = 'activa' | 'completada' | 'cancelada'

export interface ApiRoutineAssignment {
  id: number
  routine_id: number
  client_id: number
  /** Id del admin/entrenador autenticado que asignó la rutina -- el backend lo rellena solo, nunca se manda en el body. */
  assigned_by: number
  assigned_date: string
  status: ApiRoutineAssignmentStatus
  notes: string | null
}

export interface RoutineAssignmentCreatePayload {
  routine_id: number
  client_id: number
  assigned_date: string
  status?: ApiRoutineAssignmentStatus
  notes?: string | null
}

export interface RoutineAssignmentUpdatePayload {
  status?: ApiRoutineAssignmentStatus
  notes?: string | null
}

// ---------------------------------------------------------------------------
// Dietas (RF009, RF012, RF013) — ver backend/src/api/v1/routers/diets.py
//
// A diferencia de Rutinas, un `DietPlan` NO tiene un catálogo de sub-items
// equivalente a `Exercise`/`RoutineExercise` -- es un plan plano con
// `calories_target` opcional, sin endpoint de "agregar item a un plan".
// ---------------------------------------------------------------------------

export interface ApiDietPlan {
  id: number
  name: string
  /** Id del admin/entrenador autenticado que creó el plan -- el backend lo rellena solo, nunca se manda en el body. */
  created_by: number
  description: string | null
  calories_target: number | null
  created_at: string
}

export interface DietPlanCreatePayload {
  name: string
  description?: string | null
  calories_target?: number | null
}

export type ApiDietAssignmentStatus = 'activa' | 'completada' | 'cancelada'

export interface ApiDietAssignment {
  id: number
  diet_plan_id: number
  client_id: number
  /** Id del admin/entrenador autenticado que asignó el plan -- el backend lo rellena solo, nunca se manda en el body. */
  assigned_by: number
  assigned_date: string
  status: ApiDietAssignmentStatus
  notes: string | null
}

export interface DietAssignmentCreatePayload {
  diet_plan_id: number
  client_id: number
  assigned_date: string
  status?: ApiDietAssignmentStatus
  notes?: string | null
}

export interface DietAssignmentUpdatePayload {
  status?: ApiDietAssignmentStatus
  notes?: string | null
}

// ---------------------------------------------------------------------------
// Progreso Corporal (RF010, RF011) — ver backend/src/api/v1/routers/progress.py
//
// Sin campo de autoría (a diferencia de Payment/Routine/Diet): BodyProgress
// solo liga peso/medidas/fecha a un client_id, nunca tuvo un
// created_by/registered_by que corregir.
// ---------------------------------------------------------------------------

export interface ApiBodyProgress {
  id: number
  client_id: number
  record_date: string
  /** Decimal del backend serializado como string -- mismo criterio que ApiMembershipPlan.price. */
  weight_kg: string
  height_cm: string | null
  body_fat_pct: string | null
  muscle_mass_kg: string | null
  chest_cm: string | null
  waist_cm: string | null
  hip_cm: string | null
  arm_cm: string | null
  notes: string | null
}

export interface BodyProgressCreatePayload {
  client_id: number
  record_date: string
  /** Se envía como number: FastAPI/Pydantic acepta int|float|str para un campo Decimal. */
  weight_kg: number
  height_cm?: number | null
  body_fat_pct?: number | null
  muscle_mass_kg?: number | null
  chest_cm?: number | null
  waist_cm?: number | null
  hip_cm?: number | null
  arm_cm?: number | null
  notes?: string | null
}
