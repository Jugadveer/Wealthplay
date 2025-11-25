import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
}

const categoryColors = {
  trading: 'bg-blue-100 text-blue-600',
  learning: 'bg-green-100 text-green-600',
  consistency: 'bg-orange-100 text-orange-600',
  milestone: 'bg-purple-100 text-purple-600',
}

const Achievements = () => {
  const navigate = useNavigate()
  const [achievements, setAchievements] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total_unlocked: 0, total_available: 0 })

  useEffect(() => {
    fetchAchievements()
  }, [])

  const fetchAchievements = async () => {
    try {
      const response = await api.getAchievements()
      if (response.data) {
        setAchievements(response.data.achievements || [])
        setStats({
          total_unlocked: response.data.total_unlocked || 0,
          total_available: response.data.total_available || 0,
        })
      }
    } catch (error) {
      console.error('Error fetching achievements:', error)
    } finally {
      setLoading(false)
    }
  }

  // Group achievements by category
  const groupedAchievements = achievements.reduce((acc, achievement) => {
    const category = achievement.category || 'general'
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push(achievement)
    return acc
  }, {})

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  const progressPercent = stats.total_available > 0 
    ? (stats.total_unlocked / stats.total_available * 100).toFixed(1)
    : 0

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <header className="bg-gradient-to-r from-brand-1 to-brand-2 text-white px-6 py-8 lg:px-10">
        <div className="max-w-container mx-auto">
          <div className="flex items-center justify-between mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </button>
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">Achievements</h1>
            <p className="text-xl text-white/90">
              Track your progress and unlock rewards
            </p>
          </div>
          
          {/* Progress Stats */}
          <div className="mt-8 max-w-2xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
              <div className="flex items-center justify-between mb-4">
                <span className="text-white/90">Progress</span>
                <span className="text-white font-bold">
                  {stats.total_unlocked} / {stats.total_available}
                </span>
              </div>
              <div className="w-full h-3 bg-white/20 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white rounded-full transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
              <p className="text-center text-white/90 mt-2 text-sm">
                {progressPercent}% Complete
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Achievements by Category */}
        {Object.entries(groupedAchievements).map(([category, categoryAchievements]) => (
          <div key={category} className="mb-12">
            <h2 className="text-2xl font-bold text-text-main mb-6 capitalize">
              {category.replace('_', ' ')}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {categoryAchievements.map((achievement) => {
                const Icon = iconMap[achievement.icon_name] || Trophy
                const isUnlocked = achievement.unlocked

                return (
                  <div
                    key={achievement.id}
                    className={`bg-white rounded-xl p-6 shadow-card border-2 transition-all duration-300 ${
                      isUnlocked
                        ? 'border-brand-1 hover:shadow-card-hover'
                        : 'border-gray-200 opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-4 mb-4">
                      <div
                        className={`w-16 h-16 rounded-full flex items-center justify-center flex-shrink-0 ${
                          isUnlocked
                            ? 'bg-gradient-to-br from-brand-1 to-brand-2'
                            : 'bg-gray-200'
                        }`}
                      >
                        {isUnlocked ? (
                          <Icon className="w-8 h-8 text-white" />
                        ) : (
                          <Lock className="w-8 h-8 text-gray-400" />
                        )}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-text-main mb-1">
                          {achievement.name}
                        </h3>
                        <p className="text-sm text-text-muted mb-3">
                          {achievement.description}
                        </p>
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
                    {isUnlocked && achievement.unlocked_at && (
                      <div className="pt-4 border-t border-gray-200">
                        <p className="text-xs text-text-muted">
                          Unlocked: {new Date(achievement.unlocked_at).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </main>
    </div>
  )
}

export default Achievements

