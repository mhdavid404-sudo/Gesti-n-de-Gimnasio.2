import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import type { UserRole } from '../../types/models'
import { AppShellContext } from './AppShellContext'
import { IconClose, IconResults } from './icons'
import { RoleSwitcher } from './RoleSwitcher'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import './AppShell.css'

const PAGE_META: Record<string, { title: string; subtitle?: string }> = {
  '/dashboard': { title: 'Panel general', subtitle: 'Qué puedes hacer hoy, según tu rol (datos de ejemplo)' },
  '/clientes': { title: 'Clientes', subtitle: 'Padrón centralizado — reemplaza el Excel de cada turno' },
  '/clientes/nuevo': { title: 'Nuevo cliente', subtitle: 'Alta de cliente, membresía y pago inicial' },
  '/membresias': { title: 'Membresías', subtitle: 'Planes Básica, VIP y Premium' },
  '/rutinas': { title: 'Rutinas', subtitle: 'Catálogo de ejercicios y asignación a clientes' },
  '/dietas': { title: 'Dietas', subtitle: 'Planes de alimentación y asignación a clientes' },
  '/progreso': { title: 'Progreso corporal', subtitle: 'Evolución de peso y medidas por cliente' },
}

const MOCK_ROLE_STORAGE_KEY = 'smartgym:mock-role'

function isUserRole(value: string | null): value is UserRole {
  return value === 'admin' || value === 'entrenador' || value === 'cliente'
}

function readStoredMockRole(): UserRole {
  if (typeof window === 'undefined') return 'admin'
  const stored = window.localStorage.getItem(MOCK_ROLE_STORAGE_KEY)
  return isUserRole(stored) ? stored : 'admin'
}

/**
 * Layout de 3 zonas del panel interno (Entrega 2, Parte A):
 *   IZQUIERDA — Sidebar (navegación).
 *   CENTRO    — contenido de la ruta activa (Outlet), "qué puedo hacer".
 *   DERECHA   — columna "Resultados" (ver AppShellContext/useResultsPanel):
 *               solo se renderiza si la pantalla activa registró contenido;
 *               las pantallas que todavía no lo hacen ocupan el centro
 *               completo, sin romper su layout actual.
 *
 * En móvil, sidebar y columna de resultados se comportan como drawers fuera
 * de flujo (ver AppShell.css) en vez de reflow horizontal — ver
 * docs/REVISION-UX.md para el razonamiento completo.
 */
export function AppShell() {
  const location = useLocation()
  const { user } = useAuth()
  // Punto de integración documentado en RoleSwitcher.tsx: con sesión real
  // activa, el rol autenticado manda (no la anulación mock guardada de una
  // sesión anterior, que podría ser de otra cuenta) — el switch sigue
  // disponible para cambiar la vista dentro de esta sesión, solo para
  // demostrar las 3 variantes sin crear tres cuentas.
  const [mockRole, setMockRole] = useState<UserRole>(() => user?.role ?? readStoredMockRole())
  const [resultsPanel, setResultsPanel] = useState<ReactNode>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [resultsOpen, setResultsOpen] = useState(false)

  // Cierra cualquier drawer móvil abierto al cambiar de pantalla. Se ajusta
  // en el propio render (patrón recomendado por React para "resetear estado
  // cuando cambia una prop") en vez de un useEffect, para no disparar un
  // render en cascada innecesario.
  const [trackedPathname, setTrackedPathname] = useState(location.pathname)
  if (trackedPathname !== location.pathname) {
    setTrackedPathname(location.pathname)
    setSidebarOpen(false)
    setResultsOpen(false)
  }

  useEffect(() => {
    window.localStorage.setItem(MOCK_ROLE_STORAGE_KEY, mockRole)
  }, [mockRole])

  const meta =
    PAGE_META[location.pathname] ??
    (location.pathname.startsWith('/clientes/')
      ? { title: 'Detalle de cliente' }
      : { title: 'Stronger Aragón' })

  const anyDrawerOpen = sidebarOpen || resultsOpen

  return (
    <AppShellContext.Provider value={{ mockRole, setMockRole, resultsPanel, setResultsPanel }}>
      <div className="app-shell">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {anyDrawerOpen && (
          <button
            type="button"
            className="app-shell__scrim"
            aria-label="Cerrar panel"
            onClick={() => {
              setSidebarOpen(false)
              setResultsOpen(false)
            }}
          />
        )}

        <div className="app-shell__main">
          <Topbar
            title={meta.title}
            subtitle={meta.subtitle}
            onToggleSidebar={() => setSidebarOpen((v) => !v)}
            hasResults={Boolean(resultsPanel)}
            onToggleResults={() => setResultsOpen((v) => !v)}
          />

          <div className="app-shell__body">
            <div className="app-shell__content">
              <Outlet />
            </div>

            {resultsPanel && (
              <aside
                className="app-shell__results"
                data-open={resultsOpen}
                aria-label="Resultados"
              >
                <div className="app-shell__results-header">
                  <h2 className="app-shell__results-title">
                    <IconResults className="app-shell__results-icon" />
                    Resultados
                  </h2>
                  <button
                    type="button"
                    className="app-shell__results-close"
                    onClick={() => setResultsOpen(false)}
                    aria-label="Cerrar resultados"
                  >
                    <IconClose />
                  </button>
                </div>
                <div className="app-shell__results-body">{resultsPanel}</div>
              </aside>
            )}
          </div>
        </div>
      </div>

      <RoleSwitcher />
    </AppShellContext.Provider>
  )
}
