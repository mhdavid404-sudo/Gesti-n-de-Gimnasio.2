/**
 * Persistencia de la sesión de autenticación en `localStorage`.
 *
 * Separado de `client.ts` y de `hooks/useAuth.tsx` para que ambos puedan
 * leer/escribir la misma clave sin que uno dependa del otro: `client.ts`
 * necesita el token guardado para armar el header `Authorization` en cada
 * request, y `useAuth.tsx` necesita `client.ts` para llamar `POST
 * /auth/login` -- si `client.ts` importara `useAuth.tsx` para leer el
 * token, se formaría un import circular.
 */
import type { UserRole } from '../types/models'

/** Clave propia del proyecto, no genérica ("token", "auth"), para evitar colisiones. */
export const AUTH_STORAGE_KEY = 'smartgym_auth'

/** Forma que devuelve el backend en `UserRead` (sin `password_hash`). */
export interface AuthUser {
  id: number
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface StoredAuth {
  token: string
  user: AuthUser
}

export function readStoredAuth(): StoredAuth | null {
  const raw = localStorage.getItem(AUTH_STORAGE_KEY)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as StoredAuth
    if (!parsed?.token || !parsed?.user) return null
    return parsed
  } catch {
    return null
  }
}

export function writeStoredAuth(auth: StoredAuth): void {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth))
}

export function clearStoredAuth(): void {
  localStorage.removeItem(AUTH_STORAGE_KEY)
}
