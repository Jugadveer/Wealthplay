/**
 * Routes.
 *
 * Every page below the landing route is lazily loaded, so the first paint ships
 * the landing page and nothing else. Auth no longer blocks the tree: the app
 * renders immediately and only guarded routes wait on the session check.
 */
import { Suspense, lazy } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'

import { AuthProvider, useAuth } from './auth/AuthContext'
import ErrorBoundary from './components/ErrorBoundary'
import Shell from './components/Shell'
import { Skeleton } from './ui'
import Landing from './pages/Landing'

const Today = lazy(() => import('./pages/Today'))
const Learn = lazy(() => import('./pages/Learn'))
const Course = lazy(() => import('./pages/Course'))
const Lesson = lazy(() => import('./pages/Lesson'))
const Markets = lazy(() => import('./pages/Markets'))
const Play = lazy(() => import('./pages/Play'))
const Progress = lazy(() => import('./pages/Progress'))
const Onboarding = lazy(() => import('./pages/Onboarding'))
const NotFound = lazy(() => import('./pages/NotFound'))

export default function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <AuthProvider>
          <Shell>
            <Suspense fallback={<PageFallback />}>
              <Routes>
                <Route path="/" element={<PublicHome />} />

                <Route element={<RequireAuth />}>
                  <Route path="/onboarding" element={<Onboarding />} />
                  <Route path="/today" element={<Today />} />
                  <Route path="/learn" element={<Learn />} />
                  <Route path="/learn/:courseId" element={<Course />} />
                  <Route path="/learn/:courseId/:moduleId" element={<Lesson />} />
                  <Route path="/markets" element={<Markets />} />
                  <Route path="/markets/:tab" element={<Markets />} />
                  <Route path="/markets/explore/:symbol" element={<Markets />} />
                  <Route path="/play" element={<Play />} />
                  <Route path="/progress" element={<Progress />} />
                </Route>

                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </Shell>
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

/** Signed-in visitors land on today's set rather than the marketing page. */
function PublicHome() {
  const { user, checked } = useAuth()
  if (checked && user) return <Navigate to="/today" replace />
  return <Landing />
}

/**
 * Gate for authenticated routes.
 *
 * Waits only for the session check, and only here — the rest of the app has
 * already rendered by this point.
 */
function RequireAuth() {
  const { user, checked } = useAuth()
  const location = useLocation()

  if (!checked) return <PageFallback />
  if (!user) return <Navigate to="/" replace state={{ from: location }} />

  // A new account is sent through onboarding once, then never again.
  if (user.needs_onboarding && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />
  }

  return <Outlet />
}

function PageFallback() {
  return (
    <div className="mx-auto max-w-page space-y-4 px-4 py-10">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-10 w-72" />
      <Skeleton className="h-52" />
    </div>
  )
}
