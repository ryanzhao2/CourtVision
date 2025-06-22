"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { Camera, Square, BarChart3, ArrowLeft, AlertTriangle, CheckCircle } from "lucide-react"

interface LiveEvent {
  id: string
  type: string
  description: string
  timestamp: string
  severity: "info" | "warning" | "error"
}

const WebcamAnalysisPage: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false)
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [processInfo, setProcessInfo] = useState<{
    pid?: number
    message?: string
    error?: string
  } | null>(null)

  const startAnalysis = async () => {
    try {
      setIsRunning(true)
      setProcessInfo(null)
      
      // Call the backend API to launch the basketball analysis
      const response = await fetch('http://localhost:5002/api/launch-desktop-app', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const data = await response.json()
      
      if (data.success) {
        setProcessInfo({
          pid: data.pid,
          message: data.message
        })
        
        // Simulate some live events for demonstration
        simulateLiveEvents()
        
        console.log('Basketball analysis launched successfully:', data.message)
      } else {
        setProcessInfo({
          error: data.error
        })
        console.error('Failed to launch basketball analysis:', data.error)
      }
    } catch (error) {
      setProcessInfo({
        error: 'Failed to connect to backend server'
      })
      console.error('Error launching basketball analysis:', error)
    }
  }

  const stopAnalysis = async () => {
    try {
      // Call the backend API to kill the basketball analysis process
      const response = await fetch('http://localhost:5002/api/kill-desktop-app', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const data = await response.json()
      
      if (data.success) {
        console.log('Analysis stopped successfully:', data.message)
        setProcessInfo({
          message: data.message
        })
      } else {
        console.error('Failed to stop analysis:', data.error)
        setProcessInfo({
          error: data.error
        })
      }
    } catch (error) {
      console.error('Error stopping analysis:', error)
      setProcessInfo({
        error: 'Failed to connect to backend server'
      })
    }
    
    // Reset state after a short delay
    setTimeout(() => {
      setIsRunning(false)
      setProcessInfo(null)
      setLiveEvents([])
    }, 2000)
  }

  const checkAnalysisStatus = async () => {
    try {
      const response = await fetch('http://localhost:5002/api/analysis-status')
      const data = await response.json()
      
      if (data.running) {
        setIsRunning(true)
        setProcessInfo({
          pid: data.pid,
          message: data.message
        })
      } else {
        setIsRunning(false)
        setProcessInfo(null)
      }
    } catch (error) {
      console.error('Error checking analysis status:', error)
    }
  }

  // Check status on component mount
  useEffect(() => {
    checkAnalysisStatus()
  }, [])

  const simulateLiveEvents = () => {
    const events = [
      { type: "Analysis Started", description: "Basketball analysis window opened", severity: "info" as const },
      { type: "Detection Active", description: "Real-time ball and player detection running", severity: "info" as const },
      { type: "Webcam Active", description: "Backend webcam feed processing", severity: "info" as const },
      { type: "OpenCV Overlays", description: "Visual overlays and analytics displayed", severity: "info" as const },
    ]

    let eventIndex = 0
    const interval = setInterval(() => {
      if (eventIndex < events.length && isRunning) {
        const event = events[eventIndex]
        setLiveEvents((prev) => [
          ...prev,
          {
            id: Date.now().toString(),
            ...event,
            timestamp: new Date().toLocaleTimeString(),
          },
        ])
        eventIndex++
      } else {
        clearInterval(interval)
      }
    }, 1000)
  }

  const getEventIcon = (severity: string) => {
    switch (severity) {
      case "error":
        return <AlertTriangle size={16} className="text-red" />
      case "warning":
        return <AlertTriangle size={16} className="text-yellow" />
      default:
        return <CheckCircle size={16} className="text-green" />
    }
  }

  return (
    <div className="webcam-analysis-page">
      {/* Header */}
      <header className="analysis-header">
        <div className="header-left">
          <Link to="/dashboard" className="btn btn-ghost">
            <ArrowLeft size={16} />
            Back to Dashboard
          </Link>
          <div className="page-title">
            <BarChart3 size={24} />
            <span>Basketball Analysis</span>
          </div>
        </div>

        <div className="header-right">
          {isRunning && (
            <div className="recording-badge">
              <div className="pulse-dot"></div>
              Analysis Running
            </div>
          )}
        </div>
      </header>

      <main className="webcam-main">
        <div className="container">
          <div className="webcam-layout">
            {/* Video Feed */}
            <div className="video-section">
              <div className="video-card">
                <div className="video-header">
                  <Camera size={20} />
                  <h3>Basketball Analysis</h3>
                </div>
                <div className="video-container">
                  {!isRunning ? (
                    <div className="video-overlay">
                      <div className="video-placeholder">
                        <Camera size={64} className="placeholder-icon" />
                        <p>Ready to start basketball analysis</p>
                        <p className="text-sm text-gray-600 mt-2">
                          This will open a desktop window with real-time analysis using the backend webcam
                        </p>
                        <button onClick={startAnalysis} className="btn btn-primary btn-large">
                          Start Analysis
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="video-overlay">
                      <div className="video-placeholder">
                        <CheckCircle size={64} className="placeholder-icon text-green" />
                        <p>Analysis Window Active</p>
                        <p className="text-sm text-gray-600 mt-2">
                          Check your desktop for the basketball analysis window
                        </p>
                        {processInfo?.message && (
                          <p className="text-sm text-blue-600 mt-2">{processInfo.message}</p>
                        )}
                        {processInfo?.pid && (
                          <p className="text-sm text-gray-500 mt-1">Process ID: {processInfo.pid}</p>
                        )}
                        <button onClick={stopAnalysis} className="btn btn-danger btn-large">
                          <Square size={16} />
                          Stop Analysis
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {processInfo?.error && (
                  <div className="error-message">
                    <AlertTriangle size={16} />
                    <span>{processInfo.error}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Live Events */}
            <div className="events-section">
              <div className="events-card">
                <div className="events-header">
                  <h3>Analysis Status</h3>
                </div>
                <div className="events-list">
                  {liveEvents.length === 0 ? (
                    <p className="events-placeholder">
                      {isRunning ? "Starting analysis..." : "Start analysis to see status updates"}
                    </p>
                  ) : (
                    liveEvents.map((event) => (
                      <div key={event.id} className={`event-item ${event.severity}`}>
                        <div className="event-content">
                          {getEventIcon(event.severity)}
                          <div className="event-details">
                            <div className="event-header">
                              <h4>{event.type}</h4>
                              <span className="event-time">{event.timestamp}</span>
                            </div>
                            <p className="event-description">{event.description}</p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Instructions */}
              <div className="stats-card">
                <div className="stats-header">
                  <h3>How to Use</h3>
                </div>
                <div className="instructions">
                  <ol>
                    <li>Click "Start Analysis" to launch the desktop app</li>
                    <li>A new window will open with real-time basketball analysis</li>
                    <li>The app uses your computer's webcam for detection</li>
                    <li>Press 'q' in the analysis window to quit</li>
                    <li>You'll see overlays, bounding boxes, and violation detection</li>
                  </ol>
                </div>
              </div>

              {/* Features */}
              <div className="stats-card">
                <div className="stats-header">
                  <h3>Features</h3>
                </div>
                <div className="features-list">
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green" />
                    <span>Real-time basketball detection</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green" />
                    <span>Player pose estimation</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green" />
                    <span>Traveling violation detection</span>
                  </div>
                  <div className="feature-item">
                    <CheckCircle size={16} className="text-green" />
                    <span>Visual overlays and analytics</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default WebcamAnalysisPage
