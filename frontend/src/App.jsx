import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { AchievementProvider } from './contexts/AchievementContext'
import { GlobalDataProvider } from './contexts/GlobalDataContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import ErrorBoundary from './components/ErrorBoundary'
import AuthWrapper from './components/AuthWrapper'


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
        <GlobalDataProvider>
          <AchievementProvider>
            <AuthWrapper>
              <Router
              future={{
                v7_startTransition: true,
                v7_relativeSplatPath: true,
              }}
            >
            <Routes>
              {}
            <Route path="/" element={<Layout showNav={false}><Landing /></Layout>} />
            
            {}
            <Route
              path="/onboarding"
              element={
                <PrivateRoute>
                  <Layout><Onboarding /></Layout>
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
                  <Layout><LessonDetail /></Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/scenario"
              element={
                <PrivateRoute>
                  <Layout><ScenarioHome /></Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/scenario/quiz/:runId"
              element={
                <PrivateRoute>
                  <Layout><WealthPlaySimulator /></Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/scenario/quiz/:runId/result"
              element={
                <PrivateRoute>
                  <Layout><WealthPlaySimulator /></Layout>
                </PrivateRoute>
              }
            />
            <Route
              path="/scenario/stock-challenge"
              element={
                <PrivateRoute>
                  <Layout><StockChallenge /></Layout>
                </PrivateRoute>
              }
            />

            <Route
              path="/wealthplay"
              element={
                <PrivateRoute>
                  <Layout><WealthPlaySimulator /></Layout>
                </PrivateRoute>
              }
            />
            
            {}
            <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
            </AuthWrapper>
          </AchievementProvider>
        </GlobalDataProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

