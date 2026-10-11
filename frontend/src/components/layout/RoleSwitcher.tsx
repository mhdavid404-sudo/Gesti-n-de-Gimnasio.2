import type { UserRole } from '../../types/models'
import { useAppShell } from './AppShellContext'
import './RoleSwitcher.css'

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: 'admin', label: 'Admin' },
  { value: 'entrenador', label: 'Entrenador' },
  { value: 'cliente', label: 'Cliente' },
]

/**
 * Selector de rol MOCK — herramienta de desarrollo, no de producto.
 *
 * El rol real de sesión lo va a conectar el trabajo de autenticación (JWT)
 * que se construye en paralelo a esta tarea. Mientras ese trabajo no está
 * integrado aquí, este switch deja probar las 3 variantes de la zona
 * "Qué puedo hacer" del Dashboard (ver DashboardPage.tsx) sin necesitar un
 * login real por rol.
 *
 * Punto de integración para quien conecte el rol real: reemplazar la
 * inicialización de `mockRole` en AppShell.tsx (hoy lee localStorage) por el
 * rol del usuario autenticado, y retirar este componente del árbol.
 */
export function RoleSwitcher() {
  const { mockRole, setMockRole } = useAppShell()

  return (
    <div className="role-switcher" role="group" aria-label="Selector de rol (solo desarrollo)">
      <span className="role-switcher__tag">Vista de prueba · dev</span>
      <div className="role-switcher__options">
        {ROLE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            type="button"
            className="role-switcher__option"
            data-active={opt.value === mockRole}
            onClick={() => setMockRole(opt.value)}
            aria-pressed={opt.value === mockRole}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}
