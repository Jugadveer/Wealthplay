import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, BarChart, Bar, Line, LineChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { ArrowLeft, X, Eye, EyeOff, TrendingUp, TrendingDown, Sparkles } from 'lucide-react'
import api from '../utils/api'

const StockChallenge = () => {
  const navigate = useNavigate()
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [currentStock, setCurrentStock] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [showMA, setShowMA] = useState(true)
  const [prediction, setPrediction] = useState('')
  const [score, setScore] = useState(0)
  const [totalScore, setTotalScore] = useState(0)
  const [currentStreak, setCurrentStreak] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [aiFeedback, setAiFeedback] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)

  useEffect(() => {
    loadRandomQuestion()
    fetchUserStats()
  }, [])

  const fetchUserStats = async () => {
    try {
      const response = await api.getUserChallengeStats()
      if (response.data) {
        setTotalScore(response.data.total_score || 0)
        setCurrentStreak(response.data.current_streak || 0)
      }
    } catch (error) {
      console.error('Error fetching user stats:', error)
    }
  }

  const loadRandomQuestion = async () => {
    setLoading(true)
    setShowFeedback(false)
    setPrediction('')
    try {
      // Try to get a question from the question system
      const questionResponse = await api.getRandomStockQuestion()
      if (questionResponse.data) {
        const question = questionResponse.data
        setCurrentQuestion(question)
        setCurrentStock({
          symbol: question.stock_symbol,
          name: question.stock_name,
          current_price: question.chart_data[question.chart_data.length - 1]?.price || 0,
          change_percent: 0,
        })
        setPriceHistory(question.chart_data || [])
      } else {
        // Fallback to old system
        loadRandomStock()
      }
    } catch (error) {
      console.error('Error loading question, falling back to stocks:', error)
      // Fallback to old system
      loadRandomStock()
    } finally {
      setLoading(false)
    }
  }

  const loadRandomStock = async () => {
    try {
      const response = await api.getStocks()
      const stocks = response.data.stocks || []
      if (stocks.length > 0) {
        // Pick a random stock
        const randomStock = stocks[Math.floor(Math.random() * stocks.length)]
        setCurrentStock(randomStock)
        
        // Load stock detail with chart data
        const detailResponse = await api.getStockDetail(randomStock.symbol)
        if (detailResponse.data && detailResponse.data.price_history) {
          setPriceHistory(detailResponse.data.price_history)
        } else {
          setPriceHistory([])
        }
      }
    } catch (error) {
      console.error('Error loading stock:', error)
    }
  }

  const handleSubmitPrediction = async () => {
    if (!prediction.trim() || !currentStock) {
      alert('Please enter your prediction')
      return
    }

    setSubmitting(true)
    try {
      const response = await api.submitStockPrediction({
        question_id: currentQuestion?.id,
        stock_symbol: currentStock.symbol,
        prediction: prediction,
      })
      
      if (response.data && response.data.success) {
        const feedback = {
          score: response.data.score || 0,
          feedback: response.data.feedback || '',
          is_correct: response.data.is_correct || false,
          ai_analysis: response.data.ai_analysis || '',
          prediction_direction: response.data.prediction_direction || '',
          ai_direction: response.data.ai_direction || '',
        }
        setAiFeedback(feedback)
        setScore(feedback.score)
        setTotalScore(response.data.total_score || 0)
        setCurrentStreak(response.data.current_streak || 0)
        setShowFeedback(true)
      }
    } catch (error) {
      console.error('Error submitting prediction:', error)
      alert('Failed to submit prediction. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNextStock = () => {
    setPrediction('')
    setAiFeedback(null)
    setShowFeedback(false)
    loadRandomQuestion()
  }

  const formatCurrency = (value) => {
    if (!value) return '₹0'
    if (value < 100) return `$${value.toFixed(2)}`
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-1/5 via-white to-brand-2/5">
      {/* Header */}
      <header className="bg-gradient-to-r from-brand-1 to-brand-2 text-white shadow-lg px-6 py-6 lg:px-10">
        <div className="max-w-container mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1">Challenges: Your Learning vs Ours</h1>
            <p className="text-sm text-white/90">Predict stock performance and test your skills</p>
          </div>
          <button
            onClick={() => navigate('/scenario')}
            className="bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            EXIT GAME
          </button>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-container mx-auto px-6 py-6 lg:px-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2">Total Score</p>
            <p className="text-3xl font-bold text-brand-1">{totalScore}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Current Streak
            </p>
            <p className="text-3xl font-bold text-brand-2">{currentStreak}</p>
          </div>
          <div className="bg-white rounded-xl p-6 shadow-card">
            <p className="text-sm text-text-muted mb-2">Selected Stock</p>
            <p className="text-3xl font-bold text-text-main">
              {currentStock?.symbol || 'None'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {currentStock && (
              <div className="bg-white rounded-xl shadow-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-3xl font-bold text-text-main">{currentStock.name}</h2>
                    <p className="text-lg text-text-muted">{currentStock.symbol}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-text-main">
                      {formatCurrency(currentStock.current_price)}
                    </p>
                    <p className={`text-sm font-semibold ${currentStock.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {currentStock.change_percent >= 0 ? '+' : ''}{currentStock.change_percent.toFixed(2)}%
                    </p>
                  </div>
                </div>

                {/* Chart Controls */}
                {priceHistory.length > 0 && (
                  <div className="mb-4 flex items-center justify-between">
                    <h3 className="text-lg font-bold text-text-main">Historical Price Chart</h3>
                    <div className="flex items-center gap-4">
                      {showMA && (
                        <>
                          <div className="flex items-center gap-2 text-sm">
                            <div className="w-4 h-0.5 bg-blue-500 border-dashed border-blue-500"></div>
                            <span className="text-text-muted">MA20</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <div className="w-4 h-0.5 bg-purple-500 border-dashed border-purple-500"></div>
                            <span className="text-text-muted">MA50</span>
                          </div>
                        </>
                      )}
                      <button
                        onClick={() => setShowMA(!showMA)}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted-1 hover:bg-muted-2 text-sm text-text-muted transition-colors"
                      >
                        {showMA ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        {showMA ? 'HIDE MA' : 'SHOW MA'}
                      </button>
                    </div>
                  </div>
                )}

                {/* Price Chart */}
                {priceHistory.length > 0 && (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={priceHistory}>
                      <defs>
                        <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="date"
                        stroke="#6b7280"
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => {
                          const date = new Date(value)
                          return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                        }}
                      />
                      <YAxis
                        stroke="#6b7280"
                        style={{ fontSize: '12px' }}
                        tickFormatter={(value) => {
                          if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`
                          if (value >= 100) return `₹${value.toFixed(0)}`
                          return `$${value.toFixed(0)}`
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px',
                        }}
                        formatter={(value) => {
                          if (value >= 100) return formatCurrency(value)
                          return `$${value.toFixed(2)}`
                        }}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke="#10b981"
                        strokeWidth={2}
                        fill="url(#colorPrice)"
                        dot={false}
                      />
                      {showMA && (
                        <>
                          <Line
                            type="monotone"
                            dataKey="ma20"
                            stroke="#3b82f6"
                            strokeWidth={1.5}
                            strokeDasharray="5 5"
                            dot={false}
                            strokeOpacity={0.8}
                          />
                          <Line
                            type="monotone"
                            dataKey="ma50"
                            stroke="#a855f7"
                            strokeWidth={1.5}
                            strokeDasharray="5 5"
                            dot={false}
                            strokeOpacity={0.8}
                          />
                        </>
                      )}
                    </AreaChart>
                  </ResponsiveContainer>
                )}

                {/* Volume Chart */}
                {priceHistory.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold text-text-muted mb-2">Volume</h4>
                    <ResponsiveContainer width="100%" height={150}>
                      <BarChart data={priceHistory}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                        <XAxis
                          dataKey="date"
                          stroke="#6b7280"
                          style={{ fontSize: '11px' }}
                          tickFormatter={(value) => {
                            const date = new Date(value)
                            return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                          }}
                        />
                        <YAxis
                          stroke="#6b7280"
                          style={{ fontSize: '11px' }}
                          tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
                          width={50}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#fff',
                            border: '1px solid #e5e7eb',
                            borderRadius: '8px',
                          }}
                          formatter={(value) => `Vol: ${(value / 1000000).toFixed(2)}M`}
                        />
                        <Bar 
                          dataKey="volume" 
                          fill="#10b981" 
                          opacity={0.7}
                          radius={[2, 2, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Prediction Input */}
                {!showFeedback && (
                  <div className="mt-8 p-6 bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl border-2 border-brand-1/20">
                    <h3 className="text-xl font-bold text-text-main mb-4">Make Your Prediction</h3>
                    <p className="text-sm text-text-muted mb-4">
                      {currentQuestion?.question || 'Based on the chart above, how do you think this stock will perform?'}
                    </p>
                    <textarea
                      value={prediction}
                      onChange={(e) => setPrediction(e.target.value)}
                      placeholder="Enter your prediction (e.g., 'Will go up 5% next week')"
                      className="w-full px-4 py-3 rounded-lg border border-muted-2 focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none mb-4 min-h-[100px] resize-none"
                    />
                    <button
                      onClick={handleSubmitPrediction}
                      disabled={submitting || !prediction.trim()}
                      className="w-full px-6 py-4 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      {submitting ? (
                        <>
                          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          Submitting...
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-5 h-5" />
                          SUBMIT PREDICTION
                        </>
                      )}
                    </button>
                  </div>
                )}

                {/* AI Feedback */}
                {showFeedback && aiFeedback && (
                  <div className={`mt-8 p-6 rounded-xl border-2 ${
                    aiFeedback.is_correct 
                      ? 'bg-gradient-to-br from-green-50 to-blue-50 border-green-200' 
                      : 'bg-gradient-to-br from-red-50 to-orange-50 border-red-200'
                  }`}>
                    <div className="flex items-center gap-3 mb-4">
                      <Sparkles className={`w-6 h-6 ${aiFeedback.is_correct ? 'text-green-600' : 'text-red-600'}`} />
                      <h3 className="text-xl font-bold text-text-main">AI Judge Feedback</h3>
                    </div>
                    <div className="mb-4 p-4 bg-white rounded-lg">
                      <p className="text-sm text-text-muted mb-2">Your Prediction:</p>
                      <p className="text-text-main font-semibold">{prediction}</p>
                    </div>
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-text-main">Score:</span>
                        <span className={`text-2xl font-bold ${aiFeedback.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                          {aiFeedback.score > 0 ? '+' : ''}{aiFeedback.score}
                        </span>
                      </div>
                      <p className={`text-sm mb-3 ${aiFeedback.is_correct ? 'text-green-700' : 'text-red-700'}`}>
                        {aiFeedback.feedback}
                      </p>
                      {aiFeedback.ai_analysis && (
                        <div className={`p-3 bg-white rounded-lg border-l-4 ${
                          aiFeedback.is_correct ? 'border-green-500' : 'border-red-500'
                        }`}>
                          <p className="text-sm text-text-main">
                            <strong>AI Analysis:</strong> {aiFeedback.ai_analysis}
                          </p>
                          {!aiFeedback.is_correct && (
                            <p className="text-sm text-red-600 mt-2 font-semibold">
                              Your prediction was incorrect. The AI analysis indicates a {aiFeedback.ai_direction} trend, 
                              which {aiFeedback.prediction_direction === 'down' ? 'contradicts' : 'does not match'} your prediction of {aiFeedback.prediction_direction === 'down' ? 'downward' : 'upward'} movement.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={handleNextStock}
                      className="w-full px-6 py-4 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-bold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-1 active:scale-95 transition-all duration-180 flex items-center justify-center gap-2"
                    >
                      Next Stock
                      <TrendingUp className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Sidebar - Leaderboard placeholder */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-card p-6 sticky top-20">
              <h3 className="text-xl font-bold text-text-main mb-4 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-brand-2" />
                Quick Stats
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-muted-1 rounded-lg">
                  <p className="text-sm text-text-muted mb-1">Last Score</p>
                  <p className="text-2xl font-bold text-brand-1">{score}</p>
                </div>
                <div className="p-4 bg-muted-1 rounded-lg">
                  <p className="text-sm text-text-muted mb-1">Current Streak</p>
                  <p className="text-2xl font-bold text-brand-2">{currentStreak}</p>
                </div>
                <div className="p-4 bg-muted-1 rounded-lg">
                  <p className="text-sm text-text-muted mb-1">Total Score</p>
                  <p className="text-2xl font-bold text-text-main">{totalScore}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StockChallenge

