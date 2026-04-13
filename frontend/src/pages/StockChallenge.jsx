import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AreaChart, Area, BarChart, Bar, Line, LineChart, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { ArrowLeft, X, Eye, EyeOff, TrendingUp, TrendingDown, Sparkles, Loader2 } from 'lucide-react'
import api from '../utils/api'

const AI_TERMS = [
  'Relative Strength Index',
  'RSI',
  'Resistance',
  'Support',
  'Moving Average',
  'MACD',
  'Volume',
  'Trend',
  'Momentum',
  'Breakout',
]

const highlightAiTerms = (text) => {
  if (!text) return text
  return text.split(/(\s+)/).map((part, idx) => {
    const normalized = part.replace(/[^a-zA-Z]/g, '').toLowerCase()
    const shouldHighlight = AI_TERMS.some((term) =>
      term.toLowerCase().split(' ').some((token) => token === normalized)
    )
    if (!shouldHighlight) {
      return <span key={`term-${idx}`}>{part}</span>
    }
    return (
      <strong key={`hl-${idx}`} className="text-text-main font-semibold">
        {part}
      </strong>
    )
  })
}

const StockChallenge = () => {
  const navigate = useNavigate()
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [currentStock, setCurrentStock] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [showMA, setShowMA] = useState(true)
  const [predictionDirection, setPredictionDirection] = useState('')
  const [predictionReason, setPredictionReason] = useState('')
  const [score, setScore] = useState(0)
  const [totalScore, setTotalScore] = useState(0)
  const [currentStreak, setCurrentStreak] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [aiFeedback, setAiFeedback] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [xpFloatText, setXpFloatText] = useState('')
  const [showConfetti, setShowConfetti] = useState(false)

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
    setPredictionDirection('')
    setPredictionReason('')
    try {
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
        loadRandomStock()
      }
    } catch (error) {
      console.error('Error loading question, falling back to stocks:', error)
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
        const randomStock = stocks[Math.floor(Math.random() * stocks.length)]
        setCurrentStock(randomStock)
        
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
    if (!predictionDirection || !currentStock) {
      alert('Please choose bullish or bearish')
      return
    }

    setSubmitting(true)
    try {
      const predictionText = predictionReason.trim()
        ? `${predictionDirection}. Reason: ${predictionReason.trim()}`
        : predictionDirection

      const response = await api.submitStockPrediction({
        question_id: currentQuestion?.id,
        stock_symbol: currentStock.symbol,
        prediction: predictionText,
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
        if (feedback.is_correct && feedback.score > 0) {
          setXpFloatText(`+${feedback.score} XP`)
          setShowConfetti(true)
          setTimeout(() => setXpFloatText(''), 1200)
          setTimeout(() => setShowConfetti(false), 900)
        }
      }
    } catch (error) {
      console.error('Error submitting prediction:', error)
      alert('Failed to submit prediction. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNextStock = () => {
    setPredictionDirection('')
    setPredictionReason('')
    setAiFeedback(null)
    setShowFeedback(false)
    loadRandomQuestion()
  }

  const formatCurrency = (value) => {
    if (!value) return '₹0'
    if (value < 100) return `$${value.toFixed(2)}`
    return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  return (
    <div className="min-h-screen bg-retro-bg text-text-main">
      {}
      <header className="bg-retro-surface border-b border-brand-1/20 text-text-main px-6 py-6 lg:px-10">
        <div className="max-w-container mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-1 text-text-main">Challenges: Your Learning vs Ours</h1>
            <p className="text-sm text-text-muted">Predict stock performance and test your skills</p>
          </div>
          <button
            onClick={() => navigate('/scenario')}
            className="bg-brand-1/10 hover:bg-brand-1/20 border border-brand-1/20 text-brand-1 px-5 py-2.5 rounded-full text-sm font-semibold shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            EXIT GAME
          </button>
        </div>
      </header>

      {}
      <div className="max-w-container mx-auto px-6 py-6 lg:px-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-retro-surface/80 rounded-xl p-6 shadow-card border border-brand-1/20">
            <p className="text-sm text-text-muted mb-2">Total Score</p>
            <p className="text-3xl font-bold text-brand-1">{totalScore}</p>
          </div>
          <div className="bg-retro-surface/80 rounded-xl p-6 shadow-card border border-brand-1/20">
            <p className="text-sm text-text-muted mb-2 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Current Streak
            </p>
            <p className="text-3xl font-bold text-accent-green">{currentStreak}</p>
          </div>
          <div className="bg-retro-surface/80 rounded-xl p-6 shadow-card border border-brand-1/20">
            <p className="text-sm text-text-muted mb-2">Selected Stock</p>
            <p className="text-3xl font-bold text-text-main">
              {currentStock?.symbol || 'Loading...'}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {}
          <div className="lg:col-span-2 space-y-6">
            {}
            <div className="relative bg-retro-surface/80 rounded-xl shadow-card p-6 border border-brand-1/20 overflow-hidden">
              {loading ? (
                
                <div className="flex flex-col items-center justify-center py-16">
                  <Loader2 className="w-12 h-12 text-brand-1 animate-spin mb-4" />
                  <p className="text-text-muted font-semibold">Loading stock data...</p>
                  <p className="text-sm text-text-muted mt-1">Preparing chart and analysis</p>
                </div>
              ) : currentStock ? (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-3xl font-bold text-text-main">{currentStock.name}</h2>
                      <p className="text-lg text-text-muted">{currentStock.symbol}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-3xl font-bold text-text-main">
                        {formatCurrency(currentStock.current_price)}
                      </p>
                      <p className={`text-sm font-semibold ${currentStock.change_percent >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                        {currentStock.change_percent >= 0 ? '+' : ''}{currentStock.change_percent.toFixed(2)}%
                      </p>
                    </div>
                  </div>

                  {}
                  {priceHistory.length > 0 && (
                    <div className="mb-4 flex items-center justify-between">
                      <h3 className="text-lg font-bold text-text-main">Historical Price Chart</h3>
                      <div className="flex items-center gap-4">
                        {showMA && (
                          <>
                            <div className="flex items-center gap-2 text-sm">
                              <div className="w-4 h-0.5 bg-brand-1 border-dashed border-brand-1"></div>
                              <span className="text-text-muted">MA20</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                              <div className="w-4 h-0.5 bg-brand-2 border-dashed border-brand-2"></div>
                              <span className="text-text-muted">MA50</span>
                            </div>
                          </>
                        )}
                        <button
                          onClick={() => setShowMA(!showMA)}
                          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-retro-surface hover:bg-brand-1/5 text-sm text-text-main transition-colors border border-brand-1/20"
                        >
                          {showMA ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          {showMA ? 'HIDE MA' : 'SHOW MA'}
                        </button>
                      </div>
                    </div>
                  )}

                  {}
                  {priceHistory.length > 0 ? (
                    <ResponsiveContainer width="100%" height={300}>
                      <AreaChart data={priceHistory}>
                        <defs>
                          <linearGradient id="colorPriceSC" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#0F172A" stopOpacity={0.1}/>
                            <stop offset="95%" stopColor="#0F172A" stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,107,53,0.12)" />
                        <XAxis
                          dataKey="date"
                          stroke="#ff6b35"
                          style={{ fontSize: '12px' }}
                          tickFormatter={(value) => {
                            const date = new Date(value)
                            return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                          }}
                        />
                        <YAxis
                          stroke="#ff6b35"
                          style={{ fontSize: '12px' }}
                          tickFormatter={(value) => {
                            if (value >= 1000) return `₹${(value / 1000).toFixed(0)}k`
                            if (value >= 100) return `₹${value.toFixed(0)}`
                            return `$${value.toFixed(0)}`
                          }}
                        />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#fafbf9',
                            border: '1px solid rgba(255,107,53,0.3)',
                            borderRadius: '8px',
                            color: '#9a3412',
                          }}
                          labelStyle={{ color: '#ff6b35' }}
                          formatter={(value) => {
                            if (value >= 100) return formatCurrency(value)
                            return `$${value.toFixed(2)}`
                          }}
                        />
                        <Area
                          type="monotone"
                          dataKey="price"
                          stroke="#0F172A"
                          strokeWidth={2}
                          fill="url(#colorPriceSC)"
                          dot={false}
                        />
                        {showMA && (
                          <>
                            <Line
                              type="monotone"
                              dataKey="ma20"
                              stroke="#ff6b35"
                              strokeWidth={1.5}
                              strokeDasharray="5 5"
                              dot={false}
                              strokeOpacity={0.8}
                            />
                            <Line
                              type="monotone"
                              dataKey="ma50"
                              stroke="#c084fc"
                              strokeWidth={1.5}
                              strokeDasharray="5 5"
                              dot={false}
                              strokeOpacity={0.8}
                            />
                          </>
                        )}
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 text-brand-1 animate-spin mb-3" />
                      <p className="text-text-muted">Loading chart data...</p>
                    </div>
                  )}

                  {}
                  {priceHistory.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-semibold text-text-muted mb-2">Volume</h4>
                      <ResponsiveContainer width="100%" height={150}>
                        <BarChart data={priceHistory}>
                          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,107,53,0.12)" vertical={false} />
                          <XAxis
                            dataKey="date"
                            stroke="#ff6b35"
                            style={{ fontSize: '11px' }}
                            tickFormatter={(value) => {
                              const date = new Date(value)
                              return date.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })
                            }}
                          />
                          <YAxis
                            stroke="#ff6b35"
                            style={{ fontSize: '11px' }}
                            tickFormatter={(value) => `${(value / 1000000).toFixed(0)}M`}
                            width={50}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#fafbf9',
                              border: '1px solid rgba(255,107,53,0.3)',
                              borderRadius: '8px',
                              color: '#9a3412',
                            }}
                            labelStyle={{ color: '#ff6b35' }}
                            formatter={(value) => `Vol: ${(value / 1000000).toFixed(2)}M`}
                          />
                          <Bar 
                            dataKey="volume" 
                            fill="#ff6b35" 
                            opacity={0.7}
                            radius={[2, 2, 0, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}

                  {}
                  {!showFeedback && (
                    <div className="mt-8 p-6 bg-retro-surface rounded-2xl shadow-sm border border-brand-1/15">
                      <h3 className="text-xl font-bold text-text-main mb-4">Make Your Prediction</h3>
                      <p className="text-sm text-text-muted mb-4">
                        {currentQuestion?.question || 'Based on the chart above, how do you think this stock will perform?'}
                      </p>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                        <button
                          onClick={() => setPredictionDirection('bullish')}
                          className={`px-5 py-4 rounded-xl font-bold text-base transition-all border ${predictionDirection === 'bullish' ? 'bg-accent-green border-accent-green text-white shadow-sm' : 'bg-retro-surface border-brand-1/15 hover:border-accent-green text-text-main'}`}
                        >
                          ⬆ Bullish
                        </button>
                        <button
                          onClick={() => setPredictionDirection('bearish')}
                          className={`px-5 py-4 rounded-xl font-bold text-base transition-all border ${predictionDirection === 'bearish' ? 'bg-accent-red border-accent-red text-white shadow-sm' : 'bg-retro-surface border-brand-1/15 hover:border-accent-red text-text-main'}`}
                        >
                          ⬇ Bearish
                        </button>
                      </div>

                      <details className="mb-4 rounded-xl border border-brand-1/15 bg-retro-bg p-3">
                        <summary className="cursor-pointer text-sm font-semibold text-text-main">Optional: Explain why</summary>
                        <textarea
                          value={predictionReason}
                          onChange={(e) => setPredictionReason(e.target.value)}
                          placeholder="Example: RSI is recovering from oversold and price is approaching support."
                          className="w-full mt-3 px-4 py-3 rounded-lg border border-brand-1/15 bg-retro-surface text-text-main placeholder-text-text-muted/60 focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none min-h-[90px] resize-none"
                        />
                      </details>

                      <button
                        onClick={handleSubmitPrediction}
                        disabled={submitting || !predictionDirection}
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

                  {}
                  {showFeedback && aiFeedback && (
                    <div className="mt-8 p-6 rounded-xl border border-brand-2/30 bg-brand-2/10 border-l-4 border-l-brand-2">
                      <div className="flex items-center gap-3 mb-4">
                        <Sparkles className="w-6 h-6 text-brand-2" />
                        <h3 className="text-xl font-bold text-text-main">AI Judge Feedback</h3>
                      </div>
                      <div className="mb-4 p-4 bg-muted-2/40 rounded-lg">
                        <p className="text-sm text-text-muted mb-2">Your Prediction:</p>
                        <p className="text-text-main font-semibold capitalize">
                          {predictionDirection}
                          {predictionReason ? ` - ${predictionReason}` : ''}
                        </p>
                      </div>
                      <div className="mb-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-semibold text-text-main">Score:</span>
                          <span className={`text-2xl font-bold ${aiFeedback.is_correct ? 'text-accent-green' : 'text-accent-red'}`}>
                            {aiFeedback.score > 0 ? '+' : ''}{aiFeedback.score}
                          </span>
                        </div>
                        <p className={`text-sm mb-3 ${aiFeedback.is_correct ? 'text-accent-green' : 'text-accent-red'}`}>
                          {aiFeedback.feedback}
                        </p>
                        {aiFeedback.ai_analysis && (
                          <div className={`p-3 bg-muted-2/40 rounded-lg border-l-4 ${
                            aiFeedback.is_correct ? 'border-accent-green' : 'border-accent-red'
                          }`}>
                            <p className="text-sm text-text-main">
                              <strong>AI Analysis:</strong> {highlightAiTerms(aiFeedback.ai_analysis)}
                            </p>
                            {!aiFeedback.is_correct && (
                              <p className="text-sm text-accent-red mt-2 font-semibold">
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

                  {xpFloatText && (
                    <div className="pointer-events-none absolute right-10 top-8 xp-float text-brand-2 text-xl font-extrabold number-tabular">
                      {xpFloatText}
                    </div>
                  )}

                  {showConfetti && (
                    <div className="pointer-events-none absolute inset-0 overflow-hidden">
                      {[...Array(10)].map((_, idx) => (
                        <span
                          key={`conf-${idx}`}
                          className="confetti-piece absolute w-2 h-3 rounded-sm"
                          style={{
                            left: `${8 + idx * 9}%`,
                            top: '8%',
                            backgroundColor: idx % 2 === 0 ? '#00f5a0' : '#00d1ff',
                            animationDelay: `${idx * 40}ms`,
                          }}
                        />
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-16">
                  <Loader2 className="w-12 h-12 text-brand-1 animate-spin mb-4" />
                  <p className="text-text-muted font-semibold">Loading stock data...</p>
                </div>
              )}
            </div>
          </div>

          {}
          <div className="lg:col-span-1">
            <div className="bg-retro-surface/80 rounded-xl shadow-card p-6 sticky top-20 border border-brand-1/20">
              <h3 className="text-xl font-bold text-text-main mb-4 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-brand-1" />
                Quick Stats
              </h3>
              <div className="space-y-4">
                <div className="p-4 bg-retro-surface rounded-lg border border-brand-1/20">
                  <p className="text-sm text-text-muted mb-1">Last Score</p>
                  <p className="text-2xl font-bold text-brand-1">{score}</p>
                </div>
                <div className="p-4 bg-retro-surface rounded-lg border border-brand-1/20">
                  <p className="text-sm text-text-muted mb-1">Current Streak</p>
                  <p className="text-2xl font-bold text-accent-green">{currentStreak}</p>
                </div>
                <div className="p-4 bg-retro-surface rounded-lg border border-brand-1/20">
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
