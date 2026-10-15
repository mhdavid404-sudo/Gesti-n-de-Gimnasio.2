import type { ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
import { useAuth } from './hooks/useAuth'
import { AuditLogsPage } from './pages/AuditLogsPage'
import { ClientDetailPage } from './pages/ClientDetailPage'
import { ClientFormPage } from './pages/ClientFormPage'
import { ClientsListPage } from './pages/ClientsListPage'
import { DashboardPage } from './pages/DashboardPage'
import { DietsPage } from './pages/DietsPage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { MembershipsPage } from './pages/MembershipsPage'
import { ProgressPage } from './pages/ProgressPage'
import { RoutinesPage } from './pages/RoutinesPage'

/** Redirige a `/login` si no hay sesión activa -- envuelve las rutas internas (`<AppShell />`). */
function RequireAuth({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/clientes" element={<ClientsListPage />} />
        <Route path="/clientes/nuevo" element={<ClientFormPage />} />
        <Route path="/clientes/:id" element={<ClientDetailPage />} />
        <Route path="/membresias" element={<MembershipsPage />} />
        <Route path="/rutinas" element={<RoutinesPage />} />
        <Route path="/dietas" element={<DietsPage />} />
        <Route path="/progreso" element={<ProgressPage />} />
        <Route path="/bitacora" element={<AuditLogsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
      {/* catch-all redirige a la landing pública, no al login */}
    </Routes>
  )
}

export default App
