"use client"

import type React from "react"
import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { BarChart3 } from "lucide-react"

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const navigate = useNavigate()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // Handle login logic here
    console.log("Login attempt:", { email, password })
    // Simulate successful login
    navigate("/dashboard")
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

            <button type="submit" className="btn btn-primary btn-full">
              Sign In
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
