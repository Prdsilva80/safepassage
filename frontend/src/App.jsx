import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './context/AuthContext'
import Navbar from './components/Navbar'
import Login from './pages/Login'
import Register from './pages/Register'
import MapPage from './pages/MapPage'
import CivilPage from './pages/civil/CivilPage'
import AdminDashboard from './pages/admin/AdminDashboard'
import SheltersAdmin from './pages/admin/SheltersAdmin'
import ContactsPage from './pages/ContactsPage'

const queryClient = new QueryClient()

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()
  if (loading) return <div style={{ padding: 40, color: 'var(--text2)', fontFamily: 'var(--mono)', textAlign: 'center' }}>LOADING...</div>
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && user.role !== 'admin' && user.role !== 'ngo_worker') return <Navigate to="/map" replace />
  return children
}

function Layout({ children }) {
  return <><Navbar />{children}</>
}

function AppRoutes() {
  const { user } = useAuth()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/map" element={<ProtectedRoute><Layout><MapPage /></Layout></ProtectedRoute>} />
      <Route path="/civil" element={<ProtectedRoute><Layout><CivilPage /></Layout></ProtectedRoute>} />
      <Route path="/admin" element={<ProtectedRoute adminOnly><Layout><AdminDashboard /></Layout></ProtectedRoute>} />
      <Route path="/admin/sos" element={<ProtectedRoute adminOnly><Layout><AdminDashboard /></Layout></ProtectedRoute>} />
      <Route path="/admin/shelters" element={<ProtectedRoute adminOnly><Layout><SheltersAdmin /></Layout></ProtectedRoute>} />
      <Route path="/" element={<Navigate to={user ? "/map" : "/login"} replace />} />
      <Route path="/contacts" element={<ProtectedRoute><Layout><ContactsPage /></Layout></ProtectedRoute>} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <Toaster position="bottom-right" toastOptions={{
            style: { background: 'var(--bg2)', color: 'var(--text)', border: '1px solid var(--border)' }
          }} />
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
