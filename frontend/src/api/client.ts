/**
 * Wrapper de `fetch` para la API real de SmartGym v2 (backend FastAPI).
 *
 * - Base URL desde `import.meta.env.VITE_API_URL` (ver `.env.example`, raíz
 *   del repo) + el prefijo fijo `/api/v1` que monta `backend/src/api/main.py`.
 * - Agrega el header `Authorization: Bearer <token>` automáticamente si hay
 *   una sesión guardada (ver `authStorage.ts`), salvo que se pida lo
 *   contrario (`auth: false`, usado por el propio login).
 * - Si la respuesta no es 2xx, lanza `ApiError` con el `detail` en español
 *   que devuelve el backend (los routers traducen las excepciones de
 *   dominio a mensajes en español -- ver `api/v1/routers/users.py` y
 *   `routers/auth.py`).
 * - Un 401 (token inválido/expirado) limpia la sesión guardada y queda
 *   marcado en `ApiError.isUnauthorized` -- este módulo no conoce
 *   react-router, así que no navega por su cuenta; el llamador (típicamente
 *   `useAuth`, o quien use `apiFetch` directo) decide cuándo redirigir a
 *   `/login`.
 */
import { clearStoredAuth, readStoredAuth } from './authStorage'

const BASE_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const API_PREFIX = '/api/v1'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }
}

interface ApiFetchOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  body?: unknown
  /** Si es `false`, no agrega el header `Authorization` (ej. el propio login). Default `true`. */
  auth?: boolean
}

interface PydanticValidationError {
  msg?: string
}

/** Extrae `detail` del cuerpo de error del backend, con fallback genérico en español. */
async function extractErrorDetail(response: Response): Promise<string> {
  try {
    const data: unknown = await response.json()
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
      if (Array.isArray(detail)) {
        const messages = (detail as PydanticValidationError[])
          .map((item) => item.msg)
          .filter((msg): msg is string => Boolean(msg))
        if (messages.length > 0) return messages.join(' / ')
      }
    }
  } catch {
    // Respuesta sin cuerpo JSON (ej. 500 genérico sin detail) -- se usa el fallback de abajo.
  }
  return 'Ocurrió un error inesperado. Intenta de nuevo.'
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true } = options

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth) {
    const stored = readStoredAuth()
    if (stored) headers.Authorization = `Bearer ${stored.token}`
  }

  const response = await fetch(`${BASE_URL}${API_PREFIX}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!response.ok) {
    const detail = await extractErrorDetail(response)
    if (response.status === 401) {
      clearStoredAuth()
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
