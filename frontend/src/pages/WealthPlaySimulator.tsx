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
  Sparkles,
  Award,
} from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { apiAxios, axios } from '../utils/api'


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
  baseBalance: number 
  currentBalance: number
  currentRisk: number
  hasAnswered: boolean
  selectedOption: DecisionOption | null
  submittedOption: DecisionOption | null 
  hypotheticalScore: number
  projectedValue: number
}


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


const useAnimateNumber = (targetValue: number, duration: number = 500) => {
  const [displayValue, setDisplayValue] = useState(targetValue)
  const prevTargetRef = React.useRef(targetValue)
  const animationFrameRef = React.useRef<number | null>(null)
  const startValueRef = React.useRef(targetValue)

  useEffect(() => {
    
    if (prevTargetRef.current === targetValue) {
      return
    }
    
    
    if (animationFrameRef.current !== null) {
      cancelAnimationFrame(animationFrameRef.current)
      animationFrameRef.current = null
    }
    
    
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
    
    
    return () => {
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
    }
    
  }, [targetValue, duration]) 

  return displayValue
}


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
        const response = await apiAxios.get(`/scenario/api/scenario/${scenarioId}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
        if (response.data) {
          
          const options: DecisionOption[] = (response.data.choices || []).map((choice: any) => ({
            id: typeof choice.id === 'string' ? parseInt(choice.id) : choice.id, 
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
            currentRisk: 50, 
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
    
    if (runIdFromUrl) {
      try {
        const response = await apiAxios.get(`/scenario/api/quiz/${runIdFromUrl}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
        
        if (response.data.completed) {
          setScreen('RESULT')
          return
        }

        
        const scenarioIds = response.data.scenario_ids?.split(',').map((id: string) => parseInt(id)) || []
        const run: QuizRun = {
          runId: runIdFromUrl,
          scenarioIds: scenarioIds,
          currentQuestionIndex: (response.data.question_number || 1) - 1,
          totalScore: response.data.total_score || 0,
          isCompleted: false,
          history: [], 
        }
        setQuizRun(run)
        localStorage.setItem('wealthplay_quiz_run', JSON.stringify(run))
        setScreen('PLAY')
        await loadCurrentScenario(run)
        return
      } catch (error) {
        console.error('Error loading quiz from backend:', error)
        
        localStorage.removeItem('wealthplay_quiz_run')
        setScreen('START')
      }
    }

    
    const saved = localStorage.getItem('wealthplay_quiz_run')
    if (saved) {
      try {
        const run: QuizRun = JSON.parse(saved)
        const runId = parseInt(run.runId)
        
        
        if (!isNaN(runId)) {
          try {
            const verifyResponse = await apiAxios.get(`/scenario/api/quiz/${runId}/`, {
              headers: { Accept: 'application/json' },
              withCredentials: true,
            })
            
            
            const scenarioIds = verifyResponse.data.scenario_ids?.split(',').map((id: string) => parseInt(id)) || []
            const updatedRun: QuizRun = {
              runId: runId.toString(),
              scenarioIds: scenarioIds,
              currentQuestionIndex: (verifyResponse.data.question_number || 1) - 1,
              totalScore: verifyResponse.data.total_score || 0,
              isCompleted: verifyResponse.data.completed || false,
              history: run.history, 
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
            
            console.error('QuizRun not found in database, starting fresh:', verifyError)
            localStorage.removeItem('wealthplay_quiz_run')
            setScreen('START')
          }
        } else {
          
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
    
    
    const saved = localStorage.getItem('wealthplay_quiz_run')
    if (saved && !window.location.pathname.includes('/quiz/')) {
      loadQuiz()
    }
  }, [loadQuiz])

  const startQuiz = async () => {
    try {
      
      const response = await apiAxios.post('/scenario/api/start/', {})

      if (!response.data || !response.data.success || !response.data.runId) {
        alert('Failed to start quiz')
        return
      }

      const dbRunId = response.data.runId

      
      const quizResponse = await apiAxios.get(`/scenario/api/quiz/${dbRunId}/`, {
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

      
      await loadCurrentScenario(newRun)
      setScreen('PLAY')
    } catch (error) {
      console.error('Error starting quiz:', error)
      alert('Failed to start quiz. Please try again.')
    }
  }

  const handleChoice = (option: DecisionOption) => {
    if (!currentScenario) return

    
    const newBalance = Math.max(0, localState.baseBalance + option.impact.balance)
    
    
    
    
    const riskDelta = option.impact.risk 
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

      
      const runId = parseInt(quizRun.runId)
      if (isNaN(runId)) {
        console.error('Invalid runId:', quizRun.runId)
        
        localStorage.removeItem('wealthplay_quiz_run')
        alert('Invalid quiz session. Please start a new quiz.')
        setScreen('START')
        setQuizRun(null)
        return
      }

      
      try {
        await apiAxios.get(`/scenario/api/quiz/${runId}/`, {
          headers: { Accept: 'application/json' },
          withCredentials: true,
        })
      } catch (verifyError: any) {
        
        if (verifyError.response?.status === 404) {
          localStorage.removeItem('wealthplay_quiz_run')
          alert('Your quiz session expired. Please start a new quiz.')
          setScreen('START')
          setQuizRun(null)
          return
        }
        throw verifyError 
      }

      
      const optionId = typeof option.id === 'string' ? parseInt(option.id) : option.id
      if (isNaN(optionId)) {
        console.error('Invalid option ID:', option.id)
        alert('Invalid option selected. Please refresh and try again.')
        return
      }

      
      const response = await apiAxios.post('/scenario/api/submit-answer/', {
        run_id: runId,
        option_id: optionId,
        score: option.score,
      })

      
      const responseData = response.data || {}
      const newTotalScore = responseData.total_score ?? (quizRun.totalScore + option.score)
      const scoreAdded = responseData.score_added ?? option.score
      
      
      const currentIndex = responseData.current_question_index ?? quizRun.currentQuestionIndex
      
      
      
      
      
      const updatedRun: QuizRun = {
        ...quizRun,
        totalScore: newTotalScore,
        currentQuestionIndex: currentIndex, 
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

      
      setQuizRun({ ...updatedRun }) 
      localStorage.setItem('wealthplay_quiz_run', JSON.stringify(updatedRun))
      setLocalState({ 
        ...localState, 
        hasAnswered: true,
        submittedOption: option,
        
        selectedOption: option,
      })
    } catch (error: any) {
      console.error('Error submitting choice:', error)
      
      
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
      
      
      alert('Failed to submit answer. Please try again.')
    }
  }

  const nextQuestion = async () => {
    if (!quizRun) return

    const nextIndex = quizRun.currentQuestionIndex + 1
    if (nextIndex >= quizRun.scenarioIds.length) {
      
      try {
        const runId = parseInt(quizRun.runId)
        if (!isNaN(runId)) {
          
          try {
            await apiAxios.post(`/scenario/api/quiz/${runId}/complete/`, {})
          } catch (e) {
            
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

    
    try {
      const runId = parseInt(quizRun.runId)
      if (!isNaN(runId)) {
        await apiAxios.post(`/scenario/api/quiz/${runId}/next/`, {})
      }
    } catch (error) {
      console.error('Error advancing question:', error)
    }

    
    const updatedRun: QuizRun = {
      ...quizRun,
      currentQuestionIndex: nextIndex,
    }

    setQuizRun(updatedRun)
    localStorage.setItem('wealthplay_quiz_run', JSON.stringify(updatedRun))

    
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



const RiskGauge: React.FC<{ risk: number }> = ({ risk }) => {
  
  const clampedRisk = Math.max(0, Math.min(100, risk))
  
  const rotation = clampedRisk * 1.8 - 90

  return (
    <div className="relative w-full h-40 flex items-center justify-center">
      {}
      <svg className="w-full h-full" viewBox="0 0 200 100" style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#22c55e" />
            <stop offset="50%" stopColor="#eab308" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <path
          d="M 20 80 A 80 80 0 0 1 180 80"
          fill="none"
          stroke="url(#riskGradient)"
          strokeWidth="14"
          strokeLinecap="round"
          className="opacity-20"
        />
        <path
          d="M 20 80 A 80 80 0 0 1 180 80"
          fill="none"
          stroke="#ff6b35"
          strokeWidth="14"
          strokeLinecap="round"
          strokeDasharray={`${clampedRisk * 2.51} 251`}
          className="transition-all duration-1000 ease-out"
        />
        <text x="25" y="95" className="text-xs fill-brand-1/40 font-bold uppercase tracking-tighter">Safe</text>
        <text x="165" y="95" className="text-xs fill-brand-1/40 font-bold uppercase tracking-tighter">Risky</text>
      </svg>
      
      {}
      <div
        className="absolute bottom-0 left-1/2 w-1 h-20 bg-brand-1 transition-transform duration-700 ease-out"
        style={{
          transform: `translateX(-50%) rotate(${rotation}deg)`,
          transformOrigin: 'bottom center',
        }}
      >
        <div className="w-2 h-2 rounded-full bg-brand-1 absolute -top-1 -left-0.5 shadow-sm"></div>
      </div>
      
      {}
      <div className="absolute bottom-0 left-1/2 w-4 h-4 bg-brand-1 rounded-full transform -translate-x-1/2 translate-y-2 border-2 border-retro-surface shadow-sm" />
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
            backgroundColor: '#ffffff',
            border: '1px solid rgba(50,82,68,0.1)',
            borderRadius: '12px',
            boxShadow: '0 10px 30px rgba(50,82,68,0.08)',
          }}
        />
        <Bar dataKey="value" fill="#ff6b35" radius={[8, 8, 4, 4]} />
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
    INVEST: 'bg-brand-1/10 border-brand-1 text-brand-1',
    SAVE: 'bg-brand-1/10 border-brand-1/20 text-brand-1',
    SPEND: 'bg-orange-100 border-orange-600 text-orange-800',
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
          : 'bg-retro-surface border-brand-1/10 hover:border-brand-1 hover:bg-brand-1/5 hover:shadow-card-hover'
      } ${isSubmitted && !isSelected ? 'opacity-40 grayscale-[0.5]' : ''}`}
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
    <div className="bg-retro-bg flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-retro-surface rounded-3xl shadow-modal p-12 md:p-16 text-center border border-brand-1/20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-1/5 via-transparent to-brand-1/10 pointer-events-none"></div>
        <div className="absolute top-0 left-0 w-full h-1.5 bg-brand-1"></div>
        <div className="mb-10 relative z-10">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-brand-1/10 rounded-full mb-8 border border-brand-1/20 shadow-inner">
            <Trophy className="w-12 h-12 text-brand-1" />
          </div>
          <h1 className="text-5xl font-black text-brand-1 mb-4 tracking-tight">
            WealthPlay
          </h1>
          <p className="text-xl font-bold text-brand-1/60 mb-2">
            Master Financial Decision-Making
          </p>
          <p className="text-text-muted font-medium">
            Test your financial wisdom through immersive real-world scenarios
          </p>
        </div>

        <button
          onClick={startQuiz}
          className="w-full md:w-auto px-10 py-5 bg-brand-1 text-white font-black text-xl rounded-2xl shadow-lg shadow-brand-1/20 hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-200 flex items-center justify-center gap-3 mx-auto uppercase tracking-wider"
        >
          Start Challenge
          <ArrowRight className="w-6 h-6" />
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
      <div className="flex items-center justify-center min-h-screen bg-retro-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  const questionNumber = quizRun.currentQuestionIndex + 1
  const totalQuestions = quizRun.scenarioIds.length
  const progress = (questionNumber / totalQuestions) * 100

  const handleOptionClick = async (option: DecisionOption) => {
    
    handleChoice(option)
    
    
    if (!localState.hasAnswered) {
      await submitChoice(option)
    }
  }

  
  const optionToShow = localState.selectedOption

  return (
    <div className="min-h-screen bg-retro-bg">
      {}
      <div className="bg-retro-surface/95 backdrop-blur border-b border-brand-1/20 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <button
            onClick={() => navigate('/scenario')}
            className="group flex items-center gap-2 px-5 py-2.5 rounded-full text-brand-1 font-bold bg-brand-1/10 hover:bg-brand-1/20 transition-all duration-200"
          >
            <ArrowRight className="w-4 h-4 rotate-180 group-hover:-translate-x-1 transition-transform" />
            Back to Scenarios
          </button>
          <div className="flex items-center gap-8">
            <div className="text-right">
              <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-0.5">PROGRESS</div>
              <div className="text-lg font-black text-brand-1 tabular-nums">
                {questionNumber} <span className="text-brand-1/30 font-medium">/</span> {totalQuestions}
              </div>
            </div>
            <div className="w-40 h-3 bg-brand-1/5 rounded-full overflow-hidden border border-brand-1/10 p-0.5">
              <div
                className="h-full rounded-full transition-all duration-1000 cubic-bezier(0.4, 0, 0.2, 1)"
                style={{
                  width: `${progress}%`,
                  backgroundColor: progress >= 100 ? '#f59e0b' : '#ff6b35',
                }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {}
          <div className="lg:col-span-1 space-y-6">
            {}
            <div className="bg-retro-surface rounded-3xl p-8 border border-brand-1/20 shadow-card relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-brand-1/5 rounded-full -mr-16 -mt-16 transition-transform group-hover:scale-110 duration-700"></div>
              <div className="relative z-10">
                <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-2">CURRENT CAPITAL</div>
                <div className="text-4xl font-black text-brand-1 tabular-nums">
                  ₹{animatedBalance.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </div>
              </div>
            </div>

            {}
            <div className="bg-retro-surface rounded-3xl p-8 border border-brand-1/20 shadow-card relative overflow-hidden group">
               <div className="absolute bottom-0 right-0 w-24 h-24 bg-brand-1/10 rounded-full -mr-8 -mb-8"></div>
              <div className="relative z-10">
                <div className="text-[10px] font-black text-brand-1/50 uppercase tracking-widest mb-2">STRATEGY SCORE</div>
                <div className="text-4xl font-black text-brand-1 tabular-nums">
                  {quizRun.totalScore}
                </div>
              </div>
            </div>

            {}
            <div className="bg-retro-surface rounded-3xl shadow-card p-8 border border-brand-1/20">
              <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-6 text-center">RISK EXPOSURE</div>
              <RiskGauge risk={localState.currentRisk} />
            </div>
          </div>

          {}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-retro-surface rounded-3xl shadow-modal p-10 border border-brand-1/20 relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-brand-1/5 via-transparent to-brand-1/10 pointer-events-none"></div>
              <div className="absolute top-8 left-0 w-1.5 h-10 bg-brand-1 rounded-r-full"></div>
              <h2 className="relative text-3xl font-black text-brand-1 mb-6 leading-tight tracking-tight">
                {currentScenario.title}
              </h2>
              <p className="relative text-lg text-text-muted font-medium mb-10 leading-relaxed italic border-l-4 border-brand-1/10 pl-6">"{currentScenario.description}"</p>

              {}
              <div className="relative space-y-4 mb-10">
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

              {}
              {optionToShow && (
                <div className="mb-8 p-6 bg-brand-1/5 border border-brand-1/10 rounded-2xl animate-[fadeIn_0.5s_ease-out] relative">
                  <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-5 h-5 text-brand-1" />
                    <div className="text-xs font-black text-brand-1/60 uppercase tracking-widest">
                      STRATEGIC RATIONALE
                    </div>
                  </div>
                  <p className="text-brand-1 font-bold leading-relaxed">
                    {optionToShow.content.why_matters}
                  </p>
                </div>
              )}

              {}
              {localState.hasAnswered && (
                <div className="mb-8 p-5 bg-brand-1/10 border border-brand-1/20 rounded-2xl flex items-center gap-4 text-brand-1">
                  <div className="w-10 h-10 rounded-full bg-retro-surface flex items-center justify-center flex-shrink-0 shadow-sm border border-brand-1/10">
                    <Eye className="w-5 h-5 text-brand-1" />
                  </div>
                  <span className="text-sm font-bold leading-tight">
                    EXPLORATION MODE: <span className="font-medium text-brand-1/70">Try other options to see their hypothetical impact.</span>
                  </span>
                </div>
              )}

              {}
              {localState.hasAnswered && (
                <button
                  onClick={nextQuestion}
                  className="w-full py-5 px-8 rounded-2xl bg-brand-1 text-white font-black text-xl hover:shadow-xl hover:shadow-brand-1/20 hover:-translate-y-1 active:scale-95 transition-all duration-300 flex items-center justify-center gap-3 group shadow-lg shadow-brand-1/10"
                >
                  {questionNumber < totalQuestions ? (
                    <>
                      Next Challenge
                      <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                    </>
                  ) : (
                    <>
                      Finalize Simulation
                      <Trophy className="w-6 h-6 group-hover:scale-110 transition-transform" />
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {}
          <div className="lg:col-span-1 space-y-6">
            {}
            {localState.selectedOption && (
              <div className="bg-retro-surface rounded-3xl shadow-card p-8 border border-brand-1/20 relative overflow-hidden">
                <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-6">IMPACT PROJECTION (1Y)</div>
                <GrowthChart
                  current={animatedBalance}
                  projected={animatedProjected}
                />
                <div className="mt-8 text-center pt-6 border-t border-brand-1/5">
                  <div className="text-3xl font-black text-brand-1 tabular-nums">
                    ₹{animatedProjected.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                  </div>
                  <div className="text-[10px] font-black text-brand-1/30 uppercase tracking-widest mt-1">
                    POTENTIAL FUTURE VALUE
                  </div>
                </div>
              </div>
            )}

            {}
            <div className="bg-retro-surface rounded-3xl shadow-card p-8 border border-brand-1/20">
              <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-6">
                SIMULATION LOG
              </div>
              {quizRun.history.length === 0 ? (
                <div className="py-10 text-center opacity-30">
                   <Target className="w-12 h-12 mx-auto mb-3" />
                   <p className="text-xs font-bold uppercase">Awaiting first move...</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {quizRun.history.map((log, index) => (
                    <div key={index} className="relative pl-6">
                      <div className="absolute top-1 left-0 w-1.5 h-1.5 rounded-full bg-brand-1 shadow-[0_0_8px_rgba(50,82,68,0.5)]"></div>
                      {index < quizRun.history.length - 1 && (
                        <div className="absolute top-3 left-[2px] w-0.5 h-[calc(100%+8px)] bg-brand-1/10"></div>
                      )}
                      <div className="text-sm font-black text-brand-1 mb-0.5 tracking-tight">
                        {log.text}
                      </div>
                      <div className="text-[10px] font-black text-brand-1/40 uppercase tracking-widest mb-2">
                        +{log.score} STRATEGY XP
                      </div>
                      {log.why_matters && (
                        <div className="text-xs text-text-muted font-medium leading-relaxed">
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
  const { quizRun, resetGame, startQuiz } = useQuiz()
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
    <div className="min-h-screen bg-retro-bg flex items-center justify-center p-6 overflow-hidden">
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array.from({ length: 100 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-brand-1 rounded-full animate-ping"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                opacity: Math.random(),
              }}
            />
          ))}
        </div>
      )}

      <div className="max-w-2xl w-full bg-retro-surface rounded-3xl shadow-modal p-12 md:p-16 text-center border border-brand-1/20 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-1/5 via-transparent to-brand-1/10 pointer-events-none"></div>
        <div className="absolute top-0 left-0 w-full h-2 bg-brand-1 rounded-t-3xl"></div>
        <div className="mb-12 relative z-10">
          <div
            className={`inline-flex items-center justify-center w-32 h-32 rounded-full mb-8 shadow-xl relative group ${
              badge.color === 'gold'
                ? 'bg-gradient-to-br from-yellow-400 to-yellow-600'
                : badge.color === 'silver'
                ? 'bg-gradient-to-br from-brand-1/40 to-brand-1/60'
                : badge.color === 'bronze'
                ? 'bg-gradient-to-br from-orange-400 to-orange-600'
                : 'bg-gradient-to-br from-brand-1/10 to-brand-1/30'
            }`}
          >
            <div className="absolute inset-2 border-2 border-white/20 rounded-full"></div>
            <BadgeIcon className="w-16 h-16 text-white relative z-10" />
          </div>
          <h1 className="text-4xl md:text-5xl font-black text-brand-1 mb-4 tracking-tight uppercase">
            {badge.name}
          </h1>
          <div className="text-7xl font-black text-brand-1 mb-2 tabular-nums">
            {quizRun.totalScore}
          </div>
          <div className="text-sm font-black text-brand-1/40 uppercase tracking-widest mb-4">
            STRATEGY XP earned • <span className="text-brand-1/60">{Math.round(percentage)}% ACCURACY</span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
          <button
            onClick={async () => {
              await startQuiz()
            }}
            className="w-full px-8 py-5 bg-brand-1 text-white font-black text-xl rounded-2xl shadow-lg shadow-brand-1/20 hover:shadow-xl hover:scale-105 active:scale-95 transition-all duration-300 md:col-span-2"
          >
            PLAY AGAIN
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full px-8 py-5 bg-retro-surface border-2 border-brand-1/20 text-brand-1 font-black text-lg rounded-2xl hover:bg-brand-1/10 hover:border-brand-1 transition-all duration-200 flex items-center justify-center gap-3"
          >
            <Home className="w-6 h-6" />
            DASHBOARD
          </button>
           <button
            onClick={() => navigate('/achievements')}
            className="w-full px-8 py-5 bg-retro-surface border-2 border-brand-1/20 text-brand-1 font-black text-lg rounded-2xl hover:bg-brand-1/10 hover:border-brand-1 transition-all duration-200 flex items-center justify-center gap-3"
          >
            <Award className="w-6 h-6" />
            BADGES
          </button>
        </div>
      </div>
    </div>
  )
}


const WealthPlaySimulator: React.FC = () => {
  const { screen, loadQuiz } = useQuiz()
  const { runId } = useParams<{ runId?: string }>()

  
  useEffect(() => {
    if (runId) {
      loadQuiz(runId)
    } else {
      
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


const WealthPlaySimulatorWithProvider: React.FC = () => {
  return (
    <QuizProvider>
      <WealthPlaySimulator />
    </QuizProvider>
  )
}

export default WealthPlaySimulatorWithProvider
