import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { AchievementProvider } from './contexts/AchievementContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'

// Pages
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Onboarding from './pages/Onboarding'
import Goals from './pages/Goals'
import Portfolio from './pages/Portfolio'
import CourseHome from './pages/CourseHome'
import LessonDetail from './pages/LessonDetail'
import ScenarioHome from './pages/ScenarioHome'
import ScenarioPlay from './pages/ScenarioPlay'
import ScenarioResult from './pages/ScenarioResult'
import Achievements from './pages/Achievements'
import StockChallenge from './pages/StockChallenge'
import WealthPlaySimulator from './pages/WealthPlaySimulator'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AchievementProvider>
          <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<Layout showNav={false}><Landing /></Layout>} />
          
          {/* Protected Routes */}
          <Route
            path="/onboarding"
            element={
              <PrivateRoute>
                <Layout showNav={false}><Onboarding /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Layout><Dashboard /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/goals"
            element={
              <PrivateRoute>
                <Layout><Goals /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/achievements"
            element={
              <PrivateRoute>
                <Layout><Achievements /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/portfolio/:tab?"
            element={
              <PrivateRoute>
                <Layout><Portfolio /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/course"
            element={
              <PrivateRoute>
                <Layout><CourseHome /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/course/:courseId/:moduleId"
            element={
              <PrivateRoute>
                <Layout showNav={false}><LessonDetail /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/scenario"
            element={
              <PrivateRoute>
                <Layout showNav={false}><ScenarioHome /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/scenario/quiz/:runId"
            element={
              <PrivateRoute>
                <Layout showNav={false}><WealthPlaySimulator /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/scenario/quiz/:runId/result"
            element={
              <PrivateRoute>
                <Layout showNav={false}><WealthPlaySimulator /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/scenario/stock-challenge"
            element={
              <PrivateRoute>
                <Layout showNav={false}><StockChallenge /></Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/wealthplay"
            element={
              <PrivateRoute>
                <Layout showNav={false}><WealthPlaySimulator /></Layout>
              </PrivateRoute>
            }
          />
          
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
        </AchievementProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

