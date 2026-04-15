// src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import LandingPage       from './pages/LandingPage'
import LoginPage         from './pages/LoginPage'
import SignupPage        from './pages/SignupPage'
import AppShell          from './components/layout/AppShell'
import DashboardPage     from './pages/app/DashboardPage'
import ChatPage          from './pages/app/ChatPage'
import ScorecardListPage from './pages/app/ScorecardListPage'
import ScorecardPage     from './pages/app/ScorecardPage'
import ComparePage       from './pages/app/ComparePage'
import ResearchPage      from './pages/app/ResearchPage'
import WatchlistPage     from './pages/app/WatchlistPage'
import HistoryPage       from './pages/app/HistoryPage'
import FilesPage             from './pages/app/FilesPage'
import OcrPage           from './pages/app/OcrPage'
import AudioIntelligencePage from './pages/app/AudioIntelligencePage'
import ProtectedRoute    from './components/auth/ProtectedRoute'

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/"       element={<LandingPage />} />
      <Route path="/login"  element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />

      {/* Protected /app routes — requires valid JWT */}
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index                 element={<Navigate to="dashboard" replace />} />
        <Route path="dashboard"      element={<DashboardPage />} />
        <Route path="chat"           element={<ChatPage />} />
        <Route path="scorecard"      element={<ScorecardListPage />} />
        <Route path="scorecard/:company" element={<ScorecardPage />} />
        <Route path="compare"        element={<ComparePage />} />
        <Route path="research"       element={<ResearchPage />} />
        <Route path="watchlist"      element={<WatchlistPage />} />
        <Route path="history"        element={<HistoryPage />} />
        <Route path="files"          element={<FilesPage />} />
        <Route path="audio"          element={<AudioIntelligencePage />} />
        <Route path="ocr"            element={<OcrPage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
