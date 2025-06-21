"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Volume2,
  Maximize,
  BarChart3,
  ArrowLeft,
  AlertTriangle,
  CheckCircle,
  Info,
} from "lucide-react"

interface AnalysisEvent {
  id: string
  timestamp: number
  type: string
  title: string
  description: string
  severity: "info" | "warning" | "error"
}

const AnalysisResultsPage: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration] = useState(930) // 15:30 in seconds
  const [volume, setVolume] = useState(50)
  const [hoveredEvent, setHoveredEvent] = useState<AnalysisEvent | null>(null)

  const analysisEvents: AnalysisEvent[] = [
    {
      id: "1",
      timestamp: 45,
      type: "Foul",
      title: "Personal Foul",
      description: "Pushing foul committed by Player #23",
      severity: "warning",
    },
    {
      id: "2",
      timestamp: 128,
      type: "Violation",
      title: "Double Dribble",
      description: "Player #15 committed a double dribble violation",
      severity: "error",
    },
    {
      id: "3",
      timestamp: 245,
      type: "Good Play",
      title: "Steal",
      description: "Clean steal executed by Player #8",
      severity: "info",
    },
    {
      id: "4",
      timestamp: 367,
      type: "Foul",
      title: "Traveling",
      description: "Traveling violation by Player #12",
      severity: "warning",
    },
    {
      id: "5",
      timestamp: 456,
      type: "Good Play",
      title: "Three-Point Shot",
      description: "Successful three-point shot by Player #7",
      severity: "info",
    },
    {
      id: "6",
      timestamp: 589,
      type: "Violation",
      title: "Out of Bounds",
      description: "Ball went out of bounds, turnover",
      severity: "error",
    },
    {
      id: "7",
      timestamp: 723,
      type: "Good Play",
      title: "Assist",
      description: "Great assist leading to a score",
      severity: "info",
    },
    {
      id: "8",
      timestamp: 834,
      type: "Foul",
      title: "Blocking Foul",
      description: "Illegal blocking foul by Player #19",
      severity: "warning",
    },
  ]

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying)
  }

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentTime(Number.parseInt(e.target.value))
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setVolume(Number.parseInt(e.target.value))
  }

  const jumpToEvent = (timestamp: number) => {
    setCurrentTime(timestamp)
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
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

  // Simulate video playback
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>
    if (isPlaying) {
      interval = setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= duration) {
            setIsPlaying(false)
            return duration
          }
          return prev + 1
        })
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isPlaying, duration])

  return (
    <div className="results-page">
      {/* Header */}
      <header className="analysis-header">
        <div className="header-left">
          <Link to="/dashboard" className="btn btn-ghost">
            <ArrowLeft size={16} />
            Back to Dashboard
          </Link>
          <div className="page-title">
            <BarChart3 size={24} />
            <span>Analysis Results</span>
          </div>
        </div>

        <div className="header-right">
          <div className="status-badge complete">Analysis Complete</div>
        </div>
      </header>

      <main className="results-main">
        <div className="container">
          <div className="results-layout">
            {/* Video Player */}
            <div className="video-section">
              <div className="video-player-card">
                <div className="video-player">
                  <div className="video-container">
                    <img
                      src="https://images.unsplash.com/photo-1546519638-68e109498ffc?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&h=450"
                      alt="Basketball game analysis"
                      className="video-placeholder"
                    />

                    {/* Video Controls Overlay */}
                    <div className="video-controls-overlay">
                      {/* Progress Bar with Event Markers */}
                      <div className="progress-container">
                        <input
                          type="range"
                          min="0"
                          max={duration}
                          value={currentTime}
                          onChange={handleTimeChange}
                          className="progress-slider"
                        />

                        {/* Event Markers */}
                        {analysisEvents.map((event) => (
                          <div
                            key={event.id}
                            className={`event-marker ${event.severity}`}
                            style={{ left: `${(event.timestamp / duration) * 100}%` }}
                            onMouseEnter={() => setHoveredEvent(event)}
                            onMouseLeave={() => setHoveredEvent(null)}
                            onClick={() => jumpToEvent(event.timestamp)}
                          >
                            {/* Tooltip */}
                            {hoveredEvent?.id === event.id && (
                              <div className="event-tooltip">
                                <div className="tooltip-header">
                                  {getEventIcon(event.severity)}
                                  <span>{event.title}</span>
                                </div>
                                <p>{event.description}</p>
                                <small>{formatTime(event.timestamp)}</small>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>

                      {/* Control Buttons */}
                      <div className="video-controls">
                        <button onClick={togglePlayPause} className="control-btn">
                          {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                        </button>

                        <button className="control-btn">
                          <SkipBack size={16} />
                        </button>

                        <button className="control-btn">
                          <SkipForward size={16} />
                        </button>

                        <div className="volume-control">
                          <Volume2 size={16} />
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={volume}
                            onChange={handleVolumeChange}
                            className="volume-slider"
                          />
                        </div>

                        <div className="time-display">
                          {formatTime(currentTime)} / {formatTime(duration)}
                        </div>

                        <button className="control-btn ml-auto">
                          <Maximize size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Summary Stats */}
              <div className="summary-card">
                <div className="summary-header">
                  <h3>Analysis Summary</h3>
                </div>
                <div className="summary-stats">
                  <div className="stat-item">
                    <div className="stat-value error">
                      {analysisEvents.filter((e) => e.severity === "error").length}
                    </div>
                    <div className="stat-label">Violations</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value warning">
                      {analysisEvents.filter((e) => e.severity === "warning").length}
                    </div>
                    <div className="stat-label">Fouls</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value info">{analysisEvents.filter((e) => e.severity === "info").length}</div>
                    <div className="stat-label">Good Plays</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value total">{analysisEvents.length}</div>
                    <div className="stat-label">Total Events</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Events Timeline */}
            <div className="timeline-section">
              <div className="timeline-card">
                <div className="timeline-header">
                  <h3>Event Timeline</h3>
                </div>
                <div className="timeline-events">
                  {analysisEvents.map((event) => (
                    <div
                      key={event.id}
                      className={`timeline-event ${event.severity}`}
                      onClick={() => jumpToEvent(event.timestamp)}
                    >
                      <div className="event-content">
                        {getEventIcon(event.severity)}
                        <div className="event-details">
                          <div className="event-header">
                            <h4>{event.title}</h4>
                            <span className="event-time">{formatTime(event.timestamp)}</span>
                          </div>
                          <p className="event-description">{event.description}</p>
                          <div className="event-type">{event.type}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Export Options */}
              <div className="export-card">
                <div className="export-header">
                  <h3>Export Analysis</h3>
                </div>
                <div className="export-options">
                  <button className="export-btn">
                    <Info size={16} />
                    Download Report (PDF)
                  </button>
                  <button className="export-btn">
                    <BarChart3 size={16} />
                    Export Data (CSV)
                  </button>
                  <button className="export-btn">
                    <Play size={16} />
                    Share Analysis
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AnalysisResultsPage
