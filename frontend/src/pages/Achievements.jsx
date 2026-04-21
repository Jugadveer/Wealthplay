import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useGlobalData } from '../contexts/GlobalDataContext'
import api from '../utils/api'
import {
  ArrowLeft,
  Trophy,
  Sparkles,
  Flame,
  TrendingUp,
  Target,
  BarChart3,
  Award,
  Briefcase,
  Zap,
  Shield,
  BookOpen,
  CheckCircle2,
  Sun,
  Lock,
  Star,
  Loader2,
} from 'lucide-react'

const iconMap = {
  trophy: Trophy,
  sparkles: Sparkles,
  flame: Flame,
  'trending-up': TrendingUp,
  target: Target,
  'bar-chart-3': BarChart3,
  award: Award,
  briefcase: Briefcase,
  zap: Zap,
  shield: Shield,
  'book-open': BookOpen,
  'check-circle-2': CheckCircle2,
  sun: Sun,
  star: Star,
}


const ALL_ACHIEVEMENTS = [
  
  { id: 'first_trade', name: 'First Trade', description: 'Execute your first stock trade', icon_name: 'briefcase', category: 'trading', xp_reward: 25, requirement: 'Complete 1 trade' },
  { id: 'portfolio_pro', name: 'Portfolio Pro', description: 'Build a diversified portfolio with 5+ stocks', icon_name: 'briefcase', category: 'trading', xp_reward: 100, requirement: 'Hold 5 different stocks' },
  { id: 'diversified', name: 'Diversified Investor', description: 'Own stocks across 3+ different sectors', icon_name: 'target', category: 'trading', xp_reward: 75, requirement: '3+ sectors in portfolio' },
  { id: 'risk_taker', name: 'Risk Taker', description: 'Make a trade worth over ₹10,000', icon_name: 'zap', category: 'trading', xp_reward: 50, requirement: 'Single trade ≥ ₹10,000' },
  { id: 'conservative', name: 'Conservative Investor', description: 'Maintain positive returns for 7+ days', icon_name: 'shield', category: 'trading', xp_reward: 75, requirement: '7+ days positive P&L' },
  
  
  { id: 'first_lesson', name: 'First Lesson', description: 'Complete your first course module', icon_name: 'book-open', category: 'learning', xp_reward: 20, requirement: 'Complete 1 module' },
  { id: 'course_complete', name: 'Course Graduate', description: 'Complete an entire course', icon_name: 'award', category: 'learning', xp_reward: 150, requirement: 'Finish all modules in 1 course' },
  { id: 'quiz_ace', name: 'Quiz Ace', description: 'Score 100% on any course quiz', icon_name: 'star', category: 'learning', xp_reward: 50, requirement: 'Perfect score on a quiz' },
  { id: 'perfect_quiz', name: 'Perfect Quiz', description: 'Score 80%+ on a scenario quiz', icon_name: 'check-circle-2', category: 'learning', xp_reward: 100, requirement: '≥80% on scenario quiz' },
  { id: 'knowledge_seeker', name: 'Knowledge Seeker', description: 'Complete 10 course modules', icon_name: 'book-open', category: 'learning', xp_reward: 200, requirement: '10 modules completed' },
  
  
  { id: 'streak_5', name: '5-Day Streak', description: 'Log in and participate for 5 consecutive days', icon_name: 'flame', category: 'consistency', xp_reward: 50, requirement: '5 consecutive days' },
  { id: 'streak_10', name: '10-Day Streak', description: 'Maintain a 10-day activity streak', icon_name: 'flame', category: 'consistency', xp_reward: 100, requirement: '10 consecutive days' },
  { id: 'streak_30', name: '30-Day Streak', description: 'An incredible 30-day streak of learning', icon_name: 'flame', category: 'consistency', xp_reward: 300, requirement: '30 consecutive days' },
  { id: 'daily_trader', name: 'Daily Trader', description: 'Make trades on 3 different days', icon_name: 'sun', category: 'consistency', xp_reward: 40, requirement: 'Trade on 3 separate days' },
  
  
  { id: 'xp_100', name: 'Rising Star', description: 'Earn your first 100 XP', icon_name: 'sparkles', category: 'milestone', xp_reward: 25, requirement: 'Earn 100 XP total' },
  { id: 'xp_500', name: 'XP Hunter', description: 'Accumulate 500 XP', icon_name: 'sparkles', category: 'milestone', xp_reward: 50, requirement: 'Earn 500 XP total' },
  { id: 'xp_milestone', name: 'XP Legend', description: 'Reach 1000 XP and beyond', icon_name: 'trophy', category: 'milestone', xp_reward: 150, requirement: 'Earn 1000 XP total' },
  { id: 'scenario_master', name: 'Scenario Master', description: 'Complete 5 financial scenario quizzes', icon_name: 'target', category: 'milestone', xp_reward: 100, requirement: 'Finish 5 scenario quizzes' },
  { id: 'stock_predictor', name: 'Stock Oracle', description: 'Make 10 stock predictions', icon_name: 'trending-up', category: 'milestone', xp_reward: 75, requirement: '10 stock predictions' },
  { id: 'profit_maker', name: 'Profit Maker', description: 'Achieve 10% portfolio returns', icon_name: 'trending-up', category: 'milestone', xp_reward: 200, requirement: '≥10% portfolio returns' },
]

