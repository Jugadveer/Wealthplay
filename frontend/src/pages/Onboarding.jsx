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
        // Show level result
        setAssignedLevel({
          level: response.data.level,
          levelDisplay: response.data.level_display || response.data.level.charAt(0).toUpperCase() + response.data.level.slice(1),
          xp: response.data.xp
        })
        setShowLevelResult(true)
        
        // Refresh auth to get updated profile
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
        return 'bg-purple-100 text-purple-700 border-purple-500'
      case 'intermediate':
        return 'bg-blue-100 text-blue-700 border-blue-500'
      default:
        return 'bg-green-100 text-green-700 border-green-500'
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

  // Show level result screen
  if (showLevelResult && assignedLevel) {
    return (
      <div className="min-h-screen bg-muted-1 flex items-center justify-center p-6">
        <div className="max-w-2xl w-full bg-white rounded-xl shadow-card p-8 lg:p-12 text-center">
          {/* Success Icon */}
          <div className="mb-6 flex justify-center">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle2 className="w-12 h-12 text-green-600" />
            </div>
          </div>

          {/* Level Badge */}
          <h1 className="text-3xl font-bold text-text-main mb-4">Welcome to WealthPlay!</h1>
          <p className="text-lg text-text-muted mb-8">Based on your answers, we've assigned you a level:</p>
          
          <div className={`inline-block px-8 py-4 rounded-xl border-2 ${getLevelColor(assignedLevel.level)} mb-4`}>
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6" />
              <span className="text-2xl font-bold">{assignedLevel.levelDisplay}</span>
            </div>
          </div>

          <div className="bg-muted-1 rounded-xl p-6 mb-8">
            <p className="text-base text-text-muted mb-4">{getLevelDescription(assignedLevel.level)}</p>
            <div className="flex items-center justify-center gap-2 text-sm text-text-muted">
              <span className="font-semibold">Starting XP:</span>
              <span className="text-brand-1 font-bold">{assignedLevel.xp} XP</span>
            </div>
          </div>

          <button
            onClick={handleContinueToDashboard}
            className="w-full px-8 py-4 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold text-lg hover:shadow-lg hover:scale-105 transition-all flex items-center justify-center gap-2"
          >
            Continue to Dashboard
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted-1 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white rounded-xl shadow-card p-8 lg:p-12">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center">
            <Target className="w-6 h-6 text-brand-1" />
          </div>
          <h1 className="text-3xl font-bold text-text-main">Let's personalize your journey</h1>
        </div>

        {/* Progress Bar */}
        <div className="mb-10">
          <div className="flex items-center justify-between text-sm text-text-muted mb-2">
            <span>Question {currentQuestion} of {totalQuestions}</span>
            <span>{Math.round(progressPercent)}%</span>
          </div>
          <div className="w-full h-2 bg-muted-2 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-brand-1 to-brand-2 rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
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
                  className={`w-full flex items-center gap-4 p-5 rounded-xl border-2 transition-all duration-180 text-left ${
                    isSelected
                      ? 'border-brand-1 bg-brand-1/5 shadow-md scale-[1.02]'
                      : 'border-muted-3 bg-white hover:border-brand-1/50 hover:bg-muted-1'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0 ${
                      isSelected
                        ? 'border-brand-1 bg-brand-1'
                        : 'border-muted-3 bg-white'
                    }`}
                  >
                    {isSelected && <div className="w-3 h-3 rounded-full bg-white" />}
                  </div>
                  <span className="text-2xl">{option.icon}</span>
                  <span className="flex-1 text-lg font-medium text-text-main">{option.label}</span>
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
            className="flex items-center gap-2 px-8 py-3 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
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

