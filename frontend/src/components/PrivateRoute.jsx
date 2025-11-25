import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/" replace />
  }

  // If user has completed onboarding fields but is on onboarding page, redirect to dashboard
  // Check if user has filled in onboarding fields (financial_goal, risk_tolerance, etc.)
  if (location.pathname === '/onboarding' && user.financial_goal && user.risk_tolerance) {
    return <Navigate to="/dashboard" replace />
  }

  // Don't force onboarding check here - onboarding is only for first-time signups
  // Existing users who haven't completed onboarding can still access the dashboard
  
  return children
}

export default PrivateRoute


