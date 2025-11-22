import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { GraduationCap, TrendingUp, Bot, ArrowRight, Rocket } from 'lucide-react'
import { Link } from 'react-router-dom'

const Landing = () => {
  const { user, loading } = useAuth()

  // Don't redirect while loading - wait for auth check to complete
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  // Only redirect if user is authenticated and loading is complete
  // If we have a query parameter, it means we just logged out - don't redirect
  const hasQueryParam = window.location.search.length > 0
  
  // If user is authenticated and we don't have a query param, redirect to dashboard
  if (user && !hasQueryParam) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-muted-1 to-white">
      {/* Simple Header for Landing Page - Only for non-authenticated users */}
      {!user && (
        <header className="sticky top-0 z-50 bg-brand-1 text-white shadow-lg">
          <div className="max-w-container mx-auto px-6 lg:px-10">
            <div className="flex items-center justify-between h-[70px]">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold hover:scale-105 transition-transform">
                <span>WealthPlay</span>
              </Link>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => {
                    const event = new CustomEvent('openAuthModal', { detail: 'login' })
                    window.dispatchEvent(event)
                  }}
                  className="px-4 py-2 rounded-full bg-white text-brand-1 font-semibold hover:bg-muted-1 transition-all active:scale-95"
                >
                  Login
                </button>
                <button
                  onClick={() => {
                    const event = new CustomEvent('openAuthModal', { detail: 'signup' })
                    window.dispatchEvent(event)
                  }}
                  className="px-4 py-2 rounded-full bg-transparent border-2 border-white text-white font-semibold hover:bg-white/10 transition-all active:scale-95"
                >
                  Sign Up
                </button>
              </div>
            </div>
          </div>
          <div className="h-0.5 bg-gradient-to-r from-brand-1 via-brand-2 to-brand-1 bg-[length:200%_100%] animate-[shimmer_3s_linear_infinite]"></div>
        </header>
      )}
      {/* Hero Section */}
      <div className="max-w-container mx-auto px-6 py-20 lg:px-10">
        <div className="text-center mb-16 fade-slide-up">
          <h1 className="text-5xl md:text-6xl font-bold text-brand-1 mb-6">
            WealthPlay
          </h1>
          <p className="text-xl text-text-muted max-w-2xl mx-auto leading-relaxed mb-10">
            Master financial literacy through interactive courses and real-world scenarios.
            Learn, practice, and make better financial decisions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => {
                // Trigger signup modal via custom event
                const event = new CustomEvent('openAuthModal', { detail: 'signup' })
                window.dispatchEvent(event)
              }}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180"
            >
              <Rocket className="w-5 h-5" />
              Get Started
            </button>
            <Link
              to="/#features"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white border-2 border-brand-1 text-brand-1 font-semibold hover:bg-brand-1 hover:text-white transition-all duration-180 active:scale-95"
            >
              Learn More
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="mt-24">
          <h2 className="text-4xl font-bold text-center text-text-main mb-4">
            Why WealthPlay?
          </h2>
          <p className="text-center text-text-muted mb-12 text-lg">
            Everything you need to master personal finance
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-brand-1/10 flex items-center justify-center mb-6">
                <GraduationCap className="w-8 h-8 text-brand-1" />
              </div>
              <h3 className="text-xl font-bold text-text-main mb-3">
                Interactive Courses
              </h3>
              <p className="text-text-muted leading-relaxed">
                Learn financial concepts through engaging, conversational lessons with AI
                mentors guiding you every step.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-white rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-brand-1/10 flex items-center justify-center mb-6">
                <TrendingUp className="w-8 h-8 text-brand-1" />
              </div>
              <h3 className="text-xl font-bold text-text-main mb-3">Real Scenarios</h3>
              <p className="text-text-muted leading-relaxed">
                Practice decision-making with realistic financial scenarios that test your
                knowledge and build confidence.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-brand-1/10 flex items-center justify-center mb-6">
                <Bot className="w-8 h-8 text-brand-1" />
              </div>
              <h3 className="text-xl font-bold text-text-main mb-3">AI-Powered Learning</h3>
              <p className="text-text-muted leading-relaxed">
                Get personalized guidance from AI mentors that adapt to your learning style
                and answer your questions instantly.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Landing

