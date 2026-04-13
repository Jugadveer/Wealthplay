import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import {
  GraduationCap,
  TrendingUp,
  Bot,
  ArrowRight,
  Rocket,
  ShieldCheck,
  Sparkles,
  CheckCircle2,
  LineChart,
  Star,
} from 'lucide-react'
import { Link } from 'react-router-dom'

const Landing = () => {
  const { user, loading } = useAuth()

  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  
  
  const hasQueryParam = window.location.search.length > 0
  
  
  if (user && !hasQueryParam) {
    return <Navigate to="/dashboard" replace />
  }

  return (
      <div className="min-h-screen bg-retro-bg">
      {}
      {!user && (
        <header className="sticky top-0 z-50 bg-retro-surface/90 backdrop-blur-md shadow-sm border-b border-brand-1/10">
          <div className="max-w-container mx-auto px-6 lg:px-10">
            <div className="flex items-center justify-between h-[70px]">
              <Link to="/" className="flex items-center gap-2 text-xl font-bold text-text-main hover:scale-105 transition-transform">
                <span>WealthPlay</span>
              </Link>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => {
                    const event = new CustomEvent('openAuthModal', { detail: 'login' })
                    window.dispatchEvent(event)
                  }}
                  className="px-4 py-2 rounded-full bg-retro-surface border border-brand-1/20 text-text-main font-semibold hover:bg-brand-1/10 transition-all active:scale-95"
                >
                  Login
                </button>
                <button
                  onClick={() => {
                    const event = new CustomEvent('openAuthModal', { detail: 'signup' })
                    window.dispatchEvent(event)
                  }}
                  className="px-4 py-2 rounded-full bg-retro-surface border border-brand-1/20 text-text-main font-semibold hover:bg-brand-1/10 hover:border-brand-1/30 transition-all active:scale-95"
                >
                  Sign Up
                </button>
              </div>
            </div>
          </div>
        </header>
      )}
      {}
      <div className="max-w-container mx-auto px-6 py-20 lg:px-10">
        <div className="text-center mb-16 fade-slide-up">
          <h1 className="text-5xl md:text-6xl font-bold text-text-main mb-6">
            WealthPlay
          </h1>
          <p className="text-xl text-text-muted max-w-2xl mx-auto leading-relaxed mb-10">
            Master financial literacy through interactive courses and real-world scenarios.
            Learn, practice, and make better financial decisions.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => {
                
                const event = new CustomEvent('openAuthModal', { detail: 'signup' })
                window.dispatchEvent(event)
              }}
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-brand-1 text-white font-semibold hover:bg-brand-2 hover:shadow-lg hover:shadow-brand-1/20 hover:-translate-y-1 active:scale-95 transition-all duration-180"
            >
              <Rocket className="w-5 h-5" />
              Get Started
            </button>
            <Link
              to="/#features"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-retro-surface border-2 border-brand-1 text-text-main font-semibold hover:bg-brand-1/10 hover:border-brand-1/40 hover:text-text-main transition-all duration-180 active:scale-95"
            >
              Learn More
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>

        {}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-16">
          <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-5 shadow-card">
            <p className="text-3xl font-bold text-text-main number-tabular">25+</p>
            <p className="text-sm text-text-muted">Interactive Modules</p>
          </div>
          <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-5 shadow-card">
            <p className="text-3xl font-bold text-text-main number-tabular">120+</p>
            <p className="text-sm text-text-muted">Scenario Challenges</p>
          </div>
          <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-5 shadow-card">
            <p className="text-3xl font-bold text-text-main number-tabular">4.9</p>
            <p className="text-sm text-text-muted">Learner Rating</p>
          </div>
          <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-5 shadow-card">
            <p className="text-3xl font-bold text-text-main number-tabular">24/7</p>
            <p className="text-sm text-text-muted">AI Mentor Support</p>
          </div>
        </div>

        {}
        <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-6 md:p-8 shadow-card mb-16">
          <div className="grid md:grid-cols-3 gap-6">
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-6 h-6 text-brand-1 mt-0.5" />
              <div>
                <p className="font-bold text-text-main">Safe Practice Zone</p>
                <p className="text-sm text-text-muted">Learn investing with simulated portfolios and zero real-money risk.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <LineChart className="w-6 h-6 text-brand-1 mt-0.5" />
              <div>
                <p className="font-bold text-text-main">Market-Style Decisions</p>
                <p className="text-sm text-text-muted">Train with practical scenarios designed around real financial tradeoffs.</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Sparkles className="w-6 h-6 text-brand-1 mt-0.5" />
              <div>
                <p className="font-bold text-text-main">Level up your wealth.</p>
                <p className="text-sm text-text-muted">Build consistent habits with progress tracking, streaks, and badges.</p>
              </div>
            </div>
          </div>
        </div>

        {}
        <div id="features" className="mt-24">
          <h2 className="text-4xl font-bold text-center text-text-main mb-4">
            Why WealthPlay?
          </h2>
          <p className="text-center text-text-muted mb-12 text-lg">
            Everything you need to master personal finance
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {}
            <div className="bg-retro-surface rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
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

            {}
            <div className="bg-retro-surface rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-brand-1/10 flex items-center justify-center mb-6">
                <TrendingUp className="w-8 h-8 text-brand-1" />
              </div>
              <h3 className="text-xl font-bold text-text-main mb-3">Real Scenarios</h3>
              <p className="text-text-muted leading-relaxed">
                Practice decision-making with realistic financial scenarios that test your
                knowledge and build confidence.
              </p>
            </div>

            {}
            <div className="bg-retro-surface rounded-xl p-8 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20">
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

        {}
        <div className="mt-24">
          <h2 className="text-4xl font-bold text-center text-text-main mb-4">How It Works</h2>
          <p className="text-center text-text-muted mb-12 text-lg">Get started in minutes with a guided flow</p>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-7 shadow-card">
              <div className="w-10 h-10 rounded-full bg-brand-1 text-white flex items-center justify-center font-bold mb-4">1</div>
              <h3 className="text-xl font-bold text-text-main mb-2">Set Your Profile</h3>
              <p className="text-text-muted">Tell us your goals and risk comfort so lessons and challenges can match your level.</p>
            </div>
            <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-7 shadow-card">
              <div className="w-10 h-10 rounded-full bg-brand-1 text-white flex items-center justify-center font-bold mb-4">2</div>
              <h3 className="text-xl font-bold text-text-main mb-2">Learn and Practice</h3>
              <p className="text-text-muted">Complete lessons, then apply concepts in simulator rounds and stock prediction games.</p>
            </div>
            <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-7 shadow-card">
              <div className="w-10 h-10 rounded-full bg-brand-1 text-white flex items-center justify-center font-bold mb-4">3</div>
              <h3 className="text-xl font-bold text-text-main mb-2">Track Progress</h3>
              <p className="text-text-muted">Monitor XP, streaks, confidence, and portfolio performance as your skills grow.</p>
            </div>
          </div>
        </div>

        {}
        <div className="mt-24">
          <h2 className="text-4xl font-bold text-center text-text-main mb-4">What Learners Say</h2>
          <p className="text-center text-text-muted mb-12 text-lg">A finance learning app that feels practical, not theoretical</p>

          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-7 shadow-card">
              <div className="flex items-center gap-1 mb-4 text-brand-2">
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
              </div>
              <p className="text-text-main leading-relaxed mb-4">
                “The scenario challenges helped me think like an investor instead of just memorizing terms.”
              </p>
              <p className="text-sm text-text-muted">Aarav, Beginner Investor</p>
            </div>
            <div className="bg-retro-surface rounded-[12px] border border-brand-1/15 p-7 shadow-card">
              <div className="flex items-center gap-1 mb-4 text-brand-2">
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
                <Star className="w-4 h-4 fill-current" />
              </div>
              <p className="text-text-main leading-relaxed mb-4">
                “I finally understand portfolio decisions because the AI feedback explains tradeoffs clearly.”
              </p>
              <p className="text-sm text-text-muted">Nisha, Early Professional</p>
            </div>
          </div>
        </div>

        {}
        <div className="mt-24 bg-authority-navy rounded-[12px] p-8 md:p-12 text-center border border-white/10 shadow-[0_18px_40px_rgba(15,23,42,0.2)]">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">Ready to build investing confidence?</h2>
          <p className="text-white/70 mb-8 max-w-2xl mx-auto">
            Join WealthPlay and start making smarter money decisions through practice-first learning.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => {
                const event = new CustomEvent('openAuthModal', { detail: 'signup' })
                window.dispatchEvent(event)
              }}
              className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-[12px] bg-brand-1 text-white font-semibold hover:bg-brand-2 hover:shadow-lg hover:shadow-brand-1/25 transition-all"
            >
              <CheckCircle2 className="w-5 h-5" />
              Create Free Account
            </button>
            <button
              onClick={() => {
                const event = new CustomEvent('openAuthModal', { detail: 'login' })
                window.dispatchEvent(event)
              }}
              className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-[12px] bg-white/10 border border-white/25 text-white font-semibold hover:bg-white/15 transition-all"
            >
              Login
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Landing

