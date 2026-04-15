// src/components/auth/ProtectedRoute.jsx
// Wraps any route that requires authentication.
// Redirects to /login if no valid token found.

import { Navigate, useLocation } from 'react-router-dom'
import { useAuthStore } from '../../store/useAuthStore'

export default function ProtectedRoute({ children }) {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated)
  const location        = useLocation()

  if (!isAuthenticated()) {
    // Preserve the intended URL so we can redirect back after login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return children
}
