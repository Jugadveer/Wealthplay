import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api, { axios } from '../utils/api'
import {
  ArrowLeft,
  Play,
  Target,
  TrendingUp,
  Award,
  Clock,
  BarChart3,
  Trophy,
  Flame,
  Star,
  Sparkles,
  Eye,
} from 'lucide-react'

const ScenarioHome = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [totalScore, setTotalScore] = useState(0)
  const [stockScore, setStockScore] = useState(0)
  const [scenarioScore, setScenarioScore] = useState(0)
  const [currentStreak, setCurrentStreak] = useState(0)
  const [winRate, setWinRate] = useState(0)
  const [leaderboard, setLeaderboard] = useState([])
  const [leaderboardTab, setLeaderboardTab] = useState('scores') // 'scores' or 'streaks'

  useEffect(() => {
    fetchUserStats()
  }, [])

  useEffect(() => {
    fetchLeaderboard()
  }, [leaderboardTab])

  const fetchUserStats = async () => {
    try {
      const response = await api.getUserChallengeStats()
      if (response.data) {
        setTotalScore(response.data.total_score || 0)
        setStockScore(response.data.stock_score || 0)
        setScenarioScore(response.data.scenario_score || 0)
        setCurrentStreak(response.data.current_streak || 0)
        setWinRate(response.data.win_rate || 0)
      }
    } catch (error) {
      console.error('Error fetching user stats:', error)
      setTotalScore(0)
      setStockScore(0)
      setScenarioScore(0)
      setCurrentStreak(0)
      setWinRate(0)
    }
  }

  const fetchLeaderboard = async () => {
    try {
      const response = await api.getLeaderboard(leaderboardTab === 'streaks' ? 'streaks' : 'scores')
      if (response.data && response.data.leaderboard) {
        setLeaderboard(response.data.leaderboard)
      }
    } catch (error) {
      console.error('Error fetching leaderboard:', error)
      // Fallback to empty array
      setLeaderboard([])
    }
  }

  const startFinancialScenarios = async () => {
    setLoading(true)
    try {
      const { axios } = await import('../utils/api')
      const { getCsrfToken } = await import('../utils/api')
      const csrfToken = await getCsrfToken()
      
      const response = await axios.post('/api/scenario/api/start/', {}, {
        headers: {
          'X-CSRFToken': csrfToken || '',
        },
        withCredentials: true,
      })
      
      if (response.data && response.data.success && response.data.runId) {
        navigate(`/scenario/quiz/${response.data.runId}`)
      } else {
        console.error('Failed to start quiz:', response.data)
        setLoading(false)
      }
    } catch (error) {
      console.error('Error starting quiz:', error)
      setLoading(false)
    }
  }

  const startStockChallenge = async () => {
    setLoading(true)
    try {
      // Navigate to stock prediction challenge
      navigate('/scenario/stock-challenge')
    } catch (error) {
      console.error('Error starting stock challenge:', error)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header - Matching design */}
      <header className="bg-gradient-to-r from-brand-1 to-brand-2 text-white px-6 py-12 lg:px-10">
        <div className="max-w-container mx-auto">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Go to Dashboard
            </button>
          </div>
          <div className="text-center">
            <h1 className="text-5xl font-bold mb-4">Challenge Arena</h1>
            <p className="text-xl text-white/90">
              Test your trading knowledge and compete with others
            </p>
          </div>
          
          {/* Stats Cards in Header */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 max-w-4xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
              <Eye className="w-8 h-8 mx-auto mb-3 text-white" />
              <p className="text-4xl font-bold mb-2 text-white">{totalScore}</p>
              <p className="text-sm text-white/90">Total Score</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
              <Sparkles className="w-8 h-8 mx-auto mb-3 text-white" />
              <p className="text-4xl font-bold mb-2 text-white">{currentStreak}</p>
              <p className="text-sm text-white/90">Day Streak</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
              <Trophy className="w-8 h-8 mx-auto mb-3 text-white" />
              <p className="text-4xl font-bold mb-2 text-white">{winRate.toFixed(1)}%</p>
              <p className="text-sm text-white/90">Win Rate</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2">Total Score</p>
            <p className="text-3xl font-bold text-brand-1">{totalScore}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Stock Game Score
            </p>
            <p className="text-3xl font-bold text-accent-green">{stockScore}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Scenario Score
            </p>
            <p className="text-3xl font-bold text-brand-2">{scenarioScore}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <Star className="w-4 h-4" />
              Current Streak
            </p>
            <p className="text-3xl font-bold text-brand-2">{currentStreak}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Financial Scenarios Card - Matching design */}
            <div className="bg-gradient-to-br from-brand-1 to-brand-2 rounded-xl p-8 shadow-card text-white">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                  <Target className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2">Financial Scenarios</h2>
                  <p className="text-white/90 text-sm">
                    Navigate real-world financial situations and make critical decisions. Each choice impacts your score and teaches valuable lessons.
                </p>
                </div>
              </div>
                <button
                  onClick={startFinancialScenarios}
                  disabled={loading}
                className="w-full px-6 py-3 bg-white text-brand-1 rounded-lg font-bold hover:bg-white/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                {loading ? 'Starting...' : 'Start Financial Scenarios'}
                </button>
            </div>

            {/* Stock Prediction Challenge Card - Matching design */}
            <div className="bg-gradient-to-br from-accent-green to-green-600 rounded-xl p-8 shadow-card text-white">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                  <BarChart3 className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2">Stock Prediction Game</h2>
                  <p className="text-white/90 text-sm">
                    Predict market movements and test your analysis skills. Compete for the top spot on the leaderboard!
                </p>
                </div>
              </div>
                <button
                  onClick={startStockChallenge}
                  disabled={loading}
                className="w-full px-6 py-3 bg-white text-green-600 rounded-lg font-bold hover:bg-white/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                {loading ? 'Starting...' : 'Start Game'}
                </button>
            </div>

            {/* Feature Cards - Matching design */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl p-6 shadow-card border border-muted-2">
                <Target className="w-8 h-8 mb-3 text-brand-1" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Real Market Scenarios</h3>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-card border border-muted-2">
                <Sparkles className="w-8 h-8 mb-3 text-brand-2" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Instant Feedback</h3>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-card border border-muted-2">
                <Trophy className="w-8 h-8 mb-3 text-accent-green" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Earn XP & Rewards</h3>
              </div>
            </div>
          </div>

          {/* Leaderboard Sidebar - Matching design */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-card p-6 border border-muted-2 sticky top-20">
              <div className="flex items-center gap-3 mb-6">
                <Trophy className="w-8 h-8 text-brand-2" />
                <h3 className="text-xl font-bold text-text-main">Leaderboard</h3>
              </div>

              {/* Leaderboard List - Matching design */}
              <div className="space-y-3">
                {leaderboard.length > 0 ? (
                  leaderboard.map((user, idx) => (
                    <div
                      key={user.username}
                      className="flex items-center gap-3 p-3 rounded-lg bg-muted-1 hover:bg-muted-2 transition-colors"
                    >
                      {idx === 0 && <Trophy className="w-6 h-6 text-yellow-500 flex-shrink-0" />}
                      {idx === 1 && <Trophy className="w-6 h-6 text-gray-400 flex-shrink-0" />}
                      {idx === 2 && <Trophy className="w-6 h-6 text-orange-500 flex-shrink-0" />}
                      {idx > 2 && <div className="w-6 h-6 flex-shrink-0"></div>}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                        idx === 0 ? 'bg-purple-500' :
                        idx === 1 ? 'bg-blue-500' :
                        idx === 2 ? 'bg-orange-500' :
                        'bg-brand-1'
                      }`}>
                        <span className="text-white font-bold text-sm">
                          {user.username.substring(0, 2).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-text-main truncate">
                          {user.username}
                        </p>
                        <p className="text-sm text-text-muted">
                          {leaderboardTab === 'scores' 
                            ? `${user.total_score}`
                            : `${user.current_streak}`
                          }
                        </p>
                      </div>
                      {idx < 3 && (
                        <div className={`h-1 flex-1 rounded-full ${
                          idx === 0 ? 'bg-yellow-500' :
                          idx === 1 ? 'bg-gray-400' :
                          'bg-orange-500'
                        }`}></div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-text-muted">
                    <Trophy className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No leaderboard data yet</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default ScenarioHome
