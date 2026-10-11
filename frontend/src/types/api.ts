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
