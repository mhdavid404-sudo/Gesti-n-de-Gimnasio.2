import { useEffect } from 'react'
import type { ReactNode } from 'react'
import { useAppShell } from './AppShellContext'

/**
 * Registra el contenido de la columna "Resultados" (zona derecha del layout
 * de 3 zonas, ver AppShell.tsx) mientras la pantalla que llama este hook
 * esté montada. Al desmontarse — por ejemplo, al navegar a otra pantalla que
 * todavía no construye su propia zona de resultados — limpia la columna
 * automáticamente, así esas pantallas simplemente no la muestran en vez de
 * quedarse con contenido obsoleto de la pantalla anterior.
 *
 * No vive en `src/hooks/` a propósito: esa carpeta está reservada para el
 * trabajo paralelo de autenticación (`useAuth.tsx`).
 */
export function useResultsPanel(content: ReactNode): void {
  const { setResultsPanel } = useAppShell()

  useEffect(() => {
    setResultsPanel(content)
    return () => setResultsPanel(null)
    // El setter de useState es estable entre renders; solo nos interesa
    // reaccionar a cambios del contenido que la pantalla quiere mostrar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content])
}
