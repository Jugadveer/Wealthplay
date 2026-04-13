import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend 
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Search,
  Sparkles,
  AlertCircle,
  Eye,
  EyeOff,
  Loader2,
} from 'lucide-react'
import api from '../../utils/api'
import { useAchievements } from '../../contexts/AchievementContext'

const PortfolioTrade = ({ portfolio, onRefresh, stocksCache = [], refreshStocksCache }) => {
  const { checkAchievements } = useAchievements()
  const [searchParams] = useSearchParams()
  const [stocks, setStocks] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [aiRecommendation, setAiRecommendation] = useState(null)
  const [tradeType, setTradeType] = useState('buy')
  const [quantity, setQuantity] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [stocksLoading, setStocksLoading] = useState(true)
  const [trading, setTrading] = useState(false)
  const [message, setMessage] = useState(null)
  const [showMA, setShowMA] = useState(true)
  const [showAiHint, setShowAiHint] = useState(false)
  const [showTradeCelebration, setShowTradeCelebration] = useState(false)
  const [tradeXpText, setTradeXpText] = useState('')

  useEffect(() => {
    if (stocksCache.length > 0) {
      setStocks(stocksCache)
      setStocksLoading(false)
    } else {
      fetchStocks()
    }

    const symbolParam = searchParams.get('symbol')
    if (symbolParam) {
      handleStockSelect(symbolParam)
    }
  }, [searchParams])

  useEffect(() => {
    if (stocksCache.length > 0) {
      setStocks(stocksCache)
      setStocksLoading(false)
    }
  }, [stocksCache])

  const fetchStocks = async () => {
    setStocksLoading(true)
    try {
      let stocksData = []
      if (typeof refreshStocksCache === 'function') {
        stocksData = await refreshStocksCache()
      }

      if (!Array.isArray(stocksData) || stocksData.length === 0) {
        const response = await api.getStocks()
        stocksData = response.data.stocks || []
      }

      setStocks(stocksData)
    } catch (error) {
      console.error('Error fetching stocks:', error)
    } finally {
      setStocksLoading(false)
    }
  }

  const handleStockSelect = async (symbol) => {
    setLoading(true)
    setShowAiHint(false)
    try {
      const response = await api.getStockDetail(symbol)
      if (response.data) {
        setSelectedStock(response.data)
        setPriceHistory(response.data.price_history || [])
        
        if (!response.data.is_custom) {
          try {
            const aiResponse = await api.getAIRecommendation({ symbol, action: 'analyze' })
            setAiRecommendation(aiResponse.data)
          } catch (aiError) {
            console.error('Error fetching AI recommendation:', aiError)
            setAiRecommendation(null)
          }
        } else {
          setAiRecommendation({
            recommendation: 'Hold',
            confidence: 0.5,
            message: 'This is a custom stock for practice trading.',
          })
        }
      }
    } catch (error) {
      console.error('Error fetching stock detail:', error)
      alert(`Error loading stock: ${error.message || 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleTrade = async () => {
    if (!selectedStock || !quantity || parseInt(quantity) <= 0) {
      setMessage({ type: 'error', text: 'Please enter a valid quantity' })
      return
    }

    setTrading(true)
    setMessage(null)

    try {
      const response = await api.tradeAsset({ 
        symbol: selectedStock.symbol, 
        action: tradeType === 'buy' ? 'BUY' : 'SELL',
        quantity: parseInt(quantity) 
      })

      
      setMessage({ type: 'success', text: response.data?.msg || response.data?.message || 'Trade successful!' })
      setQuantity('')
      await checkAchievements()

      
      if (typeof onRefresh === 'function') {
        await onRefresh()
      }

      
      window.dispatchEvent(new CustomEvent('portfolio-updated'))

      
      if (typeof refreshStocksCache === 'function') {
        await refreshStocksCache(true)
      }

      
      await handleStockSelect(selectedStock.symbol)

      if (tradeType === 'buy') {
        setShowTradeCelebration(true)
        setTradeXpText('+10 XP')
        setTimeout(() => setShowTradeCelebration(false), 900)
        setTimeout(() => setTradeXpText(''), 1200)
      }
    } catch (error) {
      setMessage({
        type: 'error',
        text: error.response?.data?.error || 'Trade failed. Please try again.',
      })
    } finally {
      setTrading(false)
    }
  }

  const USD_TO_INR = 85 

  const formatCurrency = (value, currency = 'INR') => {
    if (currency === 'USD') {
      const usd = `$${value?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      const inr = `₹${(value * USD_TO_INR)?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
      return `${usd} (${inr})`
    }
    return `₹${value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value?.toFixed(2)}%`
  }

  const calculateTotal = () => {
    if (!selectedStock || !quantity) return 0
    return parseFloat(selectedStock.current_price) * parseInt(quantity)
  }

  const calculateTotalINR = () => {
    const total = calculateTotal()
    const currency = selectedStock?.currency || 'INR'
    return currency === 'USD' ? total * USD_TO_INR : total
  }

  const unitPriceINR = selectedStock
    ? ((selectedStock.currency || 'INR') === 'USD'
      ? (selectedStock.current_price || 0) * USD_TO_INR
      : (selectedStock.current_price || 0))
    : 1

  const maxQuantity = tradeType === 'buy'
    ? Math.floor((portfolio?.balance || 50000) / (unitPriceINR || 1))
    : (selectedStock?.holding?.quantity || 0)

  const filteredStocks = stocks.filter(
    (stock) =>
      stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  
  const StockSkeleton = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="animate-pulse flex flex-col p-5 rounded-xl border border-brand-1/10 bg-retro-surface/90">
          <div className="flex items-center justify-between mb-3 w-full">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-retro-board/80"></div>
              <div className="h-4 w-16 bg-retro-board/80 rounded"></div>
            </div>
            <div className="h-5 w-14 bg-retro-board/80 rounded"></div>
          </div>
          <div className="mt-auto pt-2 w-full">
            <div className="h-3 w-24 bg-retro-board/80 rounded mb-2"></div>
            <div className="h-6 w-20 bg-retro-board/80 rounded"></div>
          </div>
        </div>
      ))}
    </div>
  )

  return (
    <div className="space-y-6">
      {!selectedStock ? (
        <>
          {}
          <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
            <h2 className="text-xl font-bold text-text-main mb-6">Explore Assets</h2>
            <div className="mb-8 relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
              <input
                type="text"
                placeholder="Search for companies or symbols..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-4 bg-retro-surface rounded-xl border border-brand-1/10 focus:ring-2 focus:ring-brand-1/20 focus:border-brand-1 transition-all text-text-main placeholder-text-muted/50 outline-none"
              />
            </div>

            {stocksLoading ? (
              <StockSkeleton />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredStocks.map((stock) => (
                  <div
                    key={stock.symbol}
                    className="relative flex flex-col text-left p-5 rounded-xl border border-brand-1/10 hover:border-brand-1/40 hover:shadow-md transition-all bg-retro-surface/90 hover:bg-retro-surface group"
                  >
                    <button
                      onClick={() => handleStockSelect(stock.symbol)}
                      className="flex flex-col text-left w-full"
                    >
                    <div className="flex items-center justify-between mb-3 w-full">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-brand-1/10 flex items-center justify-center text-brand-1 font-bold group-hover:bg-brand-1/15 transition-colors">
                           {stock.symbol.slice(0, 2)}
                        </div>
                        <div>
                          <p className="font-bold text-text-main">{stock.symbol}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${stock.change_percent >= 0 ? 'bg-accent-green/15 text-accent-green' : 'bg-accent-red/15 text-accent-red'}`}>
                        {formatPercent(stock.change_percent)}
                      </span>
                    </div>
                    <div className="mt-auto pt-2 w-full">
                       <p className="text-xs text-text-muted truncate mb-1">{stock.name}</p>
                       <p className="text-lg font-bold text-text-main">{formatCurrency(stock.current_price, stock.currency || 'INR')}</p>
                    </div>
                    </button>
                  </div>
                ))}
              </div>
            )}

            {!stocksLoading && filteredStocks.length === 0 && (
              <div className="py-12 text-center">
                <div className="w-16 h-16 rounded-full bg-retro-board/80 flex items-center justify-center mx-auto mb-4">
                  <Search className="w-8 h-8 text-text-muted opacity-50" />
                </div>
                <h3 className="text-lg font-bold text-text-main mb-1">No assets found</h3>
                <p className="text-text-muted">Try a different search term or browse categories</p>
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          <button 
             onClick={() => {
                setSelectedStock(null);
                setTrading(false);
                setMessage(null);
                setQuantity('');
             }}
             className="flex items-center gap-2 text-text-muted hover:text-text-main font-medium transition-colors mb-2"
          >
             <span className="text-lg leading-none">←</span> Back to Explore
          </button>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {}
            <div className="lg:col-span-2 space-y-6">
              {}
              <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-xl shadow-sm border border-brand-1/20 flex items-center justify-center bg-brand-1/10 text-brand-1">
                      <span className="font-black text-xl">{selectedStock.symbol.slice(0, 2)}</span>
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-text-main">{selectedStock.symbol}</h2>
                      <p className="text-sm font-medium text-text-muted">{selectedStock.name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-3xl font-bold text-text-main tracking-tight">
                      {formatCurrency(selectedStock.current_price, selectedStock.currency || 'INR')}
                    </p>
                    <p className={`text-sm font-bold flex items-center justify-end gap-1 ${selectedStock.change_percent >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {selectedStock.change_percent >= 0 ? <TrendingUp className="w-4 h-4"/> : <TrendingDown className="w-4 h-4"/>}
                      {formatPercent(selectedStock.change_percent)}
                    </p>
                  </div>
                </div>

                {}
                {priceHistory.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={priceHistory}>
                      <defs>
                        <linearGradient id="colorPricePT" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={selectedStock.change_percent >= 0 ? "#ff6b35" : "#d94c4c"} stopOpacity={0.3}/>
                          <stop offset="95%" stopColor={selectedStock.change_percent >= 0 ? "#ff6b35" : "#d94c4c"} stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" hide={true} />
                      <YAxis hide={true} domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fafbf9',
                          border: '1px solid rgba(255,107,53,0.3)',
                          borderRadius: '8px',
                          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
                          color: '#9a3412',
                        }}
                        labelStyle={{ color: '#ff6b35' }}
                        formatter={(value, name) => {
                          if (name === 'volume') return `${(value / 1000000).toFixed(2)}M`
                          const currency = selectedStock?.currency || 'INR'
                          return formatCurrency(value, currency)
                        }}
                        labelFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { 
                          month: 'short', 
                          day: 'numeric', 
                          year: 'numeric' 
                        })}
                      />
                      <Area
                        type="monotone"
                        dataKey="price"
                        stroke={selectedStock.change_percent >= 0 ? "#ff6b35" : "#d94c4c"}
                        strokeWidth={2}
                        fill="url(#colorPricePT)"
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 text-brand-1 animate-spin mb-3" />
                    <p className="text-text-muted">Loading chart data...</p>
                  </div>
                )}

                {}
                {selectedStock.summary && (
                  <div className="mt-8 pt-6 border-t border-brand-1/10 flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-text-muted mb-1">52W High</p>
                      <p className="text-sm font-bold text-text-main">
                        {formatCurrency(selectedStock.summary.high, selectedStock.currency || 'INR')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-text-muted mb-1">Average</p>
                      <p className="text-sm font-bold text-text-main">
                        {formatCurrency(selectedStock.summary.average, selectedStock.currency || 'INR')}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-text-muted mb-1">52W Low</p>
                      <p className="text-sm font-bold text-text-main">
                        {formatCurrency(selectedStock.summary.low, selectedStock.currency || 'INR')}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {}
              {aiRecommendation && (
                <div className="mt-6">
                  {!showAiHint ? (
                    <button 
                      onClick={() => setShowAiHint(true)}
                      className="w-full py-4 bg-brand-2/10 hover:bg-brand-2/15 text-brand-2 rounded-xl font-bold flex items-center justify-center gap-2 transition-all border border-brand-2/20 shadow-sm"
                    >
                      <Sparkles className="w-5 h-5 text-brand-2" />
                      Show AI Analysis Hint
                    </button>
                  ) : (
                    <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-2/20 p-6 relative overflow-hidden animate-fade-in">
                      <div className="absolute top-0 left-0 w-1 h-full bg-brand-2"></div>
                      <div className="flex justify-between items-start mb-4">
                         <h3 className="font-bold text-text-main flex items-center gap-2 text-lg">
                            <Sparkles className="w-5 h-5 text-brand-2" /> AI Insights
                         </h3>
                         <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                            aiRecommendation.recommendation === 'buy' ? 'bg-accent-green/15 text-accent-green' :
                            aiRecommendation.recommendation === 'sell' ? 'bg-accent-red/15 text-accent-red' :
                             'bg-brand-2/15 text-brand-2'
                         }`}>
                            {aiRecommendation.recommendation} • {Math.round(aiRecommendation.confidence * 100)}%
                         </div>
                      </div>
                      <p className="text-sm text-text-muted mb-3 font-medium leading-relaxed">{aiRecommendation.message}</p>
                      {aiRecommendation.reasons && (
                        <ul className="space-y-2 mt-4 pt-4 border-t border-brand-1/10">
                          {aiRecommendation.reasons.map((reason, idx) => (
                            <li key={idx} className="text-sm text-text-muted flex items-start gap-2">
                              <span className="text-brand-2 font-bold mt-0.5">•</span>
                              <span>{reason}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {}
            <div className="lg:col-span-1">
              <div className="relative bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6 sticky top-24 overflow-hidden">
                <div className="flex bg-retro-board/70 rounded-lg p-1 mb-6">
                  <button
                    onClick={() => {
                      setTradeType('buy')
                      setQuantity('')
                      setMessage(null)
                    }}
                    className={`flex-1 py-3 text-sm rounded-md font-bold transition-all ${
                      tradeType === 'buy'
                        ? 'bg-accent-green/20 text-accent-green shadow-sm'
                        : 'text-text-muted hover:text-text-main'
                    }`}
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => {
                      setTradeType('sell')
                      setQuantity('')
                      setMessage(null)
                    }}
                    className={`flex-1 py-3 text-sm rounded-md font-bold transition-all ${
                      tradeType === 'sell'
                        ? 'bg-accent-red/20 text-accent-red shadow-sm'
                        : 'text-text-muted hover:text-text-main'
                    }`}
                  >
                    Sell
                  </button>
                </div>

                <div className="space-y-5">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                       <label className="text-sm font-semibold text-text-muted">Qty (Shares)</label>
                    </div>
                    <input
                      type="number"
                      min="1"
                      max={maxQuantity}
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      placeholder="0"
                      className="w-full px-4 py-4 rounded-xl border border-brand-1/20 bg-retro-surface focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none text-xl font-bold text-text-main transition-all placeholder-text-muted/50"
                    />
                  </div>

                  <div className="pt-4 space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Market Price</span>
                      <span className="font-semibold text-text-main">
                        {formatCurrency(selectedStock.current_price, selectedStock.currency || 'INR')}
                      </span>
                    </div>
                    <div className="flex justify-between border-t border-brand-1/10 pt-3 mt-3">
                      <span className="text-text-main font-bold">Estimated Cost</span>
                      <span className="text-lg font-bold text-brand-1">{formatCurrency(calculateTotal(), selectedStock.currency || 'INR')}</span>
                    </div>
                  </div>

                  {selectedStock.holding && tradeType === 'sell' && (
                    <div className="bg-brand-2/10 rounded-lg p-4 border border-brand-2/20">
                      <p className="text-xs text-brand-2 mb-1 font-bold">Your Investment</p>
                      <p className="text-sm font-semibold text-text-main">
                        {selectedStock.holding.quantity} shares available
                      </p>
                    </div>
                  )}

                  {message && (
                    <div className={`rounded-xl p-4 flex items-center gap-2 ${
                      message.type === 'success' ? 'bg-accent-green/10 text-accent-green border border-accent-green/20' : 'bg-accent-red/10 text-accent-red border border-accent-red/20'
                    }`}>
                      <AlertCircle className="w-5 h-5 flex-shrink-0" />
                      <span className="text-sm font-medium">{message.text}</span>
                    </div>
                  )}

                  <button
                    onClick={handleTrade}
                    disabled={trading || !quantity || parseInt(quantity) <= 0}
                    className={`w-full py-4 rounded-xl font-bold text-white transition-all transform active:scale-[0.98] ${
                      tradeType === 'buy'
                        ? 'bg-brand-1 hover:bg-brand-600 shadow-md hover:shadow-lg shadow-brand-1/20'
                        : 'bg-accent-red hover:bg-red-500 shadow-md hover:shadow-lg shadow-accent-red/20'
                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    {trading ? 'Processing...' : `${tradeType === 'buy' ? 'BUY' : 'SELL'} ${selectedStock.symbol}`}
                  </button>

                  <div className="text-center">
                    <p className="text-xs font-medium text-text-muted">
                      Balance: ₹{portfolio.balance?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </div>
                </div>

                {tradeXpText && (
                  <div className="pointer-events-none absolute right-6 top-4 xp-float text-brand-2 text-lg font-extrabold number-tabular">
                    {tradeXpText}
                  </div>
                )}

                {showTradeCelebration && (
                  <div className="pointer-events-none absolute inset-0 overflow-hidden">
                    {[...Array(10)].map((_, idx) => (
                      <span
                        key={`trade-conf-${idx}`}
                        className="confetti-piece absolute w-2 h-3 rounded-sm"
                        style={{
                          left: `${10 + idx * 8}%`,
                          top: '10%',
                          backgroundColor: idx % 2 === 0 ? '#00f5a0' : '#00d1ff',
                          animationDelay: `${idx * 30}ms`,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default PortfolioTrade
