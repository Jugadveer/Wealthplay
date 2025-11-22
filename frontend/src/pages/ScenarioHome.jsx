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
} from 'lucide-react'

const ScenarioHome = () => {
  const navigate = useNavigate()
  const [quizHistory, setQuizHistory] = useState([])
  const [loading, setLoading] = useState(false)

  const startNewQuiz = async () => {
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
        // Navigate to quiz page using React Router
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


  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <header className="bg-gradient-to-r from-brand-1 to-brand-2 text-white shadow-lg px-6 py-8 lg:px-10">
        <div className="max-w-container mx-auto">
          <button
            onClick={() => navigate('/dashboard')}
            className="mb-4 bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-4xl font-bold mb-2">Financial Scenarios</h1>
          <p className="text-lg text-white/90">
            Practice decision-making with realistic financial scenarios
          </p>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Hero Card */}
        <div className="bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-8 shadow-card mb-12 text-center">
          <BarChart3 className="w-16 h-16 mx-auto mb-4 text-brand-1" />
          <h2 className="text-3xl font-bold text-text-main mb-4">
            Test Your Financial Decision-Making
          </h2>
          <p className="text-lg text-text-muted mb-8 max-w-2xl mx-auto">
            Experience real-world financial scenarios and learn from your choices. Each scenario
            tests your knowledge and helps build confidence in making financial decisions.
          </p>
          <button
            onClick={startNewQuiz}
            disabled={loading}
            className="inline-flex items-center gap-3 px-8 py-4 rounded-full bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold text-lg hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                Starting...
              </>
            ) : (
              <>
                <Play className="w-6 h-6" />
                Start New Quiz
              </>
            )}
          </button>
        </div>

        {/* How It Works */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360">
            <Target className="w-12 h-12 text-brand-1 mb-4" />
            <h3 className="text-lg font-bold text-text-main mb-2">Real Scenarios</h3>
            <p className="text-text-muted text-sm">
              Face realistic financial situations and make decisions
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360">
            <TrendingUp className="w-12 h-12 text-accent-green mb-4" />
            <h3 className="text-lg font-bold text-text-main mb-2">Instant Feedback</h3>
            <p className="text-text-muted text-sm">
              Learn immediately from your choices with detailed explanations
            </p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card hover:shadow-card-hover hover:-translate-y-2 transition-all duration-360">
            <Award className="w-12 h-12 text-brand-2 mb-4" />
            <h3 className="text-lg font-bold text-text-main mb-2">Earn XP</h3>
            <p className="text-text-muted text-sm">
              Gain experience points for correct answers and improve your level
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

export default ScenarioHome

