import { createContext, useContext } from 'react'
import type { Dispatch, ReactNode, SetStateAction } from 'react'
import type { UserRole } from '../../types/models'

/**
 * Contexto compartido del panel interno.
 *
 * Conecta dos piezas del layout de 3 zonas (ver AppShell.tsx) con cualquier
 * pantalla que viva dentro de <AppShell>:
 *   - `mockRole` / `setMockRole`: el rol seleccionado en el switch de
 *     desarrollo (ver RoleSwitcher.tsx). Es deliberadamente mock — el
 *     proceso de autenticación real (JWT) que se construye en paralelo
 *     reemplazará esto por el rol de la sesión real. El punto de integración
 *     es exactamente este valor: cuando exista `useAuth()`, basta inicializar
 *     `mockRole` desde el usuario autenticado en vez de localStorage (ver
 *     RoleSwitcher.tsx para el detalle).
 *   - `resultsPanel` / `setResultsPanel`: el contenido actual de la columna
 *     "Resultados" (zona derecha). Las pantallas lo fijan con el hook
 *     `useResultsPanel` (ver useResultsPanel.ts); si ninguna pantalla lo usa,
 *     la columna no se renderiza y el contenido central ocupa todo el ancho.
 */
export interface AppShellContextValue {
  mockRole: UserRole
  setMockRole: Dispatch<SetStateAction<UserRole>>
  resultsPanel: ReactNode
  setResultsPanel: Dispatch<SetStateAction<ReactNode>>
}

export const AppShellContext = createContext<AppShellContextValue | null>(null)

export function useAppShell(): AppShellContextValue {
  const ctx = useContext(AppShellContext)
  if (!ctx) {
    throw new Error('useAppShell debe usarse dentro de <AppShell> (components/layout/AppShell.tsx)')
  }
  return ctx
}
