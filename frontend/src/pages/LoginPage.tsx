"use client"

import type React from "react"
import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { BarChart3 } from "lucide-react"
import { useAuth } from "../context/AuthContext"

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const { login, isLoading, error } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const success = await login(email, password)
    if (success) {
      navigate('/dashboard')
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-header">
          <Link to="/" className="logo">
            <BarChart3 size={32} />
            <span>CourtVision</span>
          </Link>
        </div>

        <div className="auth-card">
          <div className="auth-card-header">
            <h1>Welcome back</h1>
            <p>Enter your credentials to access your account</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <div className="form-footer">
              <Link to="/forgot-password" className="forgot-link">
                Forgot password?
              </Link>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary btn-full"
              disabled={isLoading}
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>

            <div className="auth-switch">
              Don't have an account? <Link to="/signup">Sign up</Link>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
