"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
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
import { useAuth } from "../context/AuthContext"

interface AnalysisEvent {
  id: string
  timestamp: number
  type: string
  title: string
  description: string
  severity: "info" | "warning" | "error"
}

interface AnalysisData {
  success: boolean
  session_id: string
  events: {
    events: Array<{
      type: string
      timestamp: number
      frame: number
      description: string
      team?: number
      player_id?: number
    }>
    summary: {
      total_events: number
      event_counts: Record<string, number>
      team_stats: Record<string, Record<string, number>>
    }
    metadata: {
      fps: number
      total_events: number
      video_duration?: number
    }
  }
  output_video_url: string
  video_duration: number
  message: string
}

const AnalysisResultsPage: React.FC = () => {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(50)
  const [hoveredEvent, setHoveredEvent] = useState<AnalysisEvent | null>(null)
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const { token } = useAuth()
  
  // Load analysis data from localStorage or fetch from backend
  useEffect(() => {
    const loadAnalysisData = async () => {
      try {
        // Try to get data from localStorage first
        const storedData = localStorage.getItem('analysisData')
        if (storedData) {
          const data: AnalysisData = JSON.parse(storedData)
          setAnalysisData(data)
          setLoading(false)
          return
        }

        // If no stored data, try to fetch from backend
        // You might want to pass session_id as a URL parameter
        const urlParams = new URLSearchParams(window.location.search)
        const sessionId = urlParams.get('session_id')
        
        if (sessionId) {
          const response = await fetch(`http://localhost:5002/api/events/${sessionId}`)
          if (response.ok) {
            const eventsData = await response.json()
            setAnalysisData({
              success: true,
              session_id: sessionId,
              events: eventsData,
              output_video_url: `/processed_video/${sessionId}/analyzed_video.mp4`,
              video_duration: 0, // Assuming video_duration is not provided in the response
              message: 'Analysis loaded successfully'
            })
          } else {
            throw new Error('Failed to load analysis data')
          }
        } else {
          throw new Error('No analysis data found')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analysis')
      } finally {
        setLoading(false)
      }
    }

    loadAnalysisData()
  }, [])

  const videoUrl = analysisData 
    ? `http://localhost:5002${analysisData.output_video_url}?token=${token}` 
    : ""

  // Convert backend events to frontend format
  const analysisEvents: AnalysisEvent[] = analysisData?.events?.events?.map((event, index) => ({
    id: index.toString(),
    timestamp: event.timestamp,
    type: event.type,
    title: event.type.charAt(0).toUpperCase() + event.type.slice(1).replace('_', ' '),
    description: event.description,
    severity: event.type === 'travel' || event.type === 'double_dribble' ? 'error' : 
              event.type === 'pass' || event.type === 'interception' ? 'warning' : 'info'
  })) || []

  // Calculate a stable duration for markers
  const markerDuration = analysisData?.video_duration || 
                        analysisData?.events?.metadata?.video_duration || 
                        Math.max(930, Math.max(...analysisEvents.map(e => e.timestamp)) + 60)

  const togglePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTime = parseFloat(e.target.value)
    setCurrentTime(newTime)
    if (videoRef.current) {
      videoRef.current.currentTime = newTime
    }
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = Number.parseInt(e.target.value)
    setVolume(newVolume)
    if (videoRef.current) {
      videoRef.current.volume = newVolume / 100
    }
  }

  const jumpToEvent = (timestamp: number) => {
    setCurrentTime(timestamp)
    if (videoRef.current) {
      videoRef.current.currentTime = timestamp
    }
  }

  const toggleFullscreen = () => {
    const videoContainer = videoRef.current?.parentElement
    if (videoContainer) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        videoContainer.requestFullscreen()
      }
    }
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

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleLoadedMetadata = () => {
      console.log('Video metadata loaded, duration:', video.duration)
      setDuration(video.duration)
    }

    const handleTimeUpdate = () => {
      console.log('Video time update:', video.currentTime, 'Duration:', video.duration)
      setCurrentTime(video.currentTime)
    }

    const handlePlay = () => {
      console.log('Video started playing')
      setIsPlaying(true)
    }

    const handlePause = () => {
      console.log('Video paused')
      setIsPlaying(false)
    }

    const handleEnded = () => {
      console.log('Video ended')
      setIsPlaying(false)
      setCurrentTime(0)
    }

    const handleError = (e: Event) => {
      console.error('Video error:', e)
    }

    video.addEventListener('loadedmetadata', handleLoadedMetadata)
    video.addEventListener('timeupdate', handleTimeUpdate)
    video.addEventListener('play', handlePlay)
    video.addEventListener('pause', handlePause)
    video.addEventListener('ended', handleEnded)
    video.addEventListener('error', handleError)

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata)
      video.removeEventListener('timeupdate', handleTimeUpdate)
      video.removeEventListener('play', handlePlay)
      video.removeEventListener('pause', handlePause)
      video.removeEventListener('ended', handleEnded)
      video.removeEventListener('error', handleError)
    }
  }, [])

  if (loading) {
    return (
      <div className="results-page">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading analysis results...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="results-page">
        <div className="error-container">
          <AlertTriangle size={48} className="text-red" />
          <h2>Error Loading Results</h2>
          <p>{error}</p>
          <Link to="/analyze/upload" className="btn btn-primary">
            Try Again
          </Link>
        </div>
      </div>
    )
  }

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
                    <video
                      ref={videoRef}
                      className="video-placeholder"
                      controls={false}
                      preload="metadata"
                      src={videoUrl}
                    >
                      Your browser does not support the video tag.
                    </video>

                    {/* Video Controls Overlay */}
                    <div className="video-controls-overlay">
                      {/* Progress Bar with Event Markers */}
                      <div className="progress-container">
                        <div className="progress-time-labels">
                          <span>{formatTime(currentTime)}</span>
                          <span>{formatTime(duration || markerDuration)}</span>
                        </div>
                        <input
                          type="range"
                          min="0"
                          max={duration || markerDuration}
                          value={currentTime}
                          onChange={handleTimeChange}
                          className="progress-slider"
                          step="any"
                          style={{ 
                            background: `linear-gradient(to right, #4f46e5 ${(currentTime/(duration||markerDuration))*100}%, #e5e7eb ${(currentTime/(duration||markerDuration))*100}%)` 
                          }}
                        />

                        {/* Event Markers */}
                        {analysisEvents.map((event) => (
                          <div
                            key={event.id}
                            className={`event-marker ${event.severity}`}
                            style={{
                              left: `${(event.timestamp / markerDuration) * 100}%`,
                            }}
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
                          {formatTime(currentTime)} / {formatTime(duration || markerDuration)}
                        </div>

                        <button className="control-btn ml-auto" onClick={toggleFullscreen}>
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
                      {(analysisData?.events?.summary?.event_counts?.travel || 0) + 
                       (analysisData?.events?.summary?.event_counts?.double_dribble || 0)}
                    </div>
                    <div className="stat-label">Double Dribbles</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value warning">
                      {(analysisData?.events?.summary?.event_counts?.pass || 0) + 
                       (analysisData?.events?.summary?.event_counts?.interception || 0)}
                    </div>
                    <div className="stat-label">Passes & Interceptions</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value total">{analysisData?.events?.summary?.total_events || 0}</div>
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
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default AnalysisResultsPage
