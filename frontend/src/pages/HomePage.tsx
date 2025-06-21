import type React from "react"
import { Link } from "react-router-dom"
import { Camera, Upload, BarChart3, Zap } from "lucide-react"

const HomePage: React.FC = () => {
  return (
    <div className="home-page">
      {/* Header */}
      <header className="header">
        <Link to="/" className="logo">
          <BarChart3 size={32} />
          <span>CourtVision</span>
        </Link>
        <nav className="nav">
          <Link to="/features" className="nav-link">
            Features
          </Link>
          <Link to="/pricing" className="nav-link">
            Pricing
          </Link>
          <Link to="/login" className="nav-link">
            Login
          </Link>
          <Link to="/signup" className="btn btn-primary">
            Get Started
          </Link>
        </nav>
      </header>

      <main>
        {/* Hero Section */}
        <section className="hero">
          <div className="container">
            <div className="hero-content">
              <div className="hero-text">
                <h1>AI-Powered Basketball Analytics</h1>
                <p>
                  Transform your game with real-time analysis. Upload videos or use live webcam feed to get instant
                  insights on fouls, violations, and key plays.
                </p>
                <div className="hero-buttons">
                  <Link to="/signup" className="btn btn-primary btn-large">
                    Start Analyzing
                  </Link>
                  <Link to="/demo" className="btn btn-outline btn-large">
                    Watch Demo
                  </Link>
                </div>
              </div>
              <div className="hero-image">
                <img
                  src="https://images.unsplash.com/photo-1546519638-68e109498ffc?ixlib=rb-4.0.3&auto=format&fit=crop&w=600&h=400"
                  alt="Basketball Analytics Dashboard"
                  className="dashboard-image"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features">
          <div className="container">
            <div className="section-header">
              <h2>Powerful Analytics Features</h2>
              <p>Our AI-powered platform provides comprehensive basketball analysis for players, coaches, and teams.</p>
            </div>
            <div className="features-grid">
              <div className="feature-card">
                <Camera size={48} className="feature-icon" />
                <h3>Live Webcam Analysis</h3>
                <p>
                  Real-time analysis of basketball gameplay through your webcam with instant feedback on fouls,
                  violations, and key plays.
                </p>
              </div>
              <div className="feature-card">
                <Upload size={48} className="feature-icon" />
                <h3>Video Upload Analysis</h3>
                <p>
                  Upload your game footage and receive detailed timestamps with analysis of significant events and
                  plays.
                </p>
              </div>
              <div className="feature-card">
                <Zap size={48} className="feature-icon" />
                <h3>Interactive Timeline</h3>
                <p>
                  Navigate through your analyzed videos with an interactive timeline showing key moments and detailed
                  insights.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="how-it-works">
          <div className="container">
            <div className="section-header">
              <h2>How It Works</h2>
              <p>Get started with basketball analytics in three simple steps.</p>
            </div>
            <div className="steps-grid">
              <div className="step">
                <div className="step-number">1</div>
                <h3>Upload or Stream</h3>
                <p>Choose to upload a video file or start a live webcam session for real-time analysis.</p>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <h3>AI Analysis</h3>
                <p>Our advanced AI processes your footage to identify fouls, violations, and significant plays.</p>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <h3>Get Insights</h3>
                <p>Receive detailed analytics with timestamps and actionable insights to improve your game.</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta">
          <div className="container">
            <div className="cta-content">
              <h2>Ready to Elevate Your Game?</h2>
              <p>Join thousands of players and coaches using CourtVision to improve their basketball performance.</p>
              <Link to="/signup" className="btn btn-secondary btn-large">
                Get Started Free
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          <p>&copy; 2024 CourtVision. All rights reserved.</p>
          <nav className="footer-nav">
            <Link to="/terms">Terms of Service</Link>
            <Link to="/privacy">Privacy</Link>
          </nav>
        </div>
      </footer>
    </div>
  )
}

export default HomePage
