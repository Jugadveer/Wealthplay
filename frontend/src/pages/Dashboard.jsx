import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'
import {
  BookOpen,
  TrendingUp,
  DollarSign,
  Target,
  Flame,
  Award,
  Home,
  BarChart3,
  Briefcase,
  Lightbulb,
} from 'lucide-react'

const Dashboard = () => {
  const { user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProfile()
  }, [])

  const fetchProfile = async () => {
    try {
      const response = await api.getProfile()
      setProfile(response.data)
    } catch (error) {
      console.error('Error fetching profile:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  // Calculate level info - updated XP requirements
  const levelMap = {
    beginner: { current: 0, xpNeeded: 750, next: 'Intermediate' },
    intermediate: { current: 750, xpNeeded: 1200, next: 'Advanced' },
    advanced: { current: 1200, xpNeeded: 2000, next: 'Expert' },
  }
  const levelInfo = levelMap[profile.level] || levelMap.beginner
  const currentXP = profile.xp || 0
  const xpInLevel = Math.max(0, currentXP - levelInfo.current)
  const xpForLevel = levelInfo.xpNeeded - levelInfo.current
  const xpPercent = xpForLevel > 0 ? Math.min(100, (xpInLevel / xpForLevel) * 100) : 0
  const xpUntilNext = Math.max(0, levelInfo.xpNeeded - currentXP)

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Dashboard Nav */}
      <div className="bg-white shadow-sm border-b border-muted-2">
        <div className="max-w-container mx-auto px-6 lg:px-10">
          <div className="flex items-center justify-between h-20">
            <h2 className="text-2xl font-bold text-text-main">
              Welcome back, {user?.username || 'User'}!
            </h2>
            <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-brand-1/10 border border-brand-1/20">
              <Flame className="w-4 h-4 text-brand-1" />
              <span className="text-sm font-semibold text-brand-1">
                {profile.streak || 0} day streak
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-container mx-auto px-6 py-10 lg:px-10">

        {/* Level Card */}
        <div className="mb-8 bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-8 shadow-card hover:shadow-card-hover transition-all duration-360">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="text-sm font-medium text-text-muted mb-2">Current Level</p>
              <h3 className="text-4xl font-bold text-text-main capitalize mb-1">
                {profile.level || 'Beginner'}
              </h3>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-brand-1">
                {currentXP} / {levelInfo.xpNeeded}
              </p>
              <p className="text-sm text-text-muted mt-1">XP</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <div className="w-full h-3 bg-white/50 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-1 to-brand-2 rounded-full transition-all duration-500 relative overflow-hidden"
                style={{ width: `${xpPercent}%` }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[progress-shimmer_2s_infinite]"></div>
              </div>
            </div>
          </div>
          <p className="text-sm text-text-muted">
            {xpUntilNext} XP until {levelInfo.next}
          </p>
        </div>

        {/* Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {/* Learn Card */}
          <Link
            to="/course"
            className="group bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20"
          >
            <div className="w-12 h-12 rounded-xl bg-accent-blue/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
              <BookOpen className="w-6 h-6 text-accent-blue" />
            </div>
            <h3 className="text-lg font-bold text-text-main mb-2">Learn</h3>
            <p className="text-sm text-text-muted mb-4">
              Bite-sized lessons on investing
            </p>
            <span className="text-sm font-semibold text-accent-blue group-hover:underline">
              Start Learning →
            </span>
          </Link>

          {/* Practice Card */}
          <Link
            to="/scenario"
            className="group bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20"
          >
            <div className="w-12 h-12 rounded-xl bg-accent-green/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
              <TrendingUp className="w-6 h-6 text-accent-green" />
            </div>
            <h3 className="text-lg font-bold text-text-main mb-2">Practice</h3>
            <p className="text-sm text-text-muted mb-4">
              Try virtual trading risk-free
            </p>
            <span className="text-sm font-semibold text-accent-green group-hover:underline">
              Open Simulator →
            </span>
          </Link>

          {/* Portfolio Card */}
          <Link
            to="/portfolio"
            className="group bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20"
          >
            <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
              <DollarSign className="w-6 h-6 text-brand-1" />
            </div>
            <h3 className="text-lg font-bold text-text-main mb-2">Portfolio</h3>
            <p className="text-sm text-text-muted mb-4">
              Track your investments
            </p>
            <span className="text-sm font-semibold text-brand-1 group-hover:underline">
              View Portfolio →
            </span>
          </Link>

          {/* Goals Card */}
          <Link
            to="/goals"
            className="group bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-transparent hover:border-brand-1/20"
          >
            <div className="w-12 h-12 rounded-xl bg-brand-2/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
              <Target className="w-6 h-6 text-brand-2" />
            </div>
            <h3 className="text-lg font-bold text-text-main mb-2">Goals</h3>
            <p className="text-sm text-text-muted mb-4">
              Plan your financial future
            </p>
            <span className="text-sm font-semibold text-brand-2 group-hover:underline">
              Set Goals →
            </span>
          </Link>
        </div>

        {/* Achievements Section */}
        <div className="mb-12">
          <div className="flex items-center gap-2 mb-6">
            <Award className="w-6 h-6 text-text-main" />
            <h2 className="text-2xl font-bold text-text-main">Your Achievements</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* First Step */}
            <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-360 text-center border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-purple-100 flex items-center justify-center mx-auto mb-4">
                <Home className="w-8 h-8 text-purple-600" />
              </div>
              <h4 className="font-bold text-text-main">First Step</h4>
            </div>

            {/* First Trade */}
            <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-360 text-center border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-blue-100 flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-8 h-8 text-blue-600" />
              </div>
              <h4 className="font-bold text-text-main">First Trade</h4>
            </div>

            {/* 5 Day Streak */}
            <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-360 text-center border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-brand-1/10 flex items-center justify-center mx-auto mb-4">
                <Flame className="w-8 h-8 text-brand-1" />
              </div>
              <h4 className="font-bold text-text-main">5 Day Streak</h4>
            </div>

            {/* Portfolio Pro */}
            <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-360 text-center border border-transparent hover:border-brand-1/20">
              <div className="w-16 h-16 rounded-xl bg-green-100 flex items-center justify-center mx-auto mb-4">
                <Briefcase className="w-8 h-8 text-green-600" />
              </div>
              <h4 className="font-bold text-text-main">Portfolio Pro</h4>
            </div>
          </div>
        </div>

        {/* Today's Tip */}
        <div className="bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-8 shadow-card">
          <div className="flex items-center gap-2 mb-4">
            <Lightbulb className="w-5 h-5 text-brand-1" />
            <h3 className="text-lg font-semibold text-text-main">Today's Tip</h3>
          </div>
          <p className="text-text-muted leading-relaxed">
            Don't put all your eggs in one basket. Diversification helps protect your
            investments from market volatility.
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard


