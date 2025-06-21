"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
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
  const [isRecording, setIsRecording] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const videoRef = useRef<HTMLVideoElement>(null)

  const startRecording = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 1280, height: 720 },
        audio: false,
      })
      setStream(mediaStream)
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream
      }
      setIsRecording(true)
      simulateLiveEvents()
    } catch (error) {
      console.error("Error accessing webcam:", error)
    }
  }

  const stopRecording = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop())
      setStream(null)
    }
    setIsRecording(false)
    setLiveEvents([])
  }

  const simulateLiveEvents = () => {
    const events = [
      { type: "Foul", description: "Personal foul detected - pushing", severity: "warning" as const },
      { type: "Violation", description: "Double dribble violation", severity: "error" as const },
      { type: "Good Play", description: "Clean steal executed", severity: "info" as const },
      { type: "Foul", description: "Traveling violation", severity: "warning" as const },
      { type: "Good Play", description: "Successful three-point shot", severity: "info" as const },
    ]

    let eventIndex = 0
    const interval = setInterval(() => {
      if (eventIndex < events.length && isRecording) {
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
    }, 3000)
  }

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [stream])

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
            <span>Live Analysis</span>
          </div>
        </div>

        <div className="header-right">
          {isRecording && (
            <div className="recording-badge">
              <div className="pulse-dot"></div>
              Recording
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
                  <h3>Live Video Feed</h3>
                </div>
                <div className="video-container">
                  <video ref={videoRef} autoPlay muted playsInline className="video-feed" />
                  {!isRecording && (
                    <div className="video-overlay">
                      <div className="video-placeholder">
                        <Camera size={64} className="placeholder-icon" />
                        <p>Ready to start live analysis</p>
                        <button onClick={startRecording} className="btn btn-primary btn-large">
                          Start Recording
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {isRecording && (
                  <div className="video-controls">
                    <button onClick={stopRecording} className="btn btn-danger btn-large">
                      <Square size={16} />
                      Stop Recording
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Live Events */}
            <div className="events-section">
              <div className="events-card">
                <div className="events-header">
                  <h3>Live Events</h3>
                </div>
                <div className="events-list">
                  {liveEvents.length === 0 ? (
                    <p className="events-placeholder">
                      {isRecording ? "Analyzing... Events will appear here" : "Start recording to see live events"}
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

              {/* Stats */}
              <div className="stats-card">
                <div className="stats-header">
                  <h3>Session Stats</h3>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className="stat-value error">{liveEvents.filter((e) => e.severity === "error").length}</div>
                    <div className="stat-label">Violations</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value warning">
                      {liveEvents.filter((e) => e.severity === "warning").length}
                    </div>
                    <div className="stat-label">Fouls</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value info">{liveEvents.filter((e) => e.severity === "info").length}</div>
                    <div className="stat-label">Good Plays</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value total">{liveEvents.length}</div>
                    <div className="stat-label">Total Events</div>
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
