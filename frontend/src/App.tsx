import { BrowserRouter as Router, Routes, Route } from "react-router-dom"
import HomePage from "./pages/HomePage.tsx"
import LoginPage from "./pages/LoginPage"
import SignupPage from "./pages/SignupPage"
import DashboardPage from "./pages/DashboardPage.tsx"
import WebcamAnalysisPage from "./pages/WebcamAnalysisPage"
import VideoUploadPage from "./pages/VideoUploadPage"
import AnalysisResultsPage from "./pages/AnalysisResultsPage"
import "./App.css"

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analyze/webcam" element={<WebcamAnalysisPage />} />
          <Route path="/analyze/upload" element={<VideoUploadPage />} />
          <Route path="/analyze/results" element={<AnalysisResultsPage />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
