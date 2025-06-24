"use client"

import React from "react"
import { useState } from "react"
import { Link } from "react-router-dom"
import { Camera, Upload, BarChart3, User, LogOut, History, Settings } from "lucide-react"
import { useAuth } from "../context/AuthContext"
import { useNavigate } from "react-router-dom"

const DashboardPage = () => {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  if (!user) {
    return (
      <div className="dashboard-page">
        <div className="container">
          <h1>Access Denied</h1>
          <p>Please log in to access the dashboard.</p>
          <Link to="/login" className="btn btn-primary">
            Go to Login
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-page">
      {/* Header */}
      <header className="dashboard-header">
        <Link to="/" className="logo">
          <BarChart3 size={32} />
          <span>Netly</span>
        </Link>

        <div className="header-actions">
          <div className="user-info">
            <User size={16} />
            <span>{user.firstName} {user.lastName}</span>
          </div>
          <button onClick={handleLogout} className="btn btn-ghost">
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="container">
          <div className="dashboard-welcome">
            <h1>Welcome back, {user.firstName}!</h1>
            <p>Choose how you'd like to analyze your basketball gameplay today.</p>
          </div>

          <div className="analysis-options">
            {/* Live Webcam Analysis */}
            <div className="analysis-card">
              <div className="analysis-card-header">
                <div className="analysis-icon webcam-icon">
                  <Camera size={32} />
                </div>
                <h3>Live Webcam Analysis</h3>
                <p>
                  Start a live session to get real-time analysis of your basketball gameplay with instant feedback on
                  fouls, violations, and key plays.
                </p>
              </div>
              <div className="analysis-card-content">
                <div className="feature-badge live-badge">
                  <span>Real-time processing</span>
                  <small>Get instant feedback as you play</small>
                </div>
                <Link to="/analyze/webcam" className="btn btn-primary btn-full btn-large">
                  Start Live Analysis
                </Link>
              </div>
            </div>

            {/* Video Upload Analysis */}
            <div className="analysis-card">
              <div className="analysis-card-header">
                <div className="analysis-icon upload-icon">
                  <Upload size={32} />
                </div>
                <h3>Video Upload Analysis</h3>
                <p>
                  Upload your recorded basketball footage to receive detailed timestamps and analysis of significant
                  events and plays.
                </p>
              </div>
              <div className="analysis-card-content">
                <div className="feature-badge upload-badge">
                  <span>Detailed analysis</span>
                  <small>Interactive timeline with insights</small>
                </div>
                <Link to="/analyze/upload" className="btn btn-secondary btn-full btn-large">
                  Upload Video
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default DashboardPage
