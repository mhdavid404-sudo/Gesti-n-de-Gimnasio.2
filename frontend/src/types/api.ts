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
