import { Outlet, useLocation } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import './AppShell.css'

const PAGE_META: Record<string, { title: string; subtitle?: string }> = {
  '/dashboard': { title: 'Panel general', subtitle: 'Resumen del gimnasio en tiempo real (datos de ejemplo)' },
  '/clientes': { title: 'Clientes', subtitle: 'Padrón centralizado — reemplaza el Excel de cada turno' },
  '/clientes/nuevo': { title: 'Nuevo cliente', subtitle: 'Alta de cliente, membresía y pago inicial' },
  '/membresias': { title: 'Membresías', subtitle: 'Planes Básica, VIP y Premium' },
  '/rutinas': { title: 'Rutinas', subtitle: 'Catálogo de ejercicios y asignación a clientes' },
  '/dietas': { title: 'Dietas', subtitle: 'Planes de alimentación y asignación a clientes' },
  '/progreso': { title: 'Progreso corporal', subtitle: 'Evolución de peso y medidas por cliente' },
}

export function AppShell() {
  const location = useLocation()
  const meta =
    PAGE_META[location.pathname] ??
    (location.pathname.startsWith('/clientes/')
      ? { title: 'Detalle de cliente' }
      : { title: 'Stronger Aragón' })

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-shell__main">
        <Topbar title={meta.title} subtitle={meta.subtitle} />
        <div className="app-shell__content">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
