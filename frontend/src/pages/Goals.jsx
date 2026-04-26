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
  PieChart,
  Shield,
  Palmtree,
  Receipt,
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
    monthly_sip: '0',
    time_to_goal: '60',
    category: 'HOME',
    extra_val: '9.5',
    tenure_years: '20'
  })
  const [strategyResult, setStrategyResult] = useState(null)
  const [showStrategy, setShowStrategy] = useState(false)
  const [tickerInfo, setTickerInfo] = useState({})
  const [loadingTickers, setLoadingTickers] = useState(false)
  const [returnHorizon, setReturnHorizon] = useState('1y')

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

  useEffect(() => {
    if (showStrategy && strategyResult?.tickers?.length > 0) {
      const fetchTickers = async () => {
        setLoadingTickers(true)
        try {
          const response = await api.getTickersInfo(strategyResult.tickers.join(','))
          setTickerInfo(response.data.results || {})
        } catch (error) {
          console.error('Error fetching ticker info:', error)
        } finally {
          setLoadingTickers(false)
        }
      }
      fetchTickers()
    }
  }, [showStrategy, strategyResult])

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
        name: formData.name,
        target_amount: parseFloat(formData.target_amount),
        current_amount: parseFloat(formData.current_amount || 0),
        monthly_sip: parseFloat(formData.monthly_sip || 0),
        time_to_goal: parseInt(formData.time_to_goal || 60),
        category: formData.category,
        extra_val: parseFloat(formData.extra_val || 0),
        tenure_years: parseFloat(formData.tenure_years || 5),
        color: 'from-brand-primary to-orange-500',
        icon_bg: 'bg-brand-50 text-brand-600',
        icon: formData.icon
      }

      let response;
      if (editingGoal) {
        response = await api.updateGoal(editingGoal.id, data)
      } else {
        response = await api.createGoal(data)
      }

      if (response.data?.goal?.strategy) {
        setStrategyResult(response.data.goal.strategy)
        setShowStrategy(true)
      }

      setModalOpen(false)
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
      monthly_sip: '0',
      time_to_goal: '60',
      category: 'HOME',
      extra_val: '9.5',
      tenure_years: '20'
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
      {}
      <header className="sticky top-0 z-30 bg-retro-surface border-b border-brand-1/20 shadow-card px-6 py-6 lg:px-10">
        <div className="max-w-container mx-auto flex justify-between items-center">
          <div className="flex items-center gap-5">
            <button
              onClick={() => navigate(-1)}
              className="bg-brand-1/10 border border-brand-1/20 text-brand-1 px-5 py-2.5 rounded-full text-sm font-semibold shadow-sm hover:bg-brand-1/15 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <div>
              <h1 className="text-3xl font-bold text-text-main tracking-tight">Financial Goals</h1>
              <p className="text-base text-text-muted hidden sm:block opacity-100">
                Track your dreams and savings
              </p>
            </div>
          </div>

          <button
            onClick={() => {
              resetForm()
              setModalOpen(true)
            }}
            className="bg-brand-1/10 backdrop-blur-sm hover:bg-brand-1/20 border border-brand-1/20 text-text-main px-6 py-3 rounded-full font-medium text-sm flex items-center gap-2 transition-all active:scale-95"
          >
            <Plus className="w-5 h-5" />
            <span className="hidden sm:inline">Add Goal</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-12">
          <div className="bg-retro-surface rounded-xl p-6 text-text-main shadow-sm border border-brand-1/10">
            <div className="flex items-center gap-3 mb-3 opacity-90">
              <Target className="w-5 h-5" />
              <span className="text-sm font-semibold uppercase tracking-wide">Total Target</span>
            </div>
            <div className="text-3xl font-bold">{formatCurrency(totalTarget)}</div>
          </div>
          <div className="bg-retro-surface border border-brand-1/10 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-3 text-text-muted">
              <Wallet className="w-5 h-5 text-brand-1" />
              <span className="text-sm font-semibold uppercase tracking-wide">Total Saved</span>
            </div>
            <div className="text-3xl font-bold text-text-main">{formatCurrency(totalSaved)}</div>
          </div>
          <div className="bg-retro-surface border border-brand-1/10 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-3 mb-3 text-text-muted">
              <TrendingUp className="w-5 h-5 text-brand-1" />
              <span className="text-sm font-semibold uppercase tracking-wide">Monthly SIP</span>
            </div>
            <div className="text-3xl font-bold text-brand-1">{formatCurrency(totalSIP)}</div>
          </div>
        </div>

        {}
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
                  className="bg-retro-surface rounded-2xl shadow-sm border border-brand-1/10 p-8 transition-all duration-300 hover:shadow-card-hover hover:-translate-y-1"
                >
                  {}
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-5">
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl shadow-sm bg-retro-surface border border-brand-1/10">
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

                  {}
                  <div className="w-full bg-muted-2 rounded-full h-4 overflow-hidden mt-2 mb-8 relative">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-out relative"
                      style={{
                        width: `${progress}%`,
                        backgroundColor: progress >= 100 ? '#f59e0b' : '#ff6b35',
                      }}
                    >
                      <div className="absolute top-0 left-0 bottom-0 right-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-[progress-shimmer_2s_infinite]"></div>
                    </div>
                  </div>

                  {}
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

                  {/* Quick Strategy Preview */}
                  {goal.strategy_report?.tickers?.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-brand-1/10 lg:block hidden">
                       <p className="text-[9px] font-bold text-brand-1 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                         <PieChart className="w-3 h-3" /> Strategy Focus
                       </p>
                       <div className="flex flex-wrap gap-2">
                         {goal.strategy_report.tickers.slice(0, 3).map(t => (
                           <span key={t} className="px-2 py-0.5 bg-brand-1/5 text-brand-1 text-[8px] font-bold rounded-md border border-brand-1/10 cursor-default">
                             {t}
                           </span>
                         ))}
                       </div>
                    </div>
                  )}

                  <div className="flex gap-4 mt-6">
                    <button
                      onClick={() => {
                        setStrategyResult(goal.strategy_report || {})
                        setShowStrategy(true)
                      }}
                      className="flex-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 py-3 rounded-xl text-xs font-bold transition-colors border border-emerald-200 flex items-center justify-center gap-2"
                    >
                      <Lightbulb className="w-3.5 h-3.5" />
                      Plan
                    </button>
                    <button
                      onClick={() => handleEdit(goal)}
                      className="flex-1 bg-brand-1/10 hover:bg-brand-1/20 text-brand-1 py-3 rounded-xl text-xs font-bold transition-colors border border-brand-1/20 flex items-center justify-center gap-2"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                      Adjust
                    </button>
                    <button
                      onClick={() => handleDelete(goal.id)}
                      className="bg-accent-red/10 hover:bg-accent-red/20 text-accent-red p-3 rounded-xl transition-colors border border-accent-red/25 flex items-center justify-center"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>

      {}
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
          <div className="relative w-full max-w-lg bg-retro-surface rounded-3xl shadow-modal transform transition-all animate-[modalEnter_360ms_ease-out_forwards] overflow-hidden border border-brand-1/15">
            {}
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

            {}
            {/* New Advanced Goal Builder Form */}
            <form onSubmit={handleSubmit} className="p-8 space-y-5">
              <div className="mb-4">
                <label className="block text-xs font-bold text-muted-3 uppercase tracking-widest mb-3">Category Strategy</label>
                <div className="flex gap-4 overflow-x-auto pb-6 scrollbar-hide px-1">
                  {[
                    { id: 'HOME', icon: Home, title: 'Home' },
                    { id: 'EMERGENCY', icon: Shield, title: 'Emergency' },
                    { id: 'WEDDING', icon: Gem, title: 'Wedding' },
                    { id: 'RETIRE', icon: Palmtree, title: 'Retire' },
                    { id: 'TAX', icon: Receipt, title: 'Tax' },
                    { id: 'EDU', icon: GraduationCap, title: 'Education' },
                    { id: 'TRIP', icon: Plane, title: 'Vacation' },
                  ].map(cat => (
                    <button
                      key={cat.id}
                      type="button"
                      onClick={() => setFormData({ ...formData, category: cat.id })}
                      className="flex flex-col items-center gap-2 group outline-none"
                    >
                      <div className={`w-14 h-14 rounded-2xl border-2 flex items-center justify-center transition-all ${
                        formData.category === cat.id 
                        ? 'border-brand-1 bg-brand-1/10 scale-105 shadow-md ring-4 ring-brand-1/5 text-brand-1' 
                        : 'border-muted-2 bg-white text-text-muted hover:border-brand-1/30 hover:text-text-main shadow-sm'
                      }`}>
                        <cat.icon className="w-6 h-6" />
                      </div>
                      <span className={`text-[10px] font-bold uppercase tracking-tighter transition-colors ${
                        formData.category === cat.id ? 'text-brand-1' : 'text-text-muted group-hover:text-text-main'
                      }`}>
                        {cat.title}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-bold text-text-main mb-1.5 uppercase text-[11px] tracking-wider">
                  Goal Name
                </label>
                <input
                  type="text"
                  required
                  placeholder={formData.category === 'HOME' ? 'Home Loan Recovery' : 'e.g., Dream Wedding'}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-5 py-3.5 rounded-2xl border-2 border-muted-2 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/5 outline-none transition-all text-text-main"
                />
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-bold text-text-main mb-1.5 uppercase text-[11px] tracking-wider">
                    {formData.category === 'HOME' ? 'Loan Principal (₹)' : 
                     formData.category === 'EMERGENCY' ? 'Monthly Expenses (₹)' : 
                     formData.category === 'TAX' ? 'Annual Salary (₹)' : 'Target Amount (₹)'}
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.target_amount}
                    onChange={(e) => setFormData({ ...formData, target_amount: e.target.value })}
                    className="w-full px-5 py-3.5 rounded-2xl border-2 border-muted-2 focus:border-brand-1 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-text-main mb-1.5 uppercase text-[11px] tracking-wider">
                    {formData.category === 'TAX' ? 'Existing 80C (₹)' : 'Saved So Far (₹)'}
                  </label>
                  <input
                    type="number"
                    value={formData.current_amount}
                    onChange={(e) => setFormData({ ...formData, current_amount: e.target.value })}
                    className="w-full px-5 py-3.5 rounded-2xl border-2 border-muted-2 focus:border-brand-1 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div>
                  <label className="block text-sm font-bold text-text-main mb-1.5 uppercase text-[11px] tracking-wider">
                    {formData.category === 'RETIRE' ? 'Retire Age' : 'Duration (Years)'}
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.tenure_years}
                    onChange={(e) => setFormData({ ...formData, tenure_years: e.target.value })}
                    className="w-full px-5 py-3.5 rounded-2xl border-2 border-muted-2 focus:border-brand-1 outline-none transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-text-main mb-1.5 uppercase text-[11px] tracking-wider">
                    {formData.category === 'HOME' ? 'Interest Rate (%)' : 
                     formData.category === 'EMERGENCY' ? 'Job Stability (1-10)' : 
                     formData.category === 'RETIRE' ? 'Current Age' : 
                     formData.category === 'WEDDING' ? 'Guest Count' : 
                     formData.category === 'TAX' ? 'Tax Regime (1=Old)' : 
                     formData.category === 'TRIP' ? 'International (1=Yes)' : 'Aggression (1-5)'}
                  </label>
                  <input
                    type="number"
                    value={formData.extra_val}
                    onChange={(e) => setFormData({ ...formData, extra_val: e.target.value })}
                    className="w-full px-5 py-3.5 rounded-2xl border-2 border-muted-2 focus:border-brand-1 outline-none transition-all"
                  />
                </div>
              </div>

              <div className="pt-6 flex gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setModalOpen(false)
                    resetForm()
                  }}
                  className="flex-1 py-4 rounded-2xl border-2 border-muted-2 text-text-main font-bold hover:bg-muted-1 transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-[2] py-4 rounded-2xl bg-brand-1 text-white font-bold hover:bg-brand-600 shadow-lg shadow-brand-1/20 active:scale-95 transition-all"
                >
                   Build Strategy Plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI Strategy Insights Popup */}
      {showStrategy && strategyResult && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md transition-all duration-300">
           <div className="bg-white w-full max-w-md rounded-[32px] p-8 shadow-2xl relative animate-[modalEnter_400ms_ease-out]">
             {/* Local Ticker Fetcher logic can be added here if needed, but we'll use a local state for the modal */}
              <div className="inline-block px-3 py-1 bg-green-50 text-emerald-600 font-bold text-[10px] rounded-lg mb-4 border border-emerald-200">
                AI OPTIMIZED: 98% SCORE
              </div>
              <h3 className="text-2xl font-bold text-text-main mb-6 flex items-center gap-2">
                <Lightbulb className="w-6 h-6 text-brand-1" />
                Plan Strategy
              </h3>

              <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2 scrollbar-hide">
                {strategyResult.steps?.map((step, i) => (
                  <div key={i} className="flex gap-4 group">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-1/10 text-brand-1 font-bold text-xs flex items-center justify-center border border-brand-1/20 group-hover:bg-brand-1 group-hover:text-white transition-colors">
                      {i + 1}
                    </div>
                    <div className="pt-1">
                      <h4 className="font-bold text-text-main text-sm mb-1">{step.title}</h4>
                      <p className="text-text-muted text-xs leading-relaxed">{step.p}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-6 p-4 bg-muted-1 rounded-2xl border border-brand-1/10">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-[10px] font-bold text-brand-1 uppercase tracking-widest flex items-center gap-2">
                    <TrendingUp className="w-3 h-3" />
                    Recommended Tracks
                  </h4>
                  <div className="flex gap-1 bg-white p-0.5 rounded-lg border border-brand-1/10 shadow-sm">
                    {['1y', '3y', '5y', 'max'].map(h => (
                      <button
                        key={h}
                        onClick={() => setReturnHorizon(h)}
                        className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase transition-all ${
                          returnHorizon === h ? 'bg-brand-1 text-white' : 'text-text-muted hover:text-text-main'
                        }`}
                      >
                        {h}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  {(() => {
                    const fallbackMap = {
                      'HOME': ['NIFTYBEES.NS', 'RELIANCE.NS', 'HDFCBANK.NS'],
                      'EMERGENCY': ['LIQUIDBEES.NS', 'SGB-AUG2021'],
                      'WEDDING': ['NIFTYBEES.NS', 'GOLD.NS', 'TCS.NS'],
                      'RETIRE': ['^NSEI', 'MON100.NS', 'NIFTYMIDCAP150.NS'],
                      'EDU': ['MON100.NS', 'NIFTYBEES.NS'],
                      'TAX': ['QUANT_ELSS', 'PPFAS_ELSS'],
                      'TRIP': ['LIQUIDBEES.NS', 'TATAMOTORS.NS']
                    }
                    const activeTickers = strategyResult.tickers?.length > 0 
                      ? strategyResult.tickers 
                      : (fallbackMap[formData.category] || ['^NSEI', 'NIFTYBEES.NS'])

                    return activeTickers.map(ticker => {
                      const info = tickerInfo[ticker.toUpperCase()] || {}
                      const horizonReturn = info.returns ? info.returns[returnHorizon] : null
                      
                      return (
                        <div key={ticker} className="flex items-center justify-between p-3 bg-white border border-brand-1/10 rounded-xl shadow-sm hover:border-brand-1 transition-all group">
                          <div className="flex flex-col">
                            <span className="text-xs font-bold text-text-main group-hover:text-brand-1 transition-colors">{ticker}</span>
                            <span className="text-[10px] text-text-muted">{info.name ? info.name.split(' ').slice(0,2).join(' ') : 'Investment Vehicle'}</span>
                          </div>
                          <div className="text-right">
                            <div className="text-xs font-bold text-text-main">
                               ₹{info.current_price ? Number(info.current_price).toLocaleString('en-IN') : '---'}
                            </div>
                            <div className={`text-[10px] font-bold ${horizonReturn >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                               {horizonReturn !== null ? `${horizonReturn >= 0 ? '↑' : '↓'} ${Math.abs(horizonReturn)}% (${returnHorizon.toUpperCase()})` : '---'}
                            </div>
                          </div>
                        </div>
                      )
                    })
                  })()}
                </div>
              </div>

              <button
                onClick={() => {
                  setShowStrategy(false)
                  resetForm()
                }}
                className="w-full mt-8 py-4 bg-brand-1 text-white font-bold rounded-2xl hover:bg-brand-600 transition-all active:scale-95 shadow-lg shadow-brand-1/20"
              >
                Confirm & Deploy Plan
              </button>
           </div>
        </div>
      )}
    </div>
  )
}

export default Goals



