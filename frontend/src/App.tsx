import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Header } from './components/Header'
import { Dashboard } from './components/Dashboard'
import { IncidentsPage } from './components/IncidentsPage'
import { ReportsPage } from './components/ReportsPage'
import { MemoryPage } from './components/MemoryPage'
import { SettingsPage } from './components/SettingsPage'
import { AdminPage } from './components/AdminPage'
import { IntegrationsPage } from './components/IntegrationsPage'

const TAB_TO_PATH: Record<string, string> = {
  Dashboard: '/',
  Incidents: '/incidents',
  Reports: '/reports',
  Memory: '/memory',
  Settings: '/settings',
  Admin: '/admin',
}

const PATH_TO_TAB: Record<string, string> = {
  '/': 'Dashboard',
  '/incidents': 'Incidents',
  '/reports': 'Reports',
  '/memory': 'Memory',
  '/integrations': 'Integrations',
  '/settings': 'Settings',
  '/admin': 'Admin',
}

function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const activeTab = PATH_TO_TAB[location.pathname] ?? 'Dashboard'

  function handleTabChange(tab: string) {
    navigate(TAB_TO_PATH[tab] ?? '/')
  }

  return (
    <div className="min-h-screen pb-16">
      <Header activeTab={activeTab} onTabChange={handleTabChange} />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/memory" element={<MemoryPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}

export default App
