"use client"

import React, { useState, useRef } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Upload, BarChart3, ArrowLeft, FileVideo, CheckCircle, AlertCircle } from "lucide-react"
import { useAuth } from "../context/AuthContext"

interface AnalysisResponse {
  success: boolean
  session_id: string
  events: any
  output_video_url: string
  message: string
}

const VideoUploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const { token } = useAuth()

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith("video/")) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file && file.type.startsWith("video/")) {
      setSelectedFile(file)
      setError(null)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  const uploadAndAnalyze = async () => {
    if (!selectedFile) {
      setError("Please select a video file first")
      return
    }

    if (!token) {
      setError("Please log in to upload videos")
      return
    }

    setIsUploading(true)
    setIsAnalyzing(false)
    setError(null)
    setUploadProgress(0)

    try {
      // Create FormData for file upload
      const formData = new FormData()
      formData.append('video', selectedFile)
      formData.append('max_frames', '300') // Optional: limit frames for faster testing

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Make API call to backend server at localhost:5002
      const response = await fetch('http://localhost:5002/api/analyze', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        let detailedError = errorData.error || 'Upload failed'
        if (errorData.stderr) {
          detailedError += `:\n\n${errorData.stderr}`
        }
        throw new Error(detailedError)
      }

      const data: AnalysisResponse = await response.json()
      
      if (data.success) {
        setAnalysisData(data)
        setIsUploading(false)
        setIsAnalyzing(true)
        
        // Simulate analysis time
        setTimeout(() => {
          setIsAnalyzing(false)
          setAnalysisComplete(true)
        }, 2000)
      } else {
        throw new Error(data.message || 'Analysis failed')
      }

    } catch (err) {
      console.error('Upload error:', err)
      setError(err instanceof Error ? err.message : 'Upload failed')
      setIsUploading(false)
      setIsAnalyzing(false)
      setUploadProgress(0)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const viewResults = () => {
    if (analysisData) {
      // Store the analysis data in localStorage for the results page
      localStorage.setItem('analysisData', JSON.stringify(analysisData))
      navigate('/analyze/results')
    }
  }

  if (analysisComplete) {
    return (
      <div className="upload-page">
        <header className="analysis-header">
          <div className="header-left">
            <Link to="/dashboard" className="btn btn-ghost">
              <ArrowLeft size={16} />
              Back to Dashboard
            </Link>
            <div className="page-title">
              <BarChart3 size={24} />
              <span>Analysis Complete</span>
            </div>
          </div>
        </header>

        <main className="upload-main">
          <div className="container">
            <div className="completion-content">
              <div className="completion-header">
                <CheckCircle size={64} className="text-green" />
                <h1>Analysis Complete!</h1>
                <p>Your video has been processed and analyzed successfully.</p>
              </div>

              <div className="completion-stats">
                <div className="stat-item">
                  <div className="stat-value">{analysisData?.events?.summary?.total_events || 0}</div>
                  <div className="stat-label">Events Found</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">
                    {analysisData?.events?.metadata?.video_duration 
                      ? `${Math.floor(analysisData.events.metadata.video_duration / 60)}:${Math.floor(analysisData.events.metadata.video_duration % 60).toString().padStart(2, '0')}`
                      : 'N/A'
                    }
                  </div>
                  <div className="stat-label">Duration</div>
                </div>
              </div>

              <div className="completion-actions">
                <button onClick={viewResults} className="btn btn-primary btn-large">
                  View Analysis Results
                </button>
                <button className="btn btn-outline" onClick={() => window.location.reload()}>
                  Analyze Another Video
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="upload-page">
      {/* Header */}
      <header className="analysis-header">
        <div className="header-left">
          <Link to="/dashboard" className="btn btn-ghost">
            <ArrowLeft size={16} />
            Back to Dashboard
          </Link>
          <div className="page-title">
            <BarChart3 size={24} />
            <span>Video Upload</span>
          </div>
        </div>
      </header>

      <main className="upload-main">
        <div className="container">
          <div className="upload-content">
            <div className="upload-header">
              <h1>Upload Your Basketball Video</h1>
              <p>Upload your game footage to receive detailed analysis with timestamps and insights.</p>
            </div>

            <div className="upload-card">
              <div className="upload-card-header">
                <h3>Select Video File</h3>
              </div>
              <div className="upload-card-content">
                {!selectedFile ? (
                  <div
                    className="upload-dropzone"
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload size={48} className="upload-icon" />
                    <h3>Drop your video here</h3>
                    <p>or click to browse files</p>
                    <small>Supports MP4, MOV, AVI files up to 500MB</small>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="video/*"
                      onChange={handleFileSelect}
                      style={{ display: "none" }}
                    />
                  </div>
                ) : (
                  <div className="upload-file-info">
                    <div className="file-info">
                      <FileVideo size={32} className="file-icon" />
                      <div className="file-details">
                        <h4>{selectedFile.name}</h4>
                        <p>{formatFileSize(selectedFile.size)}</p>
                      </div>
                      <button className="btn btn-ghost" onClick={() => setSelectedFile(null)}>
                        Remove
                      </button>
                    </div>

                    {error && (
                      <div className="error-message" style={{ color: 'red', marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <AlertCircle size={16} />
                        {error}
                      </div>
                    )}

                    {isUploading && (
                      <div className="upload-progress">
                        <div className="progress-info">
                          <span>Uploading...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <div className="progress-bar">
                          <div className="progress-fill" style={{ width: `${uploadProgress}%` }}></div>
                        </div>
                      </div>
                    )}

                    {isAnalyzing && (
                      <div className="analyzing-state">
                        <div className="spinner"></div>
                        <p>Analyzing your video... This may take a few minutes.</p>
                      </div>
                    )}

                    {!isUploading && !isAnalyzing && (
                      <button onClick={uploadAndAnalyze} className="btn btn-primary btn-full btn-large">
                        Start Analysis
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Upload Tips */}
            <div className="tips-card">
              <div className="tips-header">
                <h3>Tips for Best Results</h3>
              </div>
              <div className="tips-list">
                <div className="tip-item">
                  <CheckCircle size={16} className="text-green" />
                  <span>Ensure good lighting and clear visibility of players</span>
                </div>
                <div className="tip-item">
                  <CheckCircle size={16} className="text-green" />
                  <span>Keep the camera stable and focused on the court</span>
                </div>
                <div className="tip-item">
                  <CheckCircle size={16} className="text-green" />
                  <span>Higher resolution videos provide more accurate analysis</span>
                </div>
                <div className="tip-item">
                  <CheckCircle size={16} className="text-green" />
                  <span>Include the full court view when possible</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default VideoUploadPage
