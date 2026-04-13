import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'
import { Target, ChevronRight, ChevronLeft, CheckCircle2, Sparkles } from 'lucide-react'

const Onboarding = () => {
  const navigate = useNavigate()
  const { checkAuth } = useAuth()
  const [currentQuestion, setCurrentQuestion] = useState(1)
  const [answers, setAnswers] = useState({
    financial_goal: '',
    investment_experience: '',
    risk_comfort: '',
    initial_investment: '',
    investment_timeline: '',
  })
  const [loading, setLoading] = useState(false)
  const [showLevelResult, setShowLevelResult] = useState(false)
  const [assignedLevel, setAssignedLevel] = useState(null)

  const totalQuestions = 5

  const questions = [
    {
      id: 1,
      title: "What's your main financial goal?",
      key: 'financial_goal',
      options: [
        { value: 'long_term_wealth', label: 'Build long-term wealth', icon: '🌱' },
        { value: 'specific_goals', label: 'Save for specific goals', icon: '🎯' },
        { value: 'learning', label: 'Just learning for now', icon: '📚' },
        { value: 'extra_income', label: 'Generate extra income', icon: '💰' },
      ],
    },
    {
      id: 2,
      title: "How familiar are you with investing?",
      key: 'investment_experience',
      options: [
        { value: 'beginner', label: 'Complete beginner', icon: '⭐' },
        { value: 'basics', label: 'Know the basics', icon: '📖' },
        { value: 'experienced', label: 'Fairly experienced', icon: '💡' },
        { value: 'very_experienced', label: 'Very experienced', icon: '🏆' },
      ],
    },
    {
      id: 3,
      title: "What's your risk comfort level?",
      key: 'risk_comfort',
      options: [
        { value: 'safe', label: 'Play it safe', icon: '🛡️' },
        { value: 'balanced', label: 'Balanced approach', icon: '⚖️' },
        { value: 'aggressive', label: 'Higher returns, higher risk', icon: '🚀' },
      ],
    },
    {
      id: 4,
      title: "How much would you invest initially (hypothetically)?",
      key: 'initial_investment',
      options: [
        { value: 'under_10k', label: 'Under ₹10,000', icon: '🏛️' },
        { value: '10k_50k', label: '₹10,000 - ₹50,000', icon: '💵' },
        { value: '50k_2l', label: '₹50,000 - ₹2,00,000', icon: '💎' },
        { value: 'over_2l', label: 'Over ₹2,00,000', icon: '👑' },
      ],
    },
    {
      id: 5,
      title: "What's your investment timeline?",
      key: 'investment_timeline',
      options: [
        { value: 'less_than_1', label: 'Less than 1 year', icon: '⚡' },
        { value: '1_to_5', label: '1-5 years', icon: '☀️' },
        { value: '5_plus', label: '5+ years', icon: '🌳' },
      ],
    },
  ]

  const progressPercent = (currentQuestion / totalQuestions) * 100
  const currentQuestionData = questions[currentQuestion - 1]
  const isAnswered = answers[currentQuestionData.key] !== ''
  const isLastQuestion = currentQuestion === totalQuestions
  const canProceed = isAnswered

  const handleSelect = (value) => {
    setAnswers((prev) => ({
      ...prev,
      [currentQuestionData.key]: value,
    }))
  }

  const handleNext = () => {
    if (isLastQuestion) {
      handleSubmit()
    } else {
      setCurrentQuestion((prev) => prev + 1)
    }
  }

  const handleBack = () => {
    if (currentQuestion > 1) {
      setCurrentQuestion((prev) => prev - 1)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const response = await api.saveOnboarding(answers)
      if (response.data.status === 'success') {
        
        setAssignedLevel({
          level: response.data.level,
          levelDisplay: response.data.level_display || response.data.level.charAt(0).toUpperCase() + response.data.level.slice(1),
          xp: response.data.xp
        })
        setShowLevelResult(true)
        
        
        await checkAuth()
      } else {
        alert('Error saving onboarding data. Please try again.')
      }
    } catch (error) {
      console.error('Error submitting onboarding:', error)
      alert('An error occurred. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleContinueToDashboard = () => {
    navigate('/dashboard')
  }

  const getLevelColor = (level) => {
    switch(level) {
      case 'advanced':
        return 'bg-brand-2/15 text-brand-2 border-brand-2/40'
      case 'intermediate':
        return 'bg-accent-blue/15 text-accent-blue border-accent-blue/40'
        default:
          return 'bg-brand-1/10 text-brand-1 border-brand-1/20'
    }
  }

  const getLevelDescription = (level) => {
    switch(level) {
      case 'advanced':
        return 'You have extensive investing experience! All courses are unlocked for you.'
      case 'intermediate':
        return 'You know the basics! Intermediate and beginner courses are available.'
      default:
        return 'Perfect for getting started! Beginner courses are ready for you.'
    }
  }

  
  if (showLevelResult && assignedLevel) {
    return (
      <div className="min-h-screen bg-retro-bg flex items-center justify-center p-6">
        <div className="max-w-2xl w-full bg-retro-surface rounded-3xl shadow-modal p-12 lg:p-16 text-center border border-brand-1/10">
          {}
          <div className="mb-8 flex justify-center">
            <div className="w-20 h-20 rounded-full bg-brand-1/10 flex items-center justify-center border border-brand-1/20 animate-bounce">
              <CheckCircle2 className="w-12 h-12 text-brand-1" />
            </div>
          </div>

          {}
          <h1 className="text-4xl font-extrabold text-brand-1 mb-4 tracking-tight">Welcome to WealthPlay!</h1>
          <p className="text-xl text-text-muted mb-10 leading-relaxed">Based on your onboarding assessment, you've been assigned:</p>
          
          <div className={`inline-block px-10 py-5 rounded-2xl border-2 ${getLevelColor(assignedLevel.level)} mb-6 shadow-lg shadow-brand-1/10`}>
            <div className="flex items-center gap-4">
              <Sparkles className="w-8 h-8" />
              <span className="text-3xl font-black uppercase tracking-widest">{assignedLevel.levelDisplay}</span>
            </div>
          </div>

          <div className="bg-brand-1/5 rounded-2xl p-8 mb-10 border border-brand-1/10">
            <p className="text-lg text-brand-1 font-semibold mb-3">{getLevelDescription(assignedLevel.level)}</p>
            <div className="flex items-center justify-center gap-2 text-sm text-text-muted">
              <span className="font-bold opacity-60">STARTING CAPITAL BONUS:</span>
              <span className="text-brand-1 font-black text-lg">+{assignedLevel.xp} XP</span>
            </div>
          </div>

          <button
            onClick={handleContinueToDashboard}
            className="w-full px-8 py-4 rounded-xl bg-brand-1 text-white font-semibold text-lg hover:bg-brand-600 hover:shadow-lg hover:scale-105 transition-all flex items-center justify-center gap-2"
          >
            Continue to Dashboard
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-retro-surface rounded-3xl shadow-modal p-12 lg:p-16 border border-brand-1/10 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-2 bg-brand-1/5">
           <div
             className="h-full transition-all duration-500 ease-out"
             style={{
               width: `${progressPercent}%`,
               backgroundColor: progressPercent >= 100 ? '#f59e0b' : '#ff6b35',
             }}
           ></div>
        </div>
        {/* Header */}
        <div className="flex items-center gap-4 mb-10">
          <div className="w-14 h-14 rounded-2xl bg-brand-1/10 flex items-center justify-center shadow-inner border border-brand-1/5">
            <Target className="w-7 h-7 text-brand-1" />
          </div>
          <div>
             <h1 className="text-3xl font-black text-brand-1 tracking-tight">Onboarding</h1>
             <p className="text-sm font-semibold text-text-muted">Personalize your journey</p>
          </div>
        </div>

        {/* Progress Text */}
        <div className="flex items-center justify-between text-xs font-black text-brand-1/40 uppercase tracking-widest mb-4">
            <span>QUESTION {currentQuestion} OF {totalQuestions}</span>
            <span>{Math.round(progressPercent)}% COMPLETE</span>
        </div>

        {/* Question */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-text-main mb-6">{currentQuestionData.title}</h2>
          
          <div className="space-y-3">
            {currentQuestionData.options.map((option) => {
              const isSelected = answers[currentQuestionData.key] === option.value
              return (
                <button
                  key={option.value}
                  onClick={() => handleSelect(option.value)}
                  className={`w-full flex items-center gap-6 p-6 rounded-2xl border-2 transition-all duration-200 text-left ${
                    isSelected
                      ? 'border-brand-1 bg-brand-1 shadow-lg text-white scale-[1.02]'
                      : 'border-brand-1/10 bg-retro-surface hover:border-brand-1/40 hover:bg-brand-1/5 text-text-main'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      isSelected
                        ? 'border-white bg-white'
                        : 'border-brand-1/20 bg-retro-surface'
                    }`}
                  >
                    <div className={`w-3 h-3 rounded-full transition-all ${isSelected ? 'bg-brand-1' : 'bg-transparent'}`} />
                  </div>
                  <span className="text-3xl">{option.icon}</span>
                  <span className={`flex-1 text-lg font-bold ${isSelected ? 'text-white' : 'text-text-main'}`}>{option.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-6 border-t border-muted-2">
          <button
            onClick={handleBack}
            disabled={currentQuestion === 1}
            className="flex items-center gap-2 px-6 py-3 rounded-xl border-2 border-muted-3 text-text-main font-semibold hover:border-brand-1 hover:text-brand-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
          
          <button
            onClick={handleNext}
            disabled={!canProceed || loading}
            className="flex items-center gap-2 px-8 py-3 rounded-xl bg-brand-1 text-white font-semibold hover:bg-brand-2 hover:shadow-lg hover:shadow-brand-1/20 hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            {loading ? (
              'Saving...'
            ) : isLastQuestion ? (
              <>
                Get Started
                <ChevronRight className="w-5 h-5" />
              </>
            ) : (
              <>
                Next
                <ChevronRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding

