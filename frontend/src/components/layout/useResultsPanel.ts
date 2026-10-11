import { useEffect } from 'react'
import type { DependencyList, ReactNode } from 'react'
import { useAppShell } from './AppShellContext'

/**
 * Registra el contenido de la columna "Resultados" (zona derecha del layout
 * de 3 zonas, ver AppShell.tsx) mientras la pantalla que llama este hook
 * esté montada. Al desmontarse — por ejemplo, al navegar a otra pantalla que
 * todavía no construye su propia zona de resultados — limpia la columna
 * automáticamente, así esas pantallas simplemente no la muestran en vez de
 * quedarse con contenido obsoleto de la pantalla anterior.
 *
 * Firma igual a `useEffect`/`useMemo` (fábrica + `deps` explícito) a
 * propósito: un `ReactNode` ya construido es una referencia nueva en CADA
 * render, así que usarlo directo como dependencia de un efecto reinscribe el
 * contenido en cada render → el estado sube a `AppShell` → `AppShell`
 * re-renderiza su árbol → esta pantalla vuelve a renderizar → nueva
 * referencia → loop infinito ("Maximum update depth exceeded"). Exigir
 * `deps` en la llamada (valores primitivos o referencias ya estables, no el
 * JSX en sí) es lo que rompe el ciclo.
 *
 * No vive en `src/hooks/` a propósito: esa carpeta está reservada para el
 * trabajo de autenticación (`useAuth.tsx`).
 */
export function useResultsPanel(factory: () => ReactNode, deps: DependencyList): void {
  const { setResultsPanel } = useAppShell()

  useEffect(() => {
    setResultsPanel(factory())
    return () => setResultsPanel(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
