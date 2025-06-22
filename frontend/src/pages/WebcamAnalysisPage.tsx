"use client"

import type React from "react"
import { useState, useRef, useEffect, useCallback } from "react"
import { Link } from "react-router-dom"
import { Camera, Square, BarChart3, ArrowLeft, AlertTriangle, CheckCircle } from "lucide-react"

interface LiveEvent {
  id: string
  type: string
  description: string
  timestamp: string
  severity: "info" | "warning" | "error"
}

interface AnalysisResult {
  events: Array<{
    type: string
    description: string
    severity: "info" | "warning" | "error"
    timestamp: number
  }>
  current_holder: number | null
  holding_frames: number
  traveling_detected: boolean
  ball_detected: boolean
  people_detected: number
  ball_boxes: Array<[number, number, number, number, number]>
  pose_results: number
  visual_data?: {
    ball_boxes: Array<[number, number, number, number, number]>
    pose_keypoints: Array<Array<[number, number, number]>>
    current_holder_pose: Array<[number, number, number]> | null
    current_knee_pos: [number, number] | null
    current_hip_pos: [number, number] | null
    current_person_center: [number, number] | null
  }
}

const WebcamAnalysisPage: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [analysisStats, setAnalysisStats] = useState({
    ballDetected: false,
    peopleDetected: 0,
    currentHolder: null as number | null,
    holdingFrames: 0,
    travelingDetected: false
  })
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null)
  const websocketRef = useRef<WebSocket | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const [visualData, setVisualData] = useState<AnalysisResult['visual_data'] | null>(null)

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    try {
      const ws = new WebSocket('ws://localhost:8765')
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
      }
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'analysis') {
            handleAnalysisResult(message.data)
          } else if (message.type === 'connection') {
            console.log('Server connection confirmed:', message.message)
            // Start frame capture after connection is confirmed
            if (isRecording) {
              setTimeout(() => {
                captureAndSendFrame()
              }, 100)
            }
          } else if (message.type === 'error') {
            console.error('Server error:', message.message)
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setIsConnected(false)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
      }
      
      websocketRef.current = ws
    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
    }
  }, [])

  const handleAnalysisResult = (result: AnalysisResult) => {
    // Update analysis stats
    setAnalysisStats({
      ballDetected: result.ball_detected,
      peopleDetected: result.people_detected,
      currentHolder: result.current_holder,
      holdingFrames: result.holding_frames,
      travelingDetected: result.traveling_detected
    })

    // Update visual data for overlays
    if (result.visual_data) {
      setVisualData(result.visual_data)
      drawOverlays(result.visual_data)
    }

    // Add new events to live events
    if (result.events && result.events.length > 0) {
      const newEvents: LiveEvent[] = result.events.map(event => ({
        id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
        type: event.type,
        description: event.description,
        timestamp: new Date(event.timestamp * 1000).toLocaleTimeString(),
        severity: event.severity
      }))

      setLiveEvents(prev => [...prev, ...newEvents])
    }
  }

  const drawOverlays = (visualData: AnalysisResult['visual_data']) => {
    if (!overlayCanvasRef.current || !videoRef.current || !visualData) return

    const canvas = overlayCanvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Clear previous overlays
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Set canvas size to match video
    canvas.width = videoRef.current.videoWidth
    canvas.height = videoRef.current.videoHeight

    // Draw ball bounding boxes
    if (visualData.ball_boxes && visualData.ball_boxes.length > 0) {
      ctx.strokeStyle = '#00ff00'
      ctx.lineWidth = 3
      ctx.fillStyle = '#00ff00'
      ctx.font = '16px Arial'
      
      visualData.ball_boxes.forEach((box, index) => {
        const [x1, y1, x2, y2, confidence] = box
        const width = x2 - x1
        const height = y2 - y1
        
        // Draw bounding box
        ctx.strokeRect(x1, y1, width, height)
        
        // Draw label
        ctx.fillText(`Ball (${(confidence * 100).toFixed(1)}%)`, x1, y1 - 10)
      })
    }

    // Draw pose keypoints
    if (visualData.pose_keypoints && visualData.pose_keypoints.length > 0) {
      visualData.pose_keypoints.forEach((keypoints, personIndex) => {
        // Draw keypoints
        keypoints.forEach((keypoint, keypointIndex) => {
          const [x, y, confidence] = keypoint
          if (confidence > 0.3) { // Only draw high-confidence keypoints
            ctx.fillStyle = '#ff0000'
            ctx.beginPath()
            ctx.arc(x, y, 4, 0, 2 * Math.PI)
            ctx.fill()
          }
        })
      })
    }

    // Draw current holder indicators
    if (visualData.current_holder_pose) {
      ctx.fillStyle = '#ffff00'
      ctx.font = 'bold 18px Arial'
      ctx.fillText('BALL HOLDER', 10, 30)
    }
  }

  // Capture and send frames
  const captureAndSendFrame = useCallback(() => {
    if (!isRecording || !videoRef.current || !canvasRef.current || !websocketRef.current || websocketRef.current.readyState !== WebSocket.OPEN) {
      return
    }

    const video = videoRef.current
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    if (!ctx) return

    // Set canvas size to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    // Convert canvas to base64
    const frameData = canvas.toDataURL('image/jpeg', 0.8)

    // Send frame to WebSocket
    websocketRef.current.send(JSON.stringify({
      type: 'frame',
      frame: frameData
    }))

    // Schedule next frame capture
    animationFrameRef.current = requestAnimationFrame(captureAndSendFrame)
  }, [isRecording])

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
      
      // Wait for video to be ready before connecting WebSocket and starting frame capture
      if (videoRef.current) {
        videoRef.current.onloadedmetadata = () => {
          // Connect to WebSocket after video is ready
          connectWebSocket()
        }
      }
      
    } catch (error) {
      console.error("Error accessing webcam:", error)
    }
  }

  const stopRecording = () => {
    if (stream) {
      stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      setStream(null)
    }
    
    // Stop frame capture
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    
    // Close WebSocket connection
    if (websocketRef.current) {
      websocketRef.current.close()
      websocketRef.current = null
    }
    
    // Clear overlays
    if (overlayCanvasRef.current) {
      const ctx = overlayCanvasRef.current.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, overlayCanvasRef.current.width, overlayCanvasRef.current.height)
      }
    }
    
    setIsRecording(false)
    setIsConnected(false)
    setLiveEvents([])
    setVisualData(null)
    setAnalysisStats({
      ballDetected: false,
      peopleDetected: 0,
      currentHolder: null,
      holdingFrames: 0,
      travelingDetected: false
    })
  }

  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach((track: MediaStreamTrack) => track.stop())
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (websocketRef.current) {
        websocketRef.current.close()
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
              {isConnected ? "Connected & Recording" : "Connecting..."}
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
                  {isConnected && (
                    <div className="connection-status connected">
                      <div className="status-dot"></div>
                      Connected to AI
                    </div>
                  )}
                </div>
                <div className="video-container">
                  <video ref={videoRef} autoPlay muted playsInline className="video-feed" />
                  <canvas ref={canvasRef} style={{ display: 'none' }} />
                  <canvas 
                    ref={overlayCanvasRef} 
                    className="overlay-canvas"
                    style={{
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      pointerEvents: 'none',
                      zIndex: 10
                    }}
                  />
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

              {/* Real-time Stats */}
              <div className="stats-card">
                <div className="stats-header">
                  <h3>Live Analysis Stats</h3>
                </div>
                <div className="stats-grid">
                  <div className="stat-item">
                    <div className={`stat-value ${analysisStats.ballDetected ? 'info' : 'gray'}`}>
                      {analysisStats.ballDetected ? 'Yes' : 'No'}
                    </div>
                    <div className="stat-label">Ball Detected</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value info">{analysisStats.peopleDetected}</div>
                    <div className="stat-label">People Detected</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value info">
                      {analysisStats.currentHolder !== null ? `Player ${analysisStats.currentHolder}` : 'None'}
                    </div>
                    <div className="stat-label">Current Holder</div>
                  </div>
                  <div className="stat-item">
                    <div className={`stat-value ${analysisStats.travelingDetected ? 'error' : 'info'}`}>
                      {analysisStats.travelingDetected ? 'Yes' : 'No'}
                    </div>
                    <div className="stat-label">Traveling</div>
                  </div>
                </div>
              </div>

              {/* Session Stats */}
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
