import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/layout/AppShell'
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

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<AppShell />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/clientes" element={<ClientsListPage />} />
        <Route path="/clientes/nuevo" element={<ClientFormPage />} />
        <Route path="/clientes/:id" element={<ClientDetailPage />} />
        <Route path="/membresias" element={<MembershipsPage />} />
        <Route path="/rutinas" element={<RoutinesPage />} />
        <Route path="/dietas" element={<DietsPage />} />
        <Route path="/progreso" element={<ProgressPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
      {/* catch-all redirige a la landing pública, no al login */}
    </Routes>
  )
}

export default App
