import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { axios } from '../utils/api'
import { ArrowRight, Trophy, Target, RotateCcw, Home } from 'lucide-react'

const ScenarioResult = () => {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadResult()
  }, [runId])

  const loadResult = async () => {
    try {
      const response = await axios.get(`/scenario/quiz/${runId}/result/`, {
        headers: { Accept: 'application/json' },
      })
      
      // Handle both JSON and HTML responses
      if (response.data.total_score !== undefined) {
        setResult(response.data)
      } else {
        // Extract from HTML or use defaults
        setResult({
          total_score: 0,
          total_possible_score: 100,
          percentage: 0,
          badge: 'Financial Novice',
        })
      }
    } catch (error) {
      console.error('Error loading result:', error)
      // Fallback values
      setResult({
        total_score: 0,
        total_possible_score: 100,
        percentage: 0,
        badge: 'Financial Novice',
      })
    } finally {
      setLoading(false)
    }
  }

  const getBadge = (score, total) => {
    const percentage = (score / total) * 100
    if (percentage >= 80) {
      return { name: 'Financial Expert', icon: Trophy, color: 'from-yellow-400 to-yellow-600' }
    } else if (percentage >= 60) {
      return { name: 'Financial Savvy', icon: Target, color: 'from-blue-400 to-blue-600' }
    } else if (percentage >= 40) {
      return { name: 'Financial Learner', icon: Target, color: 'from-green-400 to-green-600' }
    } else {
      return { name: 'Financial Novice', icon: Target, color: 'from-gray-400 to-gray-600' }
    }
  }

  if (loading || !result) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  const score = result.total_score || 0
  const total = result.total_possible_score || 100
  const percentage = total > 0 ? ((score / total) * 100).toFixed(0) : 0
  const badge = getBadge(score, total)
  const BadgeIcon = badge.icon

  return (
    <div className="min-h-screen bg-muted-1 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-3xl shadow-modal p-12 text-center">
        <div className="mb-8">
          <div className="text-sm font-semibold text-text-muted uppercase tracking-wide mb-4">
            FINAL SCORE
          </div>
          <div className="text-7xl font-bold text-brand-1 mb-6">{score}</div>
          <div className={`inline-flex items-center gap-2 px-6 py-3 rounded-full bg-gradient-to-r ${badge.color} text-white mb-6`}>
            <BadgeIcon className="w-5 h-5" />
            <span className="font-bold">{badge.name.toUpperCase()}</span>
          </div>
        </div>

        <p className="text-lg text-text-muted mb-8 leading-relaxed">
          You have completed this financial simulation run. Review your choices or start a new
          session to improve your score.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate('/scenario')}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180 flex items-center justify-center gap-2"
          >
            <RotateCcw className="w-5 h-5" />
            Start New Quiz
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-8 py-4 rounded-xl bg-white border-2 border-muted-3 text-text-main font-semibold hover:border-brand-1 hover:text-brand-1 transition-all duration-180 flex items-center justify-center gap-2"
          >
            <Home className="w-5 h-5" />
            Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

export default ScenarioResult

