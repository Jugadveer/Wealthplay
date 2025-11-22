import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { axios } from '../utils/api'
import {
  ArrowRight,
  TrendingUp,
  Shield,
  Zap,
  CheckCircle2,
  Eye,
  Home,
} from 'lucide-react'

const ScenarioPlay = () => {
  const { runId } = useParams()
  const navigate = useNavigate()
  const [quiz, setQuiz] = useState(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [selectedOption, setSelectedOption] = useState(null)
  const [showResult, setShowResult] = useState(false)
  const [exploreMode, setExploreMode] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadQuiz()
  }, [runId])

  const loadQuiz = async () => {
    try {
      // Load quiz data from Django view (which renders template, we need API endpoint)
      // For now, let's try the direct API approach
      const response = await axios.get(`/scenario/quiz/${runId}/`, {
        headers: { Accept: 'application/json' },
      })
      
      // If response is HTML, we need a JSON endpoint
      // For now, let's create a structure from the scenario
      if (response.data.game_config) {
        setQuiz({
          scenarios: [{ ...response.data.scenario, options: response.data.game_config.choices }],
          current_question_index: response.data.game_config.question_number - 1,
        })
        setCurrentQuestion(response.data.game_config.question_number - 1)
      } else {
        setQuiz(response.data)
        setCurrentQuestion(response.data.current_question_index || 0)
      }
    } catch (error) {
      console.error('Error loading quiz:', error)
      // Fallback: create empty structure
      setQuiz({ scenarios: [], current_question_index: 0 })
    } finally {
      setLoading(false)
    }
  }

  const handleOptionSelect = (option) => {
    setSelectedOption(option)
    setShowResult(true)
    
    if (!exploreMode) {
      submitAnswer(option)
    }
  }

  const submitAnswer = async (option) => {
    try {
      const score = option.score || 0
      const response = await axios.post('/scenario/api/submit-answer/', {
        run_id: parseInt(runId),
        score: score,
      }, {
        headers: {
          'X-CSRFToken': getCsrfToken(),
          'Content-Type': 'application/json',
        },
      })

      if (response.data.status === 'success') {
        // Score submitted successfully
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
    }
  }

  const getCsrfToken = () => {
    const cookies = document.cookie.split(';')
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=')
      if (name === 'csrftoken') {
        return value
      }
    }
    return ''
  }

  const nextQuestion = async () => {
    if (currentQuestion < (quiz?.scenarios?.length || 5) - 1) {
      // Navigate to next question via Django route
      try {
        await axios.post(`/scenario/quiz/${runId}/next/`, {}, {
          headers: {
            'X-CSRFToken': getCsrfToken(),
          },
        })
        // Reload the page to get next question
        window.location.href = `/scenario/quiz/${runId}/`
      } catch (error) {
        console.error('Error moving to next question:', error)
        // Fallback: just navigate
        navigate(`/scenario/quiz/${runId}/`)
      }
    } else {
      navigate(`/scenario/quiz/${runId}/result`)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  const scenario = quiz?.scenarios?.[currentQuestion] || quiz?.scenario
  const totalQuestions = quiz?.scenarios?.length || quiz?.game_config?.total_questions || 5
  const questionNumber = currentQuestion + 1
  const progress = (questionNumber / totalQuestions) * 100

  // If no scenario, show loading state
  if (!scenario) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1 mx-auto mb-4"></div>
          <p className="text-text-muted">Loading scenario...</p>
        </div>
      </div>
    )
  }

  // Get options from scenario
  const options = scenario.options || quiz?.game_config?.choices || []

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <div className="bg-white border-b border-muted-2 shadow-sm sticky top-0 z-40">
        <div className="max-w-container mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/scenario')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-text-main hover:bg-muted-1 transition-colors"
          >
            <ArrowRight className="w-4 h-4 rotate-180" />
            Back
          </button>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-sm text-text-muted mb-1">Question</div>
              <div className="text-lg font-bold text-text-main">
                {currentQuestion + 1} of {totalQuestions}
              </div>
            </div>
            <div className="w-32 h-2 bg-muted-2 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-brand-1 to-brand-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-container mx-auto px-6 py-10 lg:px-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Sidebar - Balance & Risk */}
          <div className="lg:col-span-1 space-y-6">
            {/* Current Balance */}
            <div className="bg-gradient-to-br from-brand-1 to-brand-2 rounded-xl p-6 text-white shadow-lg">
              <div className="text-sm opacity-90 mb-2">CURRENT BALANCE</div>
              <div className="text-3xl font-bold">₹30,000</div>
            </div>

            {/* Risk Analysis */}
            <div className="bg-white rounded-xl p-6 shadow-card">
              <h3 className="text-lg font-bold text-text-main mb-4">Risk Analysis</h3>
              <div className="relative w-full h-32">
                {/* Semi-circle gauge */}
                <svg viewBox="0 0 200 100" className="w-full h-full">
                  <path
                    d="M 20 80 A 80 80 0 0 1 180 80"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="8"
                  />
                  <defs>
                    <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#10b981" />
                      <stop offset="50%" stopColor="#f59e0b" />
                      <stop offset="100%" stopColor="#ef4444" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M 20 80 A 80 80 0 0 1 180 80"
                    fill="none"
                    stroke="url(#riskGradient)"
                    strokeWidth="8"
                    strokeDasharray={`${progress * 2.51} 251`}
                  />
                  {/* Needle */}
                  <line
                    x1="100"
                    y1="80"
                    x2={100 + 60 * Math.cos(Math.PI - (progress / 100) * Math.PI)}
                    y2={80 - 60 * Math.sin(Math.PI - (progress / 100) * Math.PI)}
                    stroke="#1f2937"
                    strokeWidth="3"
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-text-muted px-2">
                  <span>Safe</span>
                  <span>Risky</span>
                </div>
              </div>
            </div>
          </div>

          {/* Center - Question & Options */}
          <div className="lg:col-span-1">
            {scenario && (
              <div className="bg-white rounded-xl p-8 shadow-card">
                <h2 className="text-3xl font-bold text-text-main mb-4">
                  {scenario.title || scenario.name || 'Financial Scenario'}
                </h2>
                <p className="text-lg text-text-muted leading-relaxed mb-8">
                  {scenario.description || scenario.scenario_text || 'Make a financial decision based on the situation.'}
                </p>

                {/* Options */}
                <div className="space-y-4 mb-6">
                  {options.map((option, idx) => {
                    const isSelected = selectedOption?.id === option.id
                    // Map option types to icons
                    const iconMap = {
                      invest: TrendingUp,
                      save: Shield,
                      spend: Zap,
                      conservative: Shield,
                      moderate: TrendingUp,
                      aggressive: Zap,
                    }
                    const Icon = iconMap[option.type?.toLowerCase()] || iconMap[option.decision_type?.toLowerCase()] || TrendingUp

                    return (
                      <button
                        key={option.id}
                        onClick={() => handleOptionSelect(option)}
                        disabled={showResult && !exploreMode}
                        className={`w-full p-6 rounded-xl border-2 text-left transition-all duration-180 ${
                          isSelected
                            ? 'border-brand-1 bg-brand-1/10 scale-105'
                            : 'border-muted-3 bg-white hover:border-brand-1/50 hover:shadow-md'
                        } ${showResult && !exploreMode ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Icon className="w-5 h-5 text-brand-1" />
                              <span className="font-semibold text-text-main">{option.text}</span>
                            </div>
                            {showResult && (
                              <p className="text-sm text-text-muted mt-2">
                                {option.content?.why_matters || option.content?.mentor || option.explanation}
                              </p>
                            )}
                          </div>
                          {isSelected && showResult && (
                            <CheckCircle2 className="w-6 h-6 text-brand-1 flex-shrink-0" />
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>

                {/* Explore Mode Toggle */}
                <button
                  onClick={() => setExploreMode(!exploreMode)}
                  className="flex items-center gap-2 text-sm text-text-muted hover:text-brand-1 transition-colors mb-6"
                >
                  <Eye className="w-4 h-4" />
                  Explore Mode: Click other options to see "What If"
                </button>

                {/* Result Card */}
                {showResult && (
                  <div className="bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-6 border-2 border-brand-1/20 mb-6 animate-[modalEnter_360ms_ease-out_forwards]">
                    <div className="flex items-center gap-2 mb-4">
                      <Zap className="w-5 h-5 text-brand-1" />
                      <h3 className="font-bold text-text-main">WHY THIS MATTERS</h3>
                    </div>
                    <p className="text-text-muted leading-relaxed mb-4">
                      {selectedOption?.content?.why_matters || selectedOption?.content?.mentor || selectedOption?.explanation || 'Learn from your decision and understand the financial implications.'}
                    </p>
                    <div className="text-sm text-text-muted">
                      You earned +{selectedOption?.score || 0} Points
                    </div>
                    {selectedOption?.impact && (
                      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-text-muted">1 YR Value:</span>
                          <span className="font-semibold text-text-main ml-2">
                            ₹{Math.round(30000 * (1 + (selectedOption.impact.growth_rate || 0) / 100)).toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="text-text-muted">Stability:</span>
                          <span className="font-semibold text-accent-green ml-2">
                            {selectedOption.impact.risk < 30 ? 'High' : selectedOption.impact.risk < 60 ? 'Medium' : 'Low'}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Next Button */}
                {showResult && (
                  <button
                    onClick={nextQuestion}
                    className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180 flex items-center justify-center gap-2"
                  >
                    {currentQuestion < totalQuestions - 1 ? (
                      <>
                        Next Question
                        <ArrowRight className="w-5 h-5" />
                      </>
                    ) : (
                      <>
                        View Results
                        <ArrowRight className="w-5 h-5" />
                      </>
                    )}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Right Sidebar - Results & Context */}
          <div className="lg:col-span-1 space-y-6">
            {/* Value Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-xl p-6 shadow-card text-center">
                <div className="text-xs text-text-muted mb-2">1 YR VALUE</div>
                <div className="text-2xl font-bold text-text-main">₹33,600</div>
              </div>
              <div className="bg-white rounded-xl p-6 shadow-card text-center">
                <div className="text-xs text-text-muted mb-2">STABILITY</div>
                <div className="text-2xl font-bold text-accent-green">High</div>
              </div>
            </div>

            {/* Decision History */}
            <div className="bg-white rounded-xl p-6 shadow-card">
              <h3 className="font-bold text-text-main mb-4">DECISION HISTORY</h3>
              <ul className="space-y-2 text-sm text-text-muted">
                {selectedOption ? (
                  <li className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-1 mt-0.5 flex-shrink-0" />
                    <span>You chose: {selectedOption.text}</span>
                  </li>
                ) : (
                  <li className="text-text-light">No decisions made yet</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScenarioPlay

