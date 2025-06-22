import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import { AuthProvider } from "./context/AuthContext"
import ProtectedRoute from "./components/ProtectedRoute"
import HomePage from "./pages/HomePage"
import LoginPage from "./pages/LoginPage"
import SignupPage from "./pages/SignupPage"
import DashboardPage from "./pages/DashboardPage"
import WebcamAnalysisPage from "./pages/WebcamAnalysisPage"
import VideoUploadPage from "./pages/VideoUploadPage"
import AnalysisResultsPage from "./pages/AnalysisResultsPage"
import "./App.css"

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } />
            <Route path="/analyze/webcam" element={
              <ProtectedRoute>
                <WebcamAnalysisPage />
              </ProtectedRoute>
            } />
            <Route path="/analyze/upload" element={
              <ProtectedRoute>
                <VideoUploadPage />
              </ProtectedRoute>
            } />
            <Route path="/analyze/results" element={
              <ProtectedRoute>
                <AnalysisResultsPage />
              </ProtectedRoute>
            } />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App
