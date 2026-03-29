import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/layout/Layout'
import LoginPage from './pages/LoginPage'
import { MainSummaryPage } from './pages/MainSummaryPage'
import { LiveDataPage } from './pages/LiveDataPage'
import { HistoricalDataPage } from './pages/HistoricalDataPage'
import { DeviceStatusPage } from './pages/DeviceStatusPage'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/summary" replace />} />
        <Route path="summary" element={<MainSummaryPage />} />
        <Route path="live" element={<LiveDataPage />} />
        <Route path="history" element={<HistoricalDataPage />} />
        <Route path="devices" element={<DeviceStatusPage />} />
      </Route>
    </Routes>
  )
}

export default App
