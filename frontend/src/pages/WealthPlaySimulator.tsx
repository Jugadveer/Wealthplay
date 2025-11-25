import React, { useState, useEffect, createContext, useContext, useCallback } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  TrendingUp,
  Shield,
  Zap,
  Trophy,
  Target,
  ArrowRight,
  Home,
  Eye,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import axios from 'axios'

// ==================== TYPES ====================
type DecisionType = 'INVEST' | 'SAVE' | 'SPEND'
type BadgeColor = 'gray' | 'bronze' | 'silver' | 'gold'
type Screen = 'START' | 'PLAY' | 'RESULT'

interface DecisionOption {
  id: number
  text: string
  type: DecisionType
  score: number
  impact: {
    balance: number
    confidence: number
    risk: number
    growth_rate: number
  }
  content: {
    why_matters: string
    mentor: string
  }
}

interface Scenario {
  id: number
  title: string
  description: string
  starting_balance: number
  options: DecisionOption[]
}

interface ChoiceLog {
  text: string
  score: number
  decisionType: DecisionType
  why_matters: string
}

interface QuizRun {
  runId: string
  scenarioIds: number[]
  currentQuestionIndex: number
  totalScore: number
  isCompleted: boolean
  history: ChoiceLog[]
}

interface LocalState {
  baseBalance: number // Store the original starting balance
  currentBalance: number
  currentRisk: number
  hasAnswered: boolean
  selectedOption: DecisionOption | null
  submittedOption: DecisionOption | null // The option that was actually submitted for scoring
  hypotheticalScore: number
  projectedValue: number
}

// ==================== CONTEXT ====================
interface QuizContextType {
  screen: Screen
  quizRun: QuizRun | null
  currentScenario: Scenario | null
  localState: LocalState
  loadQuiz: (runId?: string) => Promise<void>
  startQuiz: () => Promise<void>
  handleChoice: (option: DecisionOption) => void
  submitChoice: (option: DecisionOption) => Promise<void>
  nextQuestion: () => Promise<void>
  resetGame: () => void
}

const QuizContext = createContext<QuizContextType | null>(null)

const useQuiz = () => {
  const context = useContext(QuizContext)
  if (!context) throw new Error('useQuiz must be used within QuizProvider')
  return context
}

// ==================== UTILITY HOOKS ====================
const useAnimateNumber = (targetValue: number, duration: number = 500) => {
  const [displayValue, setDisplayValue] = useState(targetValue)
  const prevTargetRef = React.useRef(targetValue)
  const animationFrameRef = React.useRef<number | null>(null)
  const startValueRef = React.useRef(targetValue)

  useEffect(() => {
    // Only animate if targetValue actually changed
    if (prevTargetRef.current === targetValue) {
      return
    }
    
    // Cancel any ongoing animation
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    
    // Capture current display value as start
    startValueRef.current = displayValue
    const startValue = displayValue
    const difference = targetValue - startValue
    const startTime = Date.now()
    
    prevTargetRef.current = targetValue

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const easeOutQuad = 1 - (1 - progress) * (1 - progress)
      const newValue = startValue + difference * easeOutQuad
      setDisplayValue(newValue)

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate)
      } else {
        setDisplayValue(targetValue)
        animationFrameRef.current = null
      }
    }

    if (Math.abs(difference) > 0.01) {
      animationFrameRef.current = requestAnimationFrame(animate)
    } else {
      setDisplayValue(targetValue)
    }
    
    // Cleanup function
    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetValue, duration]) // Only depend on targetValue and duration - displayValue intentionally excluded

  return displayValue
}

