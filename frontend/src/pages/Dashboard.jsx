import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useAchievements } from '../contexts/AchievementContext'
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
  CheckCircle2,
  Sparkles,
  Trophy,
} from 'lucide-react'
import MarketView from '../components/MarketView'

const Dashboard = () => {
  const { user } = useAuth()
  const { checkAchievements } = useAchievements()
  const [profile, setProfile] = useState(null)
  const [portfolioPL, setPortfolioPL] = useState(0)
  const [portfolioPLPercent, setPortfolioPLPercent] = useState(0)
  const [portfolioBalance, setPortfolioBalance] = useState(50000)
  const [portfolioValue, setPortfolioValue] = useState(50000)
  const [insight, setInsight] = useState('')
  const [challengeStreak, setChallengeStreak] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProfile()
    fetchPortfolioPL()
    generateInsight()
    
    checkAchievements()
    
  }, [])

  useEffect(() => {
    const handlePortfolioUpdated = () => {
      fetchPortfolioPL()
      generateInsight()
    }

    window.addEventListener('portfolio-updated', handlePortfolioUpdated)
    return () => window.removeEventListener('portfolio-updated', handlePortfolioUpdated)
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

  const fetchPortfolioPL = async () => {
    try {
      const response = await api.getPortfolio()
      if (response.data) {
        setPortfolioPL(response.data.total_pnl || 0)
        setPortfolioPLPercent(response.data.total_pnl_percent || 0)
        setPortfolioBalance(response.data.balance || 50000)
        setPortfolioValue(response.data.total_value || 50000)
      }
    } catch (error) {
      console.error('Error fetching portfolio P/L:', error)
    }
  }

  const generateInsight = async () => {
    try {
      
      const [profileRes, portfolioRes, challengeRes] = await Promise.all([
        api.getProfile().catch(() => ({ data: null })),
        api.getPortfolio().catch(() => ({ data: null })),
        api.getUserChallengeStats().catch(() => ({ data: null }))
      ])

      const profileData = profileRes?.data
      const portfolioData = portfolioRes?.data
      const challengeData = challengeRes?.data
      setChallengeStreak(challengeData?.current_streak ?? profileData?.streak ?? 0)

      
      let insightText = ''
      
      if (portfolioData?.total_pnl_percent > 10) {
        insightText = `Excellent portfolio performance! You're up ${portfolioData.total_pnl_percent.toFixed(1)}%. Consider taking some profits to lock in gains.`
      } else if (portfolioData?.total_pnl_percent < -5) {
        insightText = `Your portfolio is down ${Math.abs(portfolioData.total_pnl_percent).toFixed(1)}%. Review your holdings and consider rebalancing.`
      } else if (challengeData?.current_streak >= 7) {
        insightText = `Amazing ${challengeData.current_streak}-day streak! Keep the momentum going with daily practice.`
      } else if (challengeData?.scenario_score > 500) {
        insightText = `Great work on scenarios! You've scored ${challengeData.scenario_score} points. Try the advanced scenarios to challenge yourself further.`
      } else if (profileData?.xp < 100) {
        insightText = `Welcome! Start by completing your first course module to earn XP and unlock new features.`
      } else if (portfolioData?.holdings?.length === 0) {
        insightText = `Your portfolio is empty. Make your first trade to start building your investment skills!`
      } else {
        insightText = `Keep learning and practicing! Review your portfolio regularly and try new scenarios to improve your financial decision-making.`
      }

      setInsight(insightText)
    } catch (error) {
      console.error('Error generating insight:', error)
      setInsight('Keep learning and practicing! Review your portfolio regularly and try new scenarios to improve your financial decision-making.')
      setChallengeStreak(0)
    }
  }

  if (loading || !profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  
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
  const levelNumber = Math.floor(currentXP / 100) || 1
  const levelRingCircumference = 2 * Math.PI * 30
  const levelRingOffset = levelRingCircumference - (xpPercent / 100) * levelRingCircumference

  
  const RecentAchievements = () => {
    const [recentAchievements, setRecentAchievements] = useState([])
    const { user } = useAuth() 

    useEffect(() => {
      
      setRecentAchievements([])
      
      const fetchRecent = async () => {
        if (!user) {
          setRecentAchievements([])
          return
        }
        
        try {
          const response = await api.getAchievements()
          if (response.data && response.data.achievements) {
            
            
            
            const unlocked = response.data.achievements
              .filter(a => {
                
                
                
                
                if (a.unlocked !== true) return false
                if (!a.unlocked_at || typeof a.unlocked_at !== 'string' || a.unlocked_at.length === 0) return false
                
                const date = new Date(a.unlocked_at)
                if (isNaN(date.getTime())) return false
                return true
              })
              .sort((a, b) => {
                if (!a.unlocked_at) return 1
                if (!b.unlocked_at) return -1
                return new Date(b.unlocked_at) - new Date(a.unlocked_at)
              })
              .slice(0, 3)
            setRecentAchievements(unlocked)
          } else {
            setRecentAchievements([])
          }
        } catch (error) {
          console.error('Error fetching recent achievements:', error)
          setRecentAchievements([]) 
        }
      }
      fetchRecent()
    }, [user]) 

    const iconMap = {
      sparkles: Sparkles,
      flame: Flame,
      trophy: Trophy,
      'trending-up': TrendingUp,
      briefcase: Briefcase,
      target: Target,
      'bar-chart-3': BarChart3,
      award: Award,
    }

    if (recentAchievements.length === 0) {
      return (
        <div className="bg-retro-surface rounded-xl p-6 shadow-card border border-brand-1/10">
          <div className="text-center">
            <Trophy className="w-12 h-12 text-text-muted mx-auto mb-3 opacity-50" />
            <p className="text-sm text-text-muted">No achievements yet.</p>
            <p className="text-xs text-text-muted mt-1">Start trading or complete quizzes to unlock achievements!</p>
          </div>
        </div>
      )
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recentAchievements.map((achievement) => {
          const Icon = iconMap[achievement.icon_name] || Trophy
          return (
            <div key={achievement.id} className="bg-retro-surface rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-360 border border-brand-1/10 hover:border-brand-1">
              <div className="flex items-center gap-4 mb-3">
                <div className="w-12 h-12 rounded-xl bg-brand-1/10 border border-brand-1/10 flex items-center justify-center">
                  <Icon className="w-6 h-6 text-text-main" />
                </div>
                <div>
                  <h4 className="font-bold text-text-main">{achievement.name}</h4>
                  <p className="text-sm text-text-muted">{achievement.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 text-accent-green">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-sm font-semibold">Unlocked</span>
              </div>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg text-text-main">
      {}
      <div className="max-w-container mx-auto px-6 pt-8 pb-4 lg:px-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-authority-navy mb-2">
              Welcome Back, Trader
            </h1>
            <p className="text-text-muted">
              Track your progress and continue your learning journey.
            </p>
          </div>
          <div className="flex items-center gap-2 px-4 py-2 rounded-[12px] bg-brand-1/10 border border-brand-1/20 shadow-sm">
            <Flame className="w-5 h-5 text-brand-1" />
            <span className="text-sm font-bold text-brand-1">
              {challengeStreak} Day Streak
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-container mx-auto px-6 py-10 lg:px-10">

        {}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {}
          <div className="bg-retro-surface rounded-2xl p-6 shadow-card card-pop">
            <div className="flex items-center gap-4 mb-4">
              <div className="relative w-16 h-16 flex items-center justify-center">
                <svg className="absolute inset-0 w-16 h-16 -rotate-90" viewBox="0 0 72 72" aria-hidden="true">
                  <defs>
                    <linearGradient id="levelRingGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#FF6B35" />
                      <stop offset="100%" stopColor="#F59E0B" />
                    </linearGradient>
                  </defs>
                  <circle cx="36" cy="36" r="30" fill="none" stroke="rgba(15,23,42,0.1)" strokeWidth="6" />
                  <circle
                    cx="36"
                    cy="36"
                    r="30"
                    fill="none"
                    stroke="url(#levelRingGradient)"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeDasharray={levelRingCircumference}
                    strokeDashoffset={levelRingOffset}
                    className="transition-all duration-500"
                  />
                </svg>
                <span className="text-text-main font-bold text-xl number-tabular">{levelNumber}</span>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Level</p>
                <p className="text-2xl font-bold text-text-main capitalize">
                  {profile.level || 'Beginner'}
                </p>
              </div>
            </div>
            <div className="text-sm text-text-muted number-tabular">
              {currentXP} / {levelInfo.xpNeeded} XP
            </div>
            <div className="mt-3 w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${xpPercent}%`,
                  backgroundColor: xpPercent >= 100 ? '#F59E0B' : '#FF6B35',
                }}
              ></div>
            </div>
            <p className="text-xs text-text-muted mt-2 number-tabular">{xpUntilNext} XP to {levelInfo.next}</p>
          </div>

          {}
          <div className="bg-retro-surface rounded-2xl p-6 shadow-card card-pop">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="w-5 h-5 text-brand-1" />
              <p className="text-sm text-text-muted">Balance Remaining</p>
            </div>
            <p className="text-2xl font-bold text-text-main number-tabular">
              ₹{portfolioBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
            <p className="text-xs text-text-muted mt-1 number-tabular">
              Total Value: ₹{portfolioValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
            </p>
          </div>

          {}
          <div className="bg-retro-surface rounded-2xl p-6 shadow-card card-pop">
            <div className="flex items-center gap-3 mb-2">
              <TrendingUp className={`w-5 h-5 ${portfolioPLPercent >= 0 ? 'text-accent-green' : 'text-accent-red'}`} />
              <p className="text-sm text-text-muted">Portfolio P&L</p>
            </div>
            <div className={`inline-flex items-center px-4 py-1.5 rounded-full number-tabular ${portfolioPLPercent >= 0 ? 'bg-accent-green/15 text-accent-green' : 'bg-accent-red/15 text-accent-red'}`}>
              <p className="text-2xl font-bold">
                {portfolioPLPercent >= 0 ? '+' : ''}{portfolioPLPercent.toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {}
          <Link
            to="/course"
            className="group bg-retro-surface rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-brand-1/10 hover:border-brand-1"
          >
            <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
              <BookOpen className="w-6 h-6 text-brand-2" />
            </div>
            <h3 className="text-lg font-bold text-text-main mb-2">Learn</h3>
            <p className="text-sm text-text-muted mb-4">
              Bite-sized lessons on investing
            </p>
            <span className="text-sm font-semibold text-brand-2 group-hover:underline">
              Start Learning →
            </span>
          </Link>

          {}
          <Link
            to="/scenario"
            className="group bg-retro-surface rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-brand-1/10 hover:border-brand-1"
          >
            <div className="w-12 h-12 rounded-xl bg-brand-1/10 border border-brand-1/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-360">
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

          {}
          <Link
            to="/portfolio"
            className="group bg-retro-surface rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-brand-1/10 hover:border-brand-1"
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

          {}
          <Link
            to="/goals"
            className="group bg-retro-surface rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360 border border-brand-1/10 hover:border-brand-1"
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

        {}
        <div className="mb-12">
          <MarketView />
        </div>

        {}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-text-main">Recent Achievements</h2>
            <Link
              to="/achievements"
              className="text-sm font-semibold text-brand-1 hover:underline cursor-pointer"
            >
              View All →
            </Link>
          </div>
          <RecentAchievements />
        </div>

        {}
        <div className="bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-8 shadow-card border border-brand-1/20">
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="w-6 h-6 text-brand-1" />
            <h3 className="text-lg font-bold text-text-main">Nex's Insight •</h3>
          </div>
          <p className="text-text-muted leading-relaxed">
            {insight || 'Keep learning and practicing! Review your portfolio regularly and try new scenarios to improve your financial decision-making.'}
          </p>
        </div>
      </div>
    </div>
  )
}

export default Dashboard