const categoryInfo = {
  trading: { label: '📈 Trading', color: 'from-accent-green/15 to-brand-1/10' },
  learning: { label: '📚 Learning', color: 'from-accent-blue/15 to-brand-1/10' },
  consistency: { label: '🔥 Consistency', color: 'from-brand-2/20 to-brand-1/10' },
  milestone: { label: '🏆 Milestone', color: 'from-brand-1/20 to-brand-2/10' },
}

const Achievements = () => {
  const navigate = useNavigate()
  const {
    achievements: cachedAchievements,
    refreshAchievements,
    loadingAchievements,
  } = useGlobalData()
  const [serverAchievements, setServerAchievements] = useState(cachedAchievements || [])
  const [loading, setLoading] = useState(!(cachedAchievements && cachedAchievements.length > 0))
  const [stats, setStats] = useState({ total_unlocked: 0, total_available: 0 })

  useEffect(() => {
    fetchAchievements()
  }, [])

  useEffect(() => {
    if (!Array.isArray(cachedAchievements)) return
    setServerAchievements(cachedAchievements)
    setStats({
      total_unlocked: cachedAchievements.filter((a) => a.unlocked).length,
      total_available: cachedAchievements.length || ALL_ACHIEVEMENTS.length,
    })
    if (cachedAchievements.length > 0) {
      setLoading(false)
    }
  }, [cachedAchievements])

  const fetchAchievements = async () => {
    try {
      const achievementsData = typeof refreshAchievements === 'function'
        ? await refreshAchievements(true)
        : null

      if (Array.isArray(achievementsData)) {
        setServerAchievements(achievementsData)
        setStats({
          total_unlocked: achievementsData.filter((a) => a.unlocked).length,
          total_available: achievementsData.length || ALL_ACHIEVEMENTS.length,
        })
        return
      }

      const response = await api.getAchievements()
      if (response.data) {
        const achievementsList = response.data.achievements || []
        setServerAchievements(achievementsList)
        setStats({
          total_unlocked: response.data.total_unlocked || 0,
          total_available: response.data.total_available || achievementsList.length || ALL_ACHIEVEMENTS.length,
        })
      }
    } catch (error) {
      console.error('Error fetching achievements:', error)
    } finally {
      setLoading(false)
    }
  }

  
  const mergedAchievements = ALL_ACHIEVEMENTS.map(ach => {
    const serverMatch = serverAchievements.find(sa => sa.id === ach.id)
    return {
      ...ach,
      unlocked: serverMatch?.unlocked || false,
      unlocked_at: serverMatch?.unlocked_at || null,
      progress: serverMatch?.progress || 0,
      progress_max: serverMatch?.progress_max || 1,
    }
  })

  
  const groupedAchievements = mergedAchievements.reduce((acc, achievement) => {
    const category = achievement.category || 'general'
    if (!acc[category]) acc[category] = []
    acc[category].push(achievement)
    return acc
  }, {})

  const totalUnlocked = mergedAchievements.filter(a => a.unlocked).length
  const totalAvailable = mergedAchievements.length
  const progressPercent = totalAvailable > 0 
    ? ((totalUnlocked / totalAvailable) * 100).toFixed(1)
    : 0

  if (loading && loadingAchievements && serverAchievements.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-retro-bg">
        <Loader2 className="w-12 h-12 text-brand-1 animate-spin" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg text-text-main">
      {}
      <header className="bg-retro-surface border-b border-brand-1/20 px-6 py-8 lg:px-10">
        <div className="max-w-container mx-auto">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-brand-1/20 hover:bg-brand-1/40 border border-brand-1/30 text-brand-1 px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4 text-text-main">Achievements</h1>
            <p className="text-xl text-text-muted">
              Track your progress and unlock rewards
            </p>
          </div>
          
          {}
          <div className="mt-8 max-w-2xl mx-auto">
            <div className="bg-retro-surface backdrop-blur-sm rounded-xl p-6 border border-brand-1/20">
              <div className="flex items-center justify-between mb-4">
                <span className="text-text-muted">Overall Progress</span>
                <span className="text-text-main font-bold">
                  {totalUnlocked} / {totalAvailable}
                </span>
              </div>
              <div className="w-full h-3 bg-retro-board rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${progressPercent}%`,
                    backgroundColor: progressPercent >= 100 ? '#f59e0b' : '#ff6b35',
                  }}
                />
              </div>
              <p className="text-center text-text-muted mt-2 text-sm">
                {progressPercent}% Complete
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {}
        {Object.entries(groupedAchievements).map(([category, categoryAchievements]) => {
          const info = categoryInfo[category] || { label: category, color: 'from-brand-1/10 to-muted-2/10' }
          const unlockedCount = categoryAchievements.filter(a => a.unlocked).length
          
          return (
            <div key={category} className="mb-12">
              <div className="flex items-center justify-between mb-6">
                <h2 className={`text-2xl font-bold text-text-main px-3 py-1.5 rounded-pill border border-brand-1/15 bg-gradient-to-r ${info.color}`}>
                  {info.label}
                </h2>
                <span className="text-sm text-text-muted font-semibold">
                  {unlockedCount} / {categoryAchievements.length} unlocked
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {categoryAchievements.map((achievement) => {
                  const Icon = iconMap[achievement.icon_name] || Trophy
                  const isUnlocked = achievement.unlocked

                  return (
                    <div
                      key={achievement.id}
                      className={`bg-retro-surface/80 rounded-xl p-6 shadow-card border-2 transition-all duration-300 ${
                        isUnlocked
                          ? 'border-brand-1/50 hover:border-brand-1 hover:shadow-[0_0_20px_rgba(255,107,53,0.2)]'
                          : 'border-brand-1/10 opacity-70'
                      }`}
                    >
                      <div className="flex items-start gap-4 mb-4">
                        <div
                          className={`w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0 ${
                            isUnlocked
                              ? 'bg-brand-1/10 border border-brand-1/20'
                              : 'bg-retro-surface border border-brand-1/10'
                          }`}
                        >
                          {isUnlocked ? (
                            <Icon className="w-8 h-8 text-text-main" />
                          ) : (
                            <Lock className="w-8 h-8 text-text-muted" />
                          )}
                        </div>
                        <div className="flex-1">
                          <h3 className="text-lg font-bold text-text-main mb-1">
                            {achievement.name}
                          </h3>
                          <p className="text-sm text-text-muted mb-2">
                            {achievement.description}
                          </p>
                          {}
                          <div className="flex items-center gap-2 mb-2">
                            <Target className="w-3 h-3 text-text-muted" />
                            <span className="text-xs text-text-muted font-medium">
                              {achievement.requirement}
                            </span>
                          </div>
                          {achievement.xp_reward > 0 && (
                            <div className="flex items-center gap-2">
                              <Award className="w-4 h-4 text-accent-green" />
                              <span className="text-sm font-semibold text-accent-green">
                                +{achievement.xp_reward} XP
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {}
                      <div className="pt-4 border-t border-brand-1/10">
                        {isUnlocked ? (
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 text-accent-green">
                              <CheckCircle2 className="w-4 h-4" />
                              <span className="text-sm font-semibold">Unlocked!</span>
                            </div>
                            {achievement.unlocked_at && (
                              <p className="text-xs text-text-muted">
                                {new Date(achievement.unlocked_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 text-text-muted">
                            <Lock className="w-4 h-4" />
                            <span className="text-sm font-medium">Locked</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </main>
    </div>
  )
}

export default Achievements
