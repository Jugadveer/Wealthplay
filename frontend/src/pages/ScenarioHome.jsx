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
  const [leaderboardTab, setLeaderboardTab] = useState('scores') 

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
      
      setLeaderboard([])
    }
  }

  const startFinancialScenarios = async () => {
    setLoading(true)
    try {
      const response = await api.startQuiz()
      
      if (response.data && response.data.success && response.data.runId) {
        navigate(`/scenario/quiz/${response.data.runId}`)
      } else {
        console.error('Failed to start quiz:', response.data)
        alert('Failed to start scenario. Please try again.')
        setLoading(false)
      }
    } catch (error) {
      console.error('Error starting quiz:', error)
      alert('Failed to start scenario. Please try again.')
      setLoading(false)
    }
  }

  const startStockChallenge = async () => {
    setLoading(true)
    try {
      
      navigate('/scenario/stock-challenge')
    } catch (error) {
      console.error('Error starting stock challenge:', error)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#fffaf5] via-[#f8fbff] to-[#f4f7fb] text-text-main">
      {}
      <header className="bg-white border-b border-[#f1d8c2] px-6 py-12 lg:px-10 mt-20 rounded-b-[28px] shadow-card">
        <div className="max-w-container mx-auto">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-[#ff6b35] text-white hover:bg-[#f97316] border border-[#ff6b35] px-5 py-2.5 rounded-[12px] text-sm font-semibold shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Go to Dashboard
            </button>
          </div>
          <div className="text-center">
            <h1 className="text-5xl font-bold text-text-main mb-4">Challenge Arena</h1>
            <p className="text-xl text-text-muted">
              Test your trading knowledge and compete with others
            </p>
          </div>
          
          {}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 max-w-4xl mx-auto">
            <div className="bg-white rounded-[12px] p-6 border border-[#f1d8c2] shadow-sm">
              <Eye className="w-8 h-8 mx-auto mb-3 text-brand-1" />
              <p className="text-4xl font-bold mb-2 text-text-main">{totalScore}</p>
              <p className="text-sm text-text-muted">Total Score</p>
            </div>
            <div className="bg-white rounded-[12px] p-6 border border-[#f1d8c2] shadow-sm">
              <Flame className="w-8 h-8 mx-auto mb-3 text-brand-1" />
              <p className="text-4xl font-bold mb-2 text-text-main">{currentStreak}</p>
              <p className="text-sm text-text-muted">Day Streak</p>
            </div>
            <div className="bg-white rounded-[12px] p-6 border border-[#f1d8c2] shadow-sm">
              <Trophy className="w-8 h-8 mx-auto mb-3 text-brand-1" />
              <p className="text-4xl font-bold mb-2 text-text-main">{winRate.toFixed(1)}%</p>
              <p className="text-sm text-text-muted">Win Rate</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-6 shadow-card hover:border-[#ff6b35] transition-colors">
            <p className="text-sm text-text-muted mb-2">Total Score</p>
            <p className="text-3xl font-bold text-brand-1">{totalScore}</p>
          </div>
          <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-6 shadow-card hover:border-[#ff6b35] transition-colors">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Stock Game Score
            </p>
            <p className="text-3xl font-bold text-text-main">{stockScore}</p>
          </div>
          <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-6 shadow-card hover:border-[#ff6b35] transition-colors">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <Target className="w-4 h-4" />
              Scenario Score
            </p>
            <p className="text-3xl font-bold text-brand-2">{scenarioScore}</p>
          </div>
          <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-6 shadow-card hover:border-[#ff6b35] transition-colors">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <Flame className="w-4 h-4 text-brand-1" />
              Current Streak
            </p>
            <p className="text-3xl font-bold text-brand-1">{currentStreak}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {}
          <div className="lg:col-span-2 space-y-6">
            {}
            <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-8 shadow-card text-text-main relative overflow-hidden group">
              <div className="absolute inset-0 bg-[#ff6b35]/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-4 mb-6 relative z-10">
                <div className="w-16 h-16 rounded-[12px] bg-[#ff6b35]/10 border border-[#ff6b35]/10 flex items-center justify-center">
                  <Target className="w-8 h-8 text-brand-1" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2 text-text-main">Financial Scenarios</h2>
                  <p className="text-text-muted text-sm">
                    Navigate real-world financial situations and make critical decisions. Each choice impacts your score and teaches valuable lessons.
                </p>
                </div>
              </div>
                <button
                  onClick={startFinancialScenarios}
                  disabled={loading}
                className="w-full px-6 py-3 bg-[#ff6b35] text-white border border-[#ff6b35] rounded-[12px] font-bold hover:shadow-lg hover:shadow-[#ff6b35]/30 hover:-translate-y-1 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative z-10"
                >
                {loading ? 'Starting...' : 'Start Financial Scenarios'}
                </button>
            </div>

            {}
            <div className="bg-white border border-[#f1d8c2] rounded-[12px] p-8 shadow-card text-text-main relative overflow-hidden group">
              <div className="absolute inset-0 bg-brand-2/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <div className="flex items-center gap-4 mb-6 relative z-10">
                <div className="w-16 h-16 rounded-[12px] bg-[#ff6b35]/10 border border-[#ff6b35]/10 flex items-center justify-center">
                  <BarChart3 className="w-8 h-8 text-brand-1" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold mb-2 text-text-main">Stock Prediction Game</h2>
                  <p className="text-text-muted text-sm">
                    Predict market movements and test your analysis skills. Compete for the top spot on the leaderboard!
                </p>
                </div>
              </div>
                <button
                  onClick={startStockChallenge}
                  disabled={loading}
                className="w-full px-6 py-3 bg-[#ff6b35] text-white border border-[#ff6b35] rounded-[12px] font-bold hover:shadow-lg hover:shadow-[#ff6b35]/30 hover:-translate-y-1 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed relative z-10"
                >
                {loading ? 'Starting...' : 'Start Game'}
                </button>
            </div>

            {}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-[12px] p-6 shadow-card border border-[#f1d8c2] hover:border-[#ff6b35] transition-colors">
                <Target className="w-8 h-8 mb-3 text-brand-1" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Real Market Scenarios</h3>
              </div>
              <div className="bg-white rounded-[12px] p-6 shadow-card border border-[#f1d8c2] hover:border-[#ff6b35] transition-colors">
                <Sparkles className="w-8 h-8 mb-3 text-brand-2" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Instant Feedback</h3>
              </div>
              <div className="bg-white rounded-[12px] p-6 shadow-card border border-[#f1d8c2] hover:border-[#ff6b35] transition-colors">
                <Trophy className="w-8 h-8 mb-3 text-brand-2" />
                <h3 className="text-lg font-bold mb-2 text-text-main">Earn XP & Rewards</h3>
              </div>
            </div>
          </div>

          {}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-[12px] shadow-card p-6 border border-[#f1d8c2] sticky top-28">
              <div className="flex items-center gap-3 mb-6">
                <Trophy className="w-8 h-8 text-brand-2" />
                <h3 className="text-xl font-bold text-text-main">Leaderboard</h3>
              </div>
              
              <div className="flex gap-2 mb-4 bg-[#f8fafc] p-1 rounded-[12px] border border-[#f1d8c2]">
                <button 
                  onClick={() => setLeaderboardTab('scores')}
                  className={`flex-1 py-1 text-sm rounded-[12px] border ${leaderboardTab==='scores' ? 'bg-[#ff6b35] text-white border-[#ff6b35] shadow-sm' : 'border-transparent text-text-muted hover:text-text-main hover:bg-white/70'}`}
                >Score</button>
                <button 
                  onClick={() => setLeaderboardTab('streaks')}
                  className={`flex-1 py-1 text-sm rounded-[12px] border ${leaderboardTab==='streaks' ? 'bg-[#ff6b35] text-white border-[#ff6b35] shadow-sm' : 'border-transparent text-text-muted hover:text-text-main hover:bg-white/70'}`}
                >Streak</button>
              </div>

              {}
              <div className="space-y-3">
                {leaderboard.length > 0 ? (
                  leaderboard.map((user, idx) => (
                    <div
                      key={user.username}
                      className="flex items-center gap-3 p-3 rounded-[12px] bg-[#f8fafc] border border-[#f1d8c2] hover:border-[#ff6b35]/30 transition-colors"
                    >
                      {idx === 0 && <Trophy className="w-6 h-6 text-brand-2 flex-shrink-0" />}
                      {idx === 1 && <Trophy className="w-6 h-6 text-brand-1 flex-shrink-0" />}
                      {idx === 2 && <Trophy className="w-6 h-6 text-text-main flex-shrink-0" />}
                      {idx > 2 && <div className="w-6 h-6 flex-shrink-0"></div>}
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border ${
                        idx === 0 ? 'bg-brand-2/15 border-brand-2/50' :
                        idx === 1 ? 'bg-brand-1/15 border-brand-1/50' :
                        idx === 2 ? 'bg-text-main/10 border-text-main/30' :
                        'bg-brand-1/10 border-brand-1/40'
                      }`}>
                        <span className="text-text-main font-bold text-sm">
                          {user.username.substring(0, 2).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-text-main truncate">
                          {user.username}
                        </p>
                        <p className="text-sm text-brand-1">
                          {leaderboardTab === 'scores' 
                            ? `${user.total_score} XP`
                            : `${user.current_streak} days`
                          }
                        </p>
                      </div>
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