// ==================== PROVIDER ====================
const QuizProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [screen, setScreen] = useState<Screen>('START')
  const [quizRun, setQuizRun] = useState<QuizRun | null>(null)
  const [currentScenario, setCurrentScenario] = useState<Scenario | null>(null)
  const [localState, setLocalState] = useState<LocalState>({
    baseBalance: 0,
    currentBalance: 0,
    currentRisk: 0,
    hasAnswered: false,
    selectedOption: null,
    submittedOption: null,
    hypotheticalScore: 0,
    projectedValue: 0,
  })

  const loadCurrentScenario = useCallback(async (run: QuizRun) => {
    if (run.currentQuestionIndex < run.scenarioIds.length) {
      const scenarioId = run.scenarioIds[run.currentQuestionIndex]
      try {
        const response = await axios.get(`/api/scenario/api/scenario/${scenarioId}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
        if (response.data) {
          // Transform API response to match our Scenario interface
          const options: DecisionOption[] = (response.data.choices || []).map((choice: any) => ({
            id: typeof choice.id === 'string' ? parseInt(choice.id) : choice.id, // Ensure ID is integer
            text: choice.text,
            type: choice.type as DecisionType,
            score: choice.score,
            impact: {
              balance: choice.impact?.balance || 0,
              confidence: choice.impact?.confidence || 0,
              risk: choice.impact?.risk || 0,
              growth_rate: choice.impact?.growth_rate || 0,
            },
            content: {
              why_matters: choice.content?.why_matters || choice.why_matters || '',
              mentor: choice.content?.mentor || choice.mentor || '',
            },
          }))

          const scenario: Scenario = {
            id: response.data.id,
            title: response.data.title,
            description: response.data.description,
            starting_balance: parseFloat(response.data.starting_balance) || 0,
            options: options,
          }
          setCurrentScenario(scenario)
          const baseBalance = scenario.starting_balance
          setLocalState({
            baseBalance: baseBalance,
            currentBalance: baseBalance,
            currentRisk: 50, // Start at middle (neutral risk)
            hasAnswered: false,
            selectedOption: null,
            submittedOption: null,
            hypotheticalScore: 0,
            projectedValue: baseBalance,
          })
        }
      } catch (error) {
        console.error('Error loading scenario:', error)
      }
    }
  }, [])

  const loadQuiz = useCallback(async (runIdFromUrl?: string) => {
    // If runId is provided from URL, load from backend
    if (runIdFromUrl) {
      try {
        const response = await axios.get(`/api/scenario/api/quiz/${runIdFromUrl}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
        
        if (response.data.completed) {
          setScreen('RESULT')
          return
        }

        // Create QuizRun from backend data
        const scenarioIds = response.data.scenario_ids?.split(',').map((id: string) => parseInt(id)) || []
        const run: QuizRun = {
          runId: runIdFromUrl,
          scenarioIds: scenarioIds,
          currentQuestionIndex: (response.data.question_number || 1) - 1,
          totalScore: response.data.total_score || 0,
          isCompleted: false,
          history: [], // Will be populated from backend if needed
        }
        setQuizRun(run)
        localStorage.setItem('wealthplay_quiz_run', JSON.stringify(run))
        setScreen('PLAY')
        await loadCurrentScenario(run)
        return
      } catch (error) {
        console.error('Error loading quiz from backend:', error)
        // If QuizRun doesn't exist in DB, clear localStorage and go to start
        localStorage.removeItem('wealthplay_quiz_run')
        setScreen('START')
      }
    }

    // Otherwise, try localStorage - but verify it exists in DB
    const saved = localStorage.getItem('wealthplay_quiz_run')
    if (saved) {
      try {
        const run: QuizRun = JSON.parse(saved)
        const runId = parseInt(run.runId)
        
        // Verify the QuizRun exists in the database
        if (!isNaN(runId)) {
          try {
            const verifyResponse = await axios.get(`/api/scenario/api/quiz/${runId}/`, {
              headers: { Accept: 'application/json' },
              withCredentials: true,
            })
            
            // Update run with latest data from backend
            const scenarioIds = verifyResponse.data.scenario_ids?.split(',').map((id: string) => parseInt(id)) || []
            const updatedRun: QuizRun = {
              runId: runId.toString(),
              scenarioIds: scenarioIds,
              currentQuestionIndex: (verifyResponse.data.question_number || 1) - 1,
              totalScore: verifyResponse.data.total_score || 0,
              isCompleted: verifyResponse.data.completed || false,
              history: run.history, // Keep local history
            }
            
            setQuizRun(updatedRun)
            localStorage.setItem('wealthplay_quiz_run', JSON.stringify(updatedRun))
            
            if (updatedRun.isCompleted) {
              setScreen('RESULT')
            } else {
              setScreen('PLAY')
              loadCurrentScenario(updatedRun)
            }
          } catch (verifyError) {
            // QuizRun doesn't exist in DB, clear localStorage and start fresh
            console.error('QuizRun not found in database, starting fresh:', verifyError)
            localStorage.removeItem('wealthplay_quiz_run')
            setScreen('START')
          }
        } else {
          // Invalid runId, clear and start fresh
          localStorage.removeItem('wealthplay_quiz_run')
          setScreen('START')
        }
      } catch (error) {
        console.error('Error loading quiz from localStorage:', error)
        localStorage.removeItem('wealthplay_quiz_run')
        setScreen('START')
      }
    }
  }, [loadCurrentScenario])

  useEffect(() => {
    // Don't auto-load on mount if we're coming from a URL with runId
    // The main component will handle that
    const saved = localStorage.getItem('wealthplay_quiz_run')
    if (saved && !window.location.pathname.includes('/quiz/')) {
      loadQuiz()
    }
  }, [loadQuiz])

  const startQuiz = async () => {
    try {
      const { getCsrfToken } = await import('../utils/api')
      const csrfToken = await getCsrfToken()

      // Create quiz run in database via backend API
      const response = await axios.post('/api/scenario/api/start/', {}, {
        headers: {
          'X-CSRFToken': csrfToken || '',
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      })

      if (!response.data || !response.data.success || !response.data.runId) {
        alert('Failed to start quiz')
        return
      }

      const dbRunId = response.data.runId

      // Get scenario IDs from the backend
      const quizResponse = await axios.get(`/api/scenario/api/quiz/${dbRunId}/`, {
        headers: { Accept: 'application/json' },
        withCredentials: true,
      })

      const scenarioIds = quizResponse.data.scenario_ids?.split(',').map((id: string) => parseInt(id)) || []

      const newRun: QuizRun = {
        runId: dbRunId.toString(),
        scenarioIds: scenarioIds,
        currentQuestionIndex: 0,
        totalScore: 0,
        isCompleted: false,
        history: [],
      }

      setQuizRun(newRun)
      localStorage.setItem('wealthplay_quiz_run', JSON.stringify(newRun))

      // Load first scenario
      await loadCurrentScenario(newRun)
      setScreen('PLAY')
    } catch (error) {
      console.error('Error starting quiz:', error)
      alert('Failed to start quiz. Please try again.')
    }
  }

  const handleChoice = (option: DecisionOption) => {
    if (!currentScenario) return

    // Always calculate from base balance, not accumulated
    const newBalance = Math.max(0, localState.baseBalance + option.impact.balance)
    
    // Map risk_score_delta to 0-100 scale
    // risk_score_delta typically ranges from -10 to +10
    // Map: -10 -> 0, 0 -> 50, +10 -> 100
    const riskDelta = option.impact.risk // This is risk_score_delta from backend
    const newRisk = Math.max(0, Math.min(100, 50 + (riskDelta * 5)))
    
    const projectedValue = newBalance * (1 + option.impact.growth_rate)

    setLocalState({
      ...localState,
      currentBalance: newBalance,
      currentRisk: newRisk,
      selectedOption: option,
      hypotheticalScore: option.score,
      projectedValue,
    })
  }

  const submitChoice = async (option: DecisionOption) => {
    if (!quizRun || localState.hasAnswered) return

    try {
      const { getCsrfToken } = await import('../utils/api')
      const csrfToken = await getCsrfToken()

      // Ensure runId is a valid integer (database ID)
      const runId = parseInt(quizRun.runId)
      if (isNaN(runId)) {
        console.error('Invalid runId:', quizRun.runId)
        // Clear invalid localStorage and restart
        localStorage.removeItem('wealthplay_quiz_run')
        alert('Invalid quiz session. Please start a new quiz.')
        setScreen('START')
        setQuizRun(null)
        return
      }

      // Verify QuizRun exists in database before submitting
      try {
        await axios.get(`/api/scenario/api/quiz/${runId}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
      } catch (verifyError: any) {
        // QuizRun doesn't exist, clear localStorage and restart
        if (verifyError.response?.status === 404) {
          localStorage.removeItem('wealthplay_quiz_run')
          alert('Your quiz session expired. Please start a new quiz.')
          setScreen('START')
          setQuizRun(null)
          return
        }
        throw verifyError // Re-throw if it's a different error
      }

      // Submit to backend - ensure option_id is an integer
      const optionId = typeof option.id === 'string' ? parseInt(option.id) : option.id
      if (isNaN(optionId)) {
        console.error('Invalid option ID:', option.id)
        alert('Invalid option selected. Please refresh and try again.')
        return
      }

      // Submit to backend
      const response = await axios.post('/api/scenario/api/submit-answer/', {
        run_id: runId,
        option_id: optionId,
        score: option.score,
      }, {
        headers: {
          'X-CSRFToken': csrfToken || '',
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      })

      // Get updated score from backend response
      const responseData = response.data || {}
      const newTotalScore = responseData.total_score ?? (quizRun.totalScore + option.score)
      const scoreAdded = responseData.score_added ?? option.score
      
      // Use the current question index from backend to ensure sync
      const currentIndex = responseData.current_question_index ?? quizRun.currentQuestionIndex
      
      // Don't advance question index - stay on current question until user clicks "Next Question"
      // This allows user to explore other options
      
      // Update local state with backend data
      const updatedRun: QuizRun = {
        ...quizRun,
        totalScore: newTotalScore,
        currentQuestionIndex: currentIndex, // Use backend's current index to stay in sync
        history: [
          ...quizRun.history,
          {
            text: option.text,
            score: scoreAdded,
            decisionType: option.type,
            why_matters: option.content.why_matters,
          },
        ],
      }

      // Force state update to ensure UI reflects changes
      setQuizRun({ ...updatedRun }) // Create new object to trigger re-render
      localStorage.setItem('wealthplay_quiz_run', JSON.stringify(updatedRun))
      setLocalState({ 
        ...localState, 
        hasAnswered: true,
        submittedOption: option,
        // Keep the selected option visible
        selectedOption: option,
      })
    } catch (error: any) {
      console.error('Error submitting choice:', error)
      
      // Handle different error types
      if (error.response?.status === 404 || error.response?.data?.error?.includes('QuizRun not found')) {
        localStorage.removeItem('wealthplay_quiz_run')
        alert('Your quiz session expired. Please start a new quiz.')
        setScreen('START')
        setQuizRun(null)
        return
      }
      
      if (error.response?.status === 400) {
        const errorMsg = error.response?.data?.error || 'Invalid request. Please try again.'
        const debugInfo = error.response?.data?.debug
        console.error('Bad Request:', errorMsg, debugInfo)
        alert(`Error: ${errorMsg}. Please refresh and try again.`)
        return
      }
      
      // Generic error
      alert('Failed to submit answer. Please try again.')
    }
  }

  const nextQuestion = async () => {
    if (!quizRun) return

    const nextIndex = quizRun.currentQuestionIndex + 1
    if (nextIndex >= quizRun.scenarioIds.length) {
      // Quiz is complete - mark as completed in backend if needed
      try {
        const runId = parseInt(quizRun.runId)
        if (!isNaN(runId)) {
          const { getCsrfToken } = await import('../utils/api')
          const csrfToken = await getCsrfToken()
          
          // Try to mark as completed in backend (optional, backend might have already done this)
          try {
            await axios.post(`/api/scenario/api/quiz/${runId}/complete/`, {}, {
              headers: {
                'X-CSRFToken': csrfToken || '',
                'Content-Type': 'application/json',
              },
              withCredentials: true,
            })
          } catch (e) {
            // Ignore if endpoint doesn't exist or already completed
            console.log('Could not mark quiz as completed in backend:', e)
          }
        }
      } catch (error) {
        console.error('Error completing quiz:', error)
      }

      const completedRun: QuizRun = {
        ...quizRun,
        isCompleted: true,
      }
      setQuizRun(completedRun)
      localStorage.setItem('wealthplay_quiz_run', JSON.stringify(completedRun))
      setScreen('RESULT')
      return
    }

    // Advance to next question in backend
    try {
      const runId = parseInt(quizRun.runId)
      if (!isNaN(runId)) {
        const { getCsrfToken } = await import('../utils/api')
        const csrfToken = await getCsrfToken()
        
        await axios.post(`/api/scenario/api/quiz/${runId}/next/`, {}, {
          headers: {
            'X-CSRFToken': csrfToken || '',
            'Content-Type': 'application/json',
          },
          withCredentials: true,
        })
      }
    } catch (error) {
      console.error('Error advancing question:', error)
    }

    // Update local state and load next scenario
    const updatedRun: QuizRun = {
      ...quizRun,
      currentQuestionIndex: nextIndex,
    }

    setQuizRun(updatedRun)
    localStorage.setItem('wealthplay_quiz_run', JSON.stringify(updatedRun))

    // Load next scenario
    await loadCurrentScenario(updatedRun)
  }

  const resetGame = () => {
    localStorage.removeItem('wealthplay_quiz_run')
    setQuizRun(null)
    setCurrentScenario(null)
    setLocalState({
      baseBalance: 0,
      currentBalance: 0,
      currentRisk: 0,
      hasAnswered: false,
      selectedOption: null,
      submittedOption: null,
      hypotheticalScore: 0,
      projectedValue: 0,
    })
    setScreen('START')
  }

  return (
    <QuizContext.Provider
      value={{
        screen,
        quizRun,
        currentScenario,
        localState,
        loadQuiz,
        startQuiz,
        handleChoice,
        submitChoice,
        nextQuestion,
        resetGame,
      }}
    >
      {children}
    </QuizContext.Provider>
  )
}

// ==================== COMPONENTS ====================

const RiskGauge: React.FC<{ risk: number }> = ({ risk }) => {
  // Clamp risk between 0 and 100
  const clampedRisk = Math.max(0, Math.min(100, risk))
  // Convert 0-100 to -90 to 90 degrees (semicircle)
  const rotation = clampedRisk * 1.8 - 90

  return (
    <div className="relative w-full h-40 flex items-center justify-center">
      {/* Semicircle background */}
      <svg className="w-full h-full" viewBox="0 0 200 100" style={{ overflow: 'visible' }}>
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
          strokeWidth="14"
          strokeLinecap="round"
        />
        <text x="25" y="95" className="text-xs fill-gray-600 font-medium">Safe</text>
        <text x="165" y="95" className="text-xs fill-gray-600 font-medium">Risky</text>
      </svg>
      
      {/* Needle - positioned at center bottom */}
      <div
        className="absolute bottom-0 left-1/2 w-0.5 h-20 bg-gray-900 transition-transform duration-500 ease-out"
        style={{
          transform: `translateX(-50%) rotate(${rotation}deg)`,
          transformOrigin: 'bottom center',
        }}
      />
      
      {/* Center dot */}
      <div className="absolute bottom-0 left-1/2 w-3 h-3 bg-gray-900 rounded-full transform -translate-x-1/2 translate-y-1.5" />
    </div>
  )
}

const GrowthChart: React.FC<{ current: number; projected: number }> = ({ current, projected }) => {
  const data = [
    { name: 'Current', value: current },
    { name: 'Projected (1Y)', value: projected },
  ]

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
        <YAxis
          stroke="#6b7280"
          style={{ fontSize: '12px' }}
          tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip
          formatter={(value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
          contentStyle={{
            backgroundColor: '#fff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Bar dataKey="value" fill="#f97316" radius={[8, 8, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

const DecisionOptionButton: React.FC<{
  option: DecisionOption
  onClick: () => void
  isSelected: boolean
  isSubmitted: boolean
}> = ({ option, onClick, isSelected, isSubmitted }) => {
  const typeColors = {
    INVEST: 'bg-blue-500/10 border-blue-500 text-blue-700',
    SAVE: 'bg-green-500/10 border-green-500 text-green-700',
    SPEND: 'bg-orange-500/10 border-orange-500 text-orange-700',
  }

  const icons = {
    INVEST: TrendingUp,
    SAVE: Shield,
    SPEND: Zap,
  }

  const Icon = icons[option.type]

  return (
    <button
      onClick={onClick}
      className={`p-4 rounded-xl border-2 transition-all duration-200 text-left ${
        isSelected
          ? `${typeColors[option.type]} shadow-lg scale-105`
          : 'bg-white border-gray-200 hover:border-gray-300 hover:shadow-md'
      } ${isSubmitted && !isSelected ? 'opacity-60' : ''}`}
    >
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${typeColors[option.type].split(' ')[0]}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <p className="font-semibold">{option.text}</p>
        </div>
      </div>
    </button>
  )
}

const StartScreen: React.FC = () => {
  const { startQuiz } = useQuiz()

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-8 md:p-12 text-center">
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-orange-500 to-orange-600 rounded-full mb-6">
            <Trophy className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            WealthPlay
          </h1>
          <p className="text-xl text-gray-600 mb-2">
            Master Financial Decision-Making
          </p>
          <p className="text-gray-500">
            Test your financial wisdom through real-world scenarios
          </p>
        </div>

        <button
          onClick={startQuiz}
          className="w-full md:w-auto px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold text-lg rounded-xl shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 flex items-center justify-center gap-2 mx-auto"
        >
          Start Quiz
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}

const ScenarioPlay: React.FC = () => {
  const {
    quizRun,
    currentScenario,
    localState,
    handleChoice,
    submitChoice,
    nextQuestion,
  } = useQuiz()
  const navigate = useNavigate()

  const animatedBalance = useAnimateNumber(localState.currentBalance)
  const animatedProjected = useAnimateNumber(localState.projectedValue)

  if (!currentScenario || !quizRun) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    )
  }

  const questionNumber = quizRun.currentQuestionIndex + 1
  const totalQuestions = quizRun.scenarioIds.length
  const progress = (questionNumber / totalQuestions) * 100

  const handleOptionClick = async (option: DecisionOption) => {
    // Always update the display (handleChoice)
    handleChoice(option)
    
    // Only submit if this is the first answer
    if (!localState.hasAnswered) {
      await submitChoice(option)
    }
  }

  // Get the option to show "Why It Matters" for
  const optionToShow = localState.selectedOption

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <button
            onClick={() => navigate('/scenario')}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
          >
            <ArrowRight className="w-4 h-4 rotate-180" />
            Back
          </button>
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-sm text-gray-500 mb-1">Question</div>
              <div className="text-lg font-bold text-gray-900">
                {questionNumber} of {totalQuestions}
              </div>
            </div>
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-500 to-orange-600 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Sidebar - Status */}
          <div className="lg:col-span-1 space-y-6">
            {/* Current Balance */}
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg">
              <div className="text-sm opacity-90 mb-2">CURRENT BALANCE</div>
              <div className="text-3xl font-bold">
                ₹{animatedBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </div>
            </div>

            {/* Total Score */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="text-sm text-gray-500 mb-1">TOTAL SCORE</div>
              <div className="text-2xl font-bold text-orange-600">
                {quizRun.totalScore}
              </div>
            </div>

            {/* Risk Analysis */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="text-sm text-gray-500 mb-4">Risk Analysis</div>
              <RiskGauge risk={localState.currentRisk} />
            </div>
          </div>

          {/* Center - Scenario */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                {currentScenario.title}
              </h2>
              <p className="text-gray-600 mb-6">{currentScenario.description}</p>

              {/* Options */}
              <div className="space-y-4 mb-6">
                {currentScenario.options.map((option) => (
                  <DecisionOptionButton
                    key={option.id}
                    option={option}
                    onClick={() => handleOptionClick(option)}
                    isSelected={localState.selectedOption?.id === option.id}
                    isSubmitted={localState.submittedOption?.id === option.id}
                  />
                ))}
              </div>

              {/* Why It Matters - Only show after selection */}
              {optionToShow && (
                <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg animate-fadeIn">
                  <div className="text-sm font-semibold text-gray-700 mb-2">
                    Why It Matters
                  </div>
                  <p className="text-sm text-gray-600">
                    {optionToShow.content.why_matters}
                  </p>
                </div>
              )}

              {/* Explore Mode Banner - Only show after first submission */}
              {localState.hasAnswered && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2 text-blue-700">
                  <Eye className="w-5 h-5" />
                  <span className="text-sm font-medium">
                    Try choosing other options to hypothetically see what would happen
                  </span>
                </div>
              )}

              {/* Next Button - Only show after first submission */}
              {localState.hasAnswered && (
                <button
                  onClick={nextQuestion}
                  className="w-full py-4 px-6 rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold hover:shadow-lg hover:shadow-orange-500/30 hover:-translate-y-1 active:scale-95 transition-all duration-200 flex items-center justify-center gap-2"
                >
                  {questionNumber < totalQuestions ? (
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
          </div>

          {/* Right Sidebar - Analysis */}
          <div className="lg:col-span-1 space-y-6">
            {/* Projected Value Chart */}
            {localState.selectedOption && (
              <div className="bg-white rounded-xl shadow-md p-6">
                <div className="text-sm text-gray-500 mb-4">Projected Value (1 Year)</div>
                <GrowthChart
                  current={animatedBalance}
                  projected={animatedProjected}
                />
                <div className="mt-4 text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    ₹{animatedProjected.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-xs text-gray-500">
                    Based on selected option
                  </div>
                </div>
              </div>
            )}

            {/* Decision History */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="text-sm font-semibold text-gray-700 mb-4">
                DECISION HISTORY
              </div>
              {quizRun.history.length === 0 ? (
                <p className="text-sm text-gray-500">No decisions made yet</p>
              ) : (
                <div className="space-y-3">
                  {quizRun.history.map((log, index) => (
                    <div key={index} className="border-l-2 border-orange-500 pl-3">
                      <div className="text-sm font-medium text-gray-700 mb-1">
                        {log.text}
                      </div>
                      <div className="text-xs text-gray-500 mb-2">
                        +{log.score} points
                      </div>
                      {log.why_matters && (
                        <div className="text-xs text-gray-600 italic">
                          {log.why_matters}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

const ResultScreen: React.FC = () => {
  const { quizRun, resetGame } = useQuiz()
  const navigate = useNavigate()
  const [showConfetti, setShowConfetti] = useState(false)

  if (!quizRun) {
    return <div>No quiz data</div>
  }

  const maxScore = quizRun.scenarioIds.length * 20
  const percentage = maxScore > 0 ? (quizRun.totalScore / maxScore) * 100 : 0

  let badge: { name: string; color: BadgeColor; icon: typeof Trophy } = {
    name: 'Financial Novice',
    color: 'gray',
    icon: Trophy,
  }

  if (percentage >= 80) {
    badge = { name: 'Wealth Master', color: 'gold', icon: Trophy }
    if (!showConfetti) {
      setShowConfetti(true)
      setTimeout(() => setShowConfetti(false), 3000)
    }
  } else if (percentage >= 50) {
    badge = { name: 'Smart Saver', color: 'silver', icon: Target }
  } else if (percentage >= 30) {
    badge = { name: 'Budding Investor', color: 'bronze', icon: Target }
  }

  const BadgeIcon = badge.icon

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center p-6">
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-orange-500 rounded-full animate-ping"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
              }}
            />
          ))}
        </div>
      )}

      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-2xl p-8 md:p-12 text-center">
        <div className="mb-8">
          <div
            className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-6 ${
              badge.color === 'gold'
                ? 'bg-gradient-to-br from-yellow-400 to-yellow-600'
                : badge.color === 'silver'
                ? 'bg-gradient-to-br from-gray-300 to-gray-500'
                : badge.color === 'bronze'
                ? 'bg-gradient-to-br from-orange-400 to-orange-600'
                : 'bg-gradient-to-br from-gray-400 to-gray-600'
            }`}
          >
            <BadgeIcon className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            {badge.name}
          </h1>
          <div className="text-6xl font-bold text-orange-600 mb-2">
            {quizRun.totalScore}
          </div>
          <div className="text-gray-500 mb-4">
            out of {maxScore} points ({Math.round(percentage)}%)
          </div>
        </div>

        <div className="space-y-4">
          <button
            onClick={async () => {
              // Start a new quiz instead of resetting
              await startQuiz()
            }}
            className="w-full px-8 py-4 bg-gradient-to-r from-orange-500 to-orange-600 text-white font-bold text-lg rounded-xl shadow-lg hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200"
          >
            Play Again
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full px-8 py-4 bg-white border-2 border-gray-300 text-gray-700 font-semibold text-lg rounded-xl hover:bg-gray-50 transition-all duration-200 flex items-center justify-center gap-2"
          >
            <Home className="w-5 h-5" />
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

// ==================== MAIN APP ====================
const WealthPlaySimulator: React.FC = () => {
  const { screen, loadQuiz } = useQuiz()
  const { runId } = useParams<{ runId?: string }>()

  // If runId is in URL, load that quiz from backend
  useEffect(() => {
    if (runId) {
      loadQuiz(runId)
    } else {
      // Otherwise try localStorage
      const saved = localStorage.getItem('wealthplay_quiz_run')
      if (saved) {
        loadQuiz()
      }
    }
  }, [runId, loadQuiz])

  return (
    <div className="min-h-screen">
      {screen === 'START' && <StartScreen />}
      {screen === 'PLAY' && <ScenarioPlay />}
      {screen === 'RESULT' && <ResultScreen />}
    </div>
  )
}

// ==================== EXPORT ====================
const WealthPlaySimulatorWithProvider: React.FC = () => {
  return (
    <QuizProvider>
      <WealthPlaySimulator />
    </QuizProvider>
  )
}

export default WealthPlaySimulatorWithProvider
