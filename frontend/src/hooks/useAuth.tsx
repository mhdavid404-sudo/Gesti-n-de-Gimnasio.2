/**
 * Contexto de autenticación: sesión en memoria + `localStorage` (ver
 * `api/authStorage.ts` para la clave y la forma persistida).
 *
 * `AuthProvider` debe envolver las rutas de la app (ver `main.tsx`).
 * `useAuth()` expone `login`, `logout`, `user`, `isAuthenticated` a
 * cualquier componente dentro del provider.
 */
import { createContext, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { AuthUser } from '../api/authStorage'
import { clearStoredAuth, readStoredAuth, writeStoredAuth } from '../api/authStorage'
import { apiFetch } from '../api/client'

interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

interface AuthContextValue {
  user: AuthUser | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => readStoredAuth()?.user ?? null)

  const login = async (email: string, password: string): Promise<void> => {
    const response = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    })
    writeStoredAuth({ token: response.access_token, user: response.user })
    setUser(response.user)
  }

  const logout = (): void => {
    clearStoredAuth()
    setUser(null)
  }

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, login, logout }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth debe usarse dentro de <AuthProvider>.')
  }
  return context
}
