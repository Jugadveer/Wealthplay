import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'
import {
  ArrowLeft,
  Plus,
  Target,
  Wallet,
  TrendingUp,
  Edit2,
  Trash2,
  Check,
  X,
  Home,
  Car,
  Plane,
  Smartphone,
  GraduationCap,
  Gem,
  Lightbulb,
} from 'lucide-react'

const Goals = () => {
  const navigate = useNavigate()
  const [goals, setGoals] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingGoal, setEditingGoal] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    icon: 'wallet',
    target_amount: '',
    current_amount: '0',
    monthly_sip: '',
    time_to_goal: '',
  })

  const iconMap = {
    wallet: Wallet,
    home: Home,
    car: Car,
    plane: Plane,
    smartphone: Smartphone,
    'graduation-cap': GraduationCap,
    gem: Gem,
    lightbulb: Lightbulb,
  }

  const iconOptions = [
    'wallet',
    'smartphone',
    'plane',
    'home',
    'car',
    'graduation-cap',
    'gem',
    'lightbulb',
  ]

  useEffect(() => {
    loadGoals()
  }, [])

  const loadGoals = async () => {
    try {
      const response = await api.getGoals()
      setGoals(response.data.goals || [])
    } catch (error) {
      console.error('Error loading goals:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const data = {
        ...formData,
        target_amount: parseFloat(formData.target_amount),
        current_amount: parseFloat(formData.current_amount || 0),
        monthly_sip: parseFloat(formData.monthly_sip),
        time_to_goal: parseInt(formData.time_to_goal),
        color: 'from-brand-primary to-orange-500',
        icon_bg: 'bg-brand-50 text-brand-600',
      }

      if (editingGoal) {
        await api.updateGoal(editingGoal.id, data)
      } else {
        await api.createGoal(data)
      }

      setModalOpen(false)
      setEditingGoal(null)
      resetForm()
      loadGoals()
    } catch (error) {
      console.error('Error saving goal:', error)
      alert(error.response?.data?.error || 'Error saving goal')
    }
  }

  const handleDelete = async (goalId) => {
    if (!confirm('Are you sure you want to delete this goal?')) return

    try {
      await api.deleteGoal(goalId)
      loadGoals()
    } catch (error) {
      console.error('Error deleting goal:', error)
      alert('Error deleting goal')
    }
  }

  const handleEdit = (goal) => {
    setEditingGoal(goal)
    setFormData({
      name: goal.name,
      icon: goal.icon,
      target_amount: goal.target_amount.toString(),
      current_amount: goal.current_amount.toString(),
      monthly_sip: goal.monthly_sip.toString(),
      time_to_goal: goal.time_to_goal_months.toString(),
    })
    setModalOpen(true)
  }

  const resetForm = () => {
    setFormData({
      name: '',
      icon: 'wallet',
      target_amount: '',
      current_amount: '0',
      monthly_sip: '',
      time_to_goal: '',
    })
    setEditingGoal(null)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const calculateProgress = (goal) => {
    if (!goal.target_amount || goal.target_amount === 0) return 0
    return Math.min(100, Math.max(0, ((goal.current_amount / goal.target_amount) * 100).toFixed(1)))
  }

  const calculateRemaining = (goal) => {
    return Math.max(0, goal.target_amount - goal.current_amount)
  }

  const totalTarget = goals.reduce((sum, g) => sum + parseFloat(g.target_amount || 0), 0)
  const totalSaved = goals.reduce((sum, g) => sum + parseFloat(g.current_amount || 0), 0)
  const totalSIP = goals.reduce((sum, g) => sum + parseFloat(g.monthly_sip || 0), 0)

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-gradient-to-r from-brand-1 to-brand-2 shadow-lg px-6 py-6 lg:px-10">
        <div className="max-w-container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-5">
            <button
              onClick={() => navigate(-1)}
              className="bg-white text-text-main px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:bg-muted-1 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div>
              <h1 className="text-3xl font-bold text-white tracking-tight">Financial Goals</h1>
              <p className="text-base text-white/90 hidden sm:block opacity-90">
                Track your dreams and savings
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              resetForm()
              setModalOpen(true)
            }}
            className="bg-white/20 backdrop-blur-sm hover:bg-white/30 border border-white/40 text-white px-6 py-3 rounded-full font-medium text-sm flex items-center gap-2 transition-all active:scale-95"
          >
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Add Goal</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
          <div className="bg-gradient-to-br from-brand-1 to-brand-2 rounded-xl p-6 text-white shadow-xl">
            <div className="flex items-center gap-3 mb-3 opacity-90">
              <Target className="w-5 h-5" />
              <span className="text-sm font-semibold uppercase tracking-wide">Total Target</span>
            </div>
            <div className="text-3xl font-bold">{formatCurrency(totalTarget)}</div>
          </div>
          <div className="bg-white border border-muted-2 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-3 text-text-muted">
              <Wallet className="w-5 h-5 text-brand-1" />
              <span className="text-sm font-semibold uppercase tracking-wide">Total Saved</span>
            </div>
            <div className="text-3xl font-bold text-text-main">{formatCurrency(totalSaved)}</div>
          </div>
          <div className="bg-white border border-muted-2 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-3 text-text-muted">
              <TrendingUp className="w-5 h-5 text-brand-1" />
              <span className="text-sm font-semibold uppercase tracking-wide">Monthly SIP</span>
            </div>
            <div className="text-3xl font-bold text-brand-1">{formatCurrency(totalSIP)}</div>
          </div>
        </div>

        {/* Goals Grid */}
        {goals.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-muted-3 mb-4">
              <Target className="w-16 h-16 mx-auto mb-4" />
            </div>
            <h3 className="text-xl font-semibold text-text-main mb-2">No goals yet</h3>
            <p className="text-text-muted mb-6">Create your first financial goal to get started!</p>
            <button
              onClick={() => {
                resetForm()
                setModalOpen(true)
              }}
              className="bg-brand-1 text-white px-6 py-3 rounded-xl font-semibold hover:bg-brand-2 transition-colors"
            >
              Create Your First Goal
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {goals.map((goal) => {
              const IconComponent = iconMap[goal.icon] || Wallet
              const progress = calculateProgress(goal)
              const remaining = calculateRemaining(goal)

              return (
                <div
                  key={goal.id}
                  className="bg-white rounded-2xl shadow-sm border border-muted-2 p-8 transition-all duration-300 hover:shadow-card-hover hover:-translate-y-1"
                >
                  {/* Header */}
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-5">
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl shadow-sm bg-brand-1/10">
                        <IconComponent className="w-8 h-8 text-brand-1" />
                      </div>
                      <div>
                        <h3 className="font-bold text-xl text-text-main leading-tight">
                          {goal.name}
                        </h3>
                        <p className="text-base text-text-muted font-medium mt-1">
                          <span className="text-text-main">{formatCurrency(goal.current_amount)}</span>
                          <span className="mx-1 text-muted-3">/</span>
                          {formatCurrency(goal.target_amount)}
                        </p>
                      </div>
                    </div>
                    <div className="bg-brand-1/10 px-4 py-1.5 rounded-full text-sm font-bold text-brand-1 border border-brand-1/20">
                      {progress}%
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-muted-2 rounded-full h-4 overflow-hidden mt-2 mb-8 relative">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-brand-1 to-brand-2 transition-all duration-1000 ease-out relative"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="absolute top-0 left-0 bottom-0 right-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[progress-shimmer_2s_infinite]"></div>
                    </div>
                  </div>

                  {/* Details Grid */}
                  <div className="grid grid-cols-3 gap-6 py-5 border-t border-muted-2">
                    <div className="text-center sm:text-left">
                      <p className="text-xs text-text-muted font-bold uppercase tracking-widest mb-1.5">
                        SIP
                      </p>
                      <p className="font-bold text-lg text-text-main">
                        {formatCurrency(goal.monthly_sip)}
                      </p>
                    </div>
                    <div className="text-center sm:text-left border-l border-muted-2 pl-6">
                      <p className="text-xs text-text-muted font-bold uppercase tracking-widest mb-1.5">
                        Time
                      </p>
                      <p className="font-bold text-lg text-text-main">
                        {goal.time_to_goal_months} mths
                      </p>
                    </div>
                    <div className="text-center sm:text-left border-l border-muted-2 pl-6">
                      <p className="text-xs text-text-muted font-bold uppercase tracking-widest mb-1.5">
                        Left
                      </p>
                      <p className="font-bold text-lg text-text-main">{formatCurrency(remaining)}</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-4 mt-6">
                    <button
                      onClick={() => handleEdit(goal)}
                      className="flex-1 bg-brand-1/10 hover:bg-brand-1/20 text-brand-1 py-3.5 rounded-xl text-sm font-bold transition-colors border border-brand-1/20 flex items-center justify-center gap-2"
                    >
                      <Edit2 className="w-4 h-4" />
                      Adjust
                    </button>
                    <button
                      onClick={() => handleDelete(goal.id)}
                      className="flex-1 bg-red-50 hover:bg-red-100 text-red-600 py-3.5 rounded-xl text-sm font-bold transition-colors border border-red-100 flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" />
                      Delete
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>

      {/* Add/Edit Goal Modal */}
      {modalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setModalOpen(false)
              resetForm()
            }
          }}
        >
          <div className="relative w-full max-w-lg bg-white rounded-3xl shadow-2xl transform transition-all animate-[modalEnter_360ms_ease-out_forwards] overflow-hidden">
            {/* Modal Header */}
            <div className="bg-brand-1/10 px-8 py-5 border-b border-brand-1/20 flex justify-between items-center">
              <h2 className="text-xl font-bold text-text-main">
                {editingGoal ? 'Edit Goal' : 'Create New Goal'}
              </h2>
              <button
                onClick={() => {
                  setModalOpen(false)
                  resetForm()
                }}
                className="text-text-muted hover:text-text-main p-2 rounded-full hover:bg-brand-1/10 transition-colors"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            {/* Modal Form */}
            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              <div>
                <label className="block text-sm font-medium text-text-main mb-1.5">
                  Goal Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Dream Home"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all text-text-main placeholder:text-text-muted text-base"
                />
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1.5">
                    Target Amount (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.target_amount}
                    onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all text-base"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1.5">
                    Saved So Far (₹)
                  </label>
                  <input
                    type="number"
                    min="0"
                    value={formData.current_amount}
                    onChange={(e) => setFormData({ ...formData, current_amount: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all text-base"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1.5">
                    Monthly SIP (₹)
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.monthly_sip}
                    onChange={(e) => setFormData({ ...formData, monthly_sip: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all text-base"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text-main mb-1.5">
                    Months to Goal
                  </label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={formData.time_to_goal}
                    onChange={(e) => setFormData({ ...formData, time_to_goal: e.target.value })}
                    className="w-full px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all text-base"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-text-main mb-2">Choose Icon</label>
                <div className="flex gap-3 overflow-x-auto pb-2">
                  {iconOptions.map((icon) => {
                    const IconComponent = iconMap[icon]
                    return (
                      <button
                        key={icon}
                        type="button"
                        onClick={() => setFormData({ ...formData, icon })}
                        className={`p-3.5 rounded-xl border-2 transition-all flex-shrink-0 ${
                          formData.icon === icon
                            ? 'border-brand-1 bg-brand-1/10 text-brand-1 ring-2 ring-brand-1/20'
                            : 'border-muted-3 text-text-muted hover:border-brand-1/50 hover:text-brand-1'
                        }`}
                      >
                        <IconComponent className="w-6 h-6" />
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="pt-6 flex gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setModalOpen(false)
                    resetForm()
                  }}
                  className="flex-1 py-3.5 rounded-xl border-2 border-muted-3 text-text-main font-semibold hover:bg-muted-1 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-[2] py-3.5 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold hover:shadow-lg hover:shadow-brand-1/20 active:scale-95 transition-all"
                >
                  {editingGoal ? 'Update Goal' : 'Save Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Goals


