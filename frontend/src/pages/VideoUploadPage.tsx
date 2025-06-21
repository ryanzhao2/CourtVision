"use client"

import type React from "react"
import { useState, useRef } from "react"
import { Link } from "react-router-dom"
import { Upload, BarChart3, ArrowLeft, FileVideo, CheckCircle } from "lucide-react"

const VideoUploadPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisComplete, setAnalysisComplete] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith("video/")) {
      setSelectedFile(file)
    }
  }

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const file = event.dataTransfer.files[0]
    if (file && file.type.startsWith("video/")) {
      setSelectedFile(file)
    }
  }

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }

  const simulateUpload = () => {
    setIsUploading(true)
    setUploadProgress(0)

    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsUploading(false)
          setIsAnalyzing(true)
          simulateAnalysis()
          return 100
        }
        return prev + 10
      })
    }, 200)
  }

  const simulateAnalysis = () => {
    setTimeout(() => {
      setIsAnalyzing(false)
      setAnalysisComplete(true)
    }, 3000)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
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
                  <div className="stat-value">23</div>
                  <div className="stat-label">Events Found</div>
                </div>
                <div className="stat-item">
                  <div className="stat-value">15:30</div>
                  <div className="stat-label">Duration</div>
                </div>
              </div>

              <div className="completion-actions">
                <Link to="/analyze/results" className="btn btn-primary btn-large">
                  View Analysis Results
                </Link>
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
                      <button onClick={simulateUpload} className="btn btn-primary btn-full btn-large">
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
