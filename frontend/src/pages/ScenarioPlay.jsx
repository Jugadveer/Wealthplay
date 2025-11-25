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
  const [currentBalance, setCurrentBalance] = useState(0)
  const [isCorrect, setIsCorrect] = useState(false)

  useEffect(() => {
    loadQuiz(true) // Only show loading on initial load
  }, [runId])

  const loadQuiz = async (showLoading = true) => {
    if (showLoading) {
      setLoading(true)
    }
    try {
      const response = await axios.get(`/api/scenario/api/quiz/${runId}/`, {
        headers: { Accept: 'application/json' },
        withCredentials: true,
      })
      
      if (response.data.completed) {
        // Quiz is completed, redirect to result
        if (response.data.redirect) {
          navigate(response.data.redirect.replace('/scenario', ''))
        } else {
          navigate(`/scenario/quiz/${runId}/result`)
        }
        return
      }
      
      // Set quiz data from API response
      if (response.data.scenario) {
        const startingBalance = parseFloat(response.data.scenario.starting_balance) || 0
        setQuiz({
          scenarios: [{
            id: response.data.scenario.id,
            title: response.data.scenario.title,
            description: response.data.scenario.description,
            starting_balance: startingBalance,
            options: response.data.choices || [],
          }],
          current_question_index: (response.data.question_number || 1) - 1,
          total_questions: response.data.total_questions || 1,
          total_score: response.data.total_score || 0,
        })
        setCurrentQuestion((response.data.question_number || 1) - 1)
        setCurrentBalance(startingBalance)
        // Reset selection state for new question
        setSelectedOption(null)
        setShowResult(false)
        setIsCorrect(false)
      } else {
        console.error('No scenario data in API response:', response.data)
        // If no scenario but not completed, try to reload
        if (!response.data.completed) {
          console.warn('Quiz not completed but no scenario data, reloading...')
          setTimeout(() => loadQuiz(showLoading), 1000)
        }
      }
    } catch (error) {
      console.error('Error loading quiz:', error)
      console.error('Error details:', error.response?.data || error.message)
      // Fallback: create empty structure
      setQuiz({ scenarios: [], current_question_index: 0 })
      // Don't leave it in loading state if there's an error
      setLoading(false)
    } finally {
      setLoading(false)
    }
  }

  const handleOptionSelect = (option) => {
    setSelectedOption(option)
    setShowResult(true)
    
    // Calculate new balance based on option
    if (option.impact?.balance !== undefined) {
      const balanceImpact = parseFloat(option.impact.balance) || 0
      setCurrentBalance(prev => Math.max(0, prev + balanceImpact))
    }
    
    if (!exploreMode) {
      submitAnswer(option)
    }
  }

  const submitAnswer = async (option) => {
    try {
      const { getCsrfToken } = await import('../utils/api')
      const csrfToken = await getCsrfToken()
      const score = option.score || 0
      const option_id = option.id
      
      const response = await axios.post('/api/scenario/api/submit-answer/', {
        run_id: parseInt(runId),
        score: score,
        option_id: option_id,
      }, {
        headers: {
          'X-CSRFToken': csrfToken || '',
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      })

      if (response.data && response.data.success) {
        // Score submitted successfully, update total score
        const isAnswerCorrect = response.data.is_correct || false
        setIsCorrect(isAnswerCorrect)
        
        if (quiz) {
          setQuiz({
            ...quiz,
            total_score: response.data.total_score || quiz.total_score,
          })
        }
        
        // Don't auto-advance - let user click "Next Question" button
        // The backend has already advanced the question index
      } else {
        console.error('Failed to submit answer:', response.data)
      }
    } catch (error) {
      console.error('Error submitting answer:', error)
    }
  }

  const nextQuestion = async () => {
    // Ensure loading is false before starting
    setLoading(false)
    
    try {
      const { getCsrfToken } = await import('../utils/api')
      const csrfToken = await getCsrfToken()
      
      // Advance the question index on backend
      const nextResponse = await axios.post(`/api/scenario/api/quiz/${runId}/next/`, {}, {
        headers: {
          'X-CSRFToken': csrfToken || '',
        },
        withCredentials: true,
      })
      
      if (nextResponse.data && nextResponse.data.completed) {
        // Quiz completed, navigate to result
        navigate(`/scenario/quiz/${runId}/result`)
        return
      }
      
      // Fetch next question data without showing loading
      const questionResponse = await axios.get(`/api/scenario/api/quiz/${runId}/`, {
        headers: { Accept: 'application/json' },
        withCredentials: true,
      })
      
      if (questionResponse.data.completed) {
        navigate(`/scenario/quiz/${runId}/result`)
        return
      }
      
      // Update state directly without loading indicator
      if (questionResponse.data.scenario) {
        const startingBalance = parseFloat(questionResponse.data.scenario.starting_balance) || 0
        setQuiz({
          scenarios: [{
            id: questionResponse.data.scenario.id,
            title: questionResponse.data.scenario.title,
            description: questionResponse.data.scenario.description,
            starting_balance: startingBalance,
            options: questionResponse.data.choices || [],
          }],
          current_question_index: (questionResponse.data.question_number || 1) - 1,
          total_questions: questionResponse.data.total_questions || 1,
          total_score: questionResponse.data.total_score || 0,
        })
        setCurrentQuestion((questionResponse.data.question_number || 1) - 1)
        setCurrentBalance(startingBalance)
        // Reset selection state for new question
        setSelectedOption(null)
        setShowResult(false)
        setIsCorrect(false)
        // Explicitly ensure loading is false
        setLoading(false)
      }
    } catch (error) {
      console.error('Error moving to next question:', error)
      // On error, try to reload but still don't show loading
      setSelectedOption(null)
      setShowResult(false)
      setIsCorrect(false)
      setLoading(false) // Ensure loading is false
      // Try to reload without showing loading
      loadQuiz(false) // Don't show loading indicator
    }
  }

  // Only show loading on initial load, not when transitioning between questions
  if (loading && !quiz) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  const scenario = quiz?.scenarios?.[currentQuestion] || quiz?.scenario
  const totalQuestions = quiz?.total_questions || quiz?.scenarios?.length || quiz?.game_config?.total_questions || 5
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
              <div className="text-3xl font-bold">
                ₹{currentBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
              {selectedOption && selectedOption.impact?.balance !== undefined && (
                <div className={`text-sm mt-2 ${selectedOption.impact.balance < 0 ? 'text-red-200' : 'text-green-200'}`}>
                  {selectedOption.impact.balance > 0 ? '+' : ''}
                  ₹{Math.abs(selectedOption.impact.balance).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </div>
              )}
            </div>

            {/* Total Score */}
            <div className="bg-white rounded-xl p-6 shadow-card">
              <div className="text-sm text-text-muted mb-2">TOTAL SCORE</div>
              <div className="text-3xl font-bold text-brand-1">{quiz?.total_score || 0}</div>
              {selectedOption && showResult && (
                <div className={`text-sm mt-2 ${isCorrect ? 'text-accent-green' : 'text-gray-400'}`}>
                  {isCorrect ? `+${selectedOption.score || 0} points earned` : 'No points (incorrect answer)'}
                </div>
              )}
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
                                    {showResult && isSelected && (
                              <div className="mt-2 space-y-1">
                                <p className="text-sm text-text-muted">
                                  <span className="font-semibold">Score: </span>
                                  {option.score || 0}/20
                                </p>
                                <p className="text-sm text-text-muted">
                                  {option.content?.why_matters || option.content?.mentor || option.explanation}
                                </p>
                              </div>
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
            {selectedOption && selectedOption.impact && (
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white rounded-xl p-6 shadow-card text-center">
                  <div className="text-xs text-text-muted mb-2">1 YR VALUE</div>
                  <div className="text-2xl font-bold text-text-main">
                    ₹{Math.round(currentBalance * (1 + (selectedOption.impact.growth_rate || 0))).toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="bg-white rounded-xl p-6 shadow-card text-center">
                  <div className="text-xs text-text-muted mb-2">STABILITY</div>
                  <div className={`text-2xl font-bold ${
                    (selectedOption.impact.risk || 0) < 30 ? 'text-accent-green' : 
                    (selectedOption.impact.risk || 0) < 60 ? 'text-yellow-500' : 'text-red-500'
                  }`}>
                    {(selectedOption.impact.risk || 0) < 30 ? 'High' : (selectedOption.impact.risk || 0) < 60 ? 'Medium' : 'Low'}
                  </div>
                </div>
              </div>
            )}

            {/* Decision History */}
            <div className="bg-white rounded-xl p-6 shadow-card">
              <h3 className="font-bold text-text-main mb-4">DECISION HISTORY</h3>
              <ul className="space-y-2 text-sm text-text-muted mb-4">
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

            {/* Result Card - WHY THIS MATTERS */}
            {showResult && selectedOption && (
              <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6 border-2 border-orange-200 shadow-card animate-[modalEnter_360ms_ease-out_forwards]">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-5 h-5 text-orange-600" />
                  <h3 className="font-bold text-text-main">WHY THIS MATTERS</h3>
                </div>
                <p className="text-text-muted leading-relaxed mb-4">
                  {selectedOption?.content?.why_matters || selectedOption?.content?.mentor || selectedOption?.explanation || 'Learn from your decision and understand the financial implications.'}
                </p>
                <div className={`text-sm font-semibold mb-4 ${
                  isCorrect ? 'text-green-600' : 'text-gray-500'
                }`}>
                  You earned +{isCorrect ? (selectedOption?.score || 0) : 0} Points
                  {!isCorrect && (
                    <span className="block text-xs text-gray-400 mt-1">No points for incorrect answer</span>
                  )}
                </div>
                {selectedOption?.impact && (
                  <div className="mt-4 grid grid-cols-2 gap-3 text-sm mb-4">
                    <div>
                      <span className="text-text-muted">1 YR Value:</span>
                      <span className="font-semibold text-text-main ml-2">
                        ₹{Math.round(currentBalance * (1 + (selectedOption.impact.growth_rate || 0))).toLocaleString('en-IN')}
                      </span>
                    </div>
                    <div>
                      <span className="text-text-muted">Risk Score:</span>
                      <span className={`font-semibold ml-2 ${
                        (selectedOption.impact.risk || 0) < 30 ? 'text-accent-green' : 
                        (selectedOption.impact.risk || 0) < 60 ? 'text-yellow-500' : 'text-red-500'
                      }`}>
                        {(selectedOption.impact.risk || 0) < 30 ? 'Low' : (selectedOption.impact.risk || 0) < 60 ? 'Medium' : 'High'}
                      </span>
                    </div>
                  </div>
                )}
                {selectedOption?.content?.mentor && (
                  <div className="mt-4 p-3 bg-orange-50 rounded-lg border-l-4 border-orange-500">
                    <p className="text-sm font-semibold text-orange-700 mb-1">Mentor Feedback:</p>
                    <p className="text-sm text-text-muted">{selectedOption.content.mentor}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ScenarioPlay

