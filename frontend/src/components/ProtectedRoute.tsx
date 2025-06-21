import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface ProtectedRouteProps {
  children: ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, isLoading, token } = useAuth()

  console.log('ProtectedRoute render:', { user, isLoading, hasToken: !!token })

  // If still loading, show loading state
  if (isLoading) {
    console.log('ProtectedRoute: Loading...')
    return (
      <div className="loading-container">
        <div className="loading-spinner">Loading...</div>
      </div>
    )
  }

  // If no token at all, redirect to login
  if (!token) {
    console.log('ProtectedRoute: No token, redirecting to login')
    return <Navigate to="/login" replace />
  }

  // If we have a token but no user (network issue), still allow access
  // The token verification will happen in the background
  if (!user && token) {
    console.log('ProtectedRoute: Has token but no user, allowing access')
    return <>{children}</>
  }

  // If we have both token and user, allow access
  if (user && token) {
    console.log('ProtectedRoute: User authenticated, rendering children')
    return <>{children}</>
  }

  // Fallback: redirect to login
  console.log('ProtectedRoute: Fallback redirect to login')
  return <Navigate to="/login" replace />
}

export default ProtectedRoute 