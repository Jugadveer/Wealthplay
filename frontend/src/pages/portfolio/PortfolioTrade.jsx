import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { 
  LineChart, 
  Line, 
  AreaChart,
  Area,
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer,
} from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Search,
  Sparkles,
  AlertCircle,
  Loader2,
} from 'lucide-react'
import api from '../../utils/api'
import { useAchievements } from '../../contexts/AchievementContext'
import TradingViewChart from '../../components/TradingViewChart'

// Using external TradingViewChart component for pro-grade candlesticks

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
  const [chartMode, setChartMode] = useState('line')
  const [convictionAnalysis, setConvictionAnalysis] = useState(null)
  
  // Elite Features State
  const [unlockedFeatures, setUnlockedFeatures] = useState({ short_selling: false, stop_loss: false })
  const [postMortemReady, setPostMortemReady] = useState(false)
  const [showPostMortem, setShowPostMortem] = useState(false)
  const [postMortemReport, setPostMortemReport] = useState('')
  const [stressTestActive, setStressTestActive] = useState(false)

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

      // Check features lock
      const portfolioResp = await api.getPortfolio()
      if (portfolioResp.data.unlocked_features) {
        setUnlockedFeatures(portfolioResp.data.unlocked_features)
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
    setConvictionAnalysis(null)

    try {
      const response = await api.tradeAsset({ 
        symbol: selectedStock.symbol, 
        action: tradeType.toUpperCase(),
        quantity: parseInt(quantity) 
      })

      setMessage({ type: 'success', text: response.data?.msg || response.data?.message || 'Trade successful!' })
      if (response.data?.post_mortem_ready) {
        setPostMortemReady(true)
      }
      
      setQuantity('')
      window.dispatchEvent(new CustomEvent('portfolio-updated', { detail: response.data || null }))
      window.dispatchEvent(new CustomEvent('achievement-updated'))

      if (typeof onRefresh === 'function') {
        onRefresh()?.catch?.(() => {})
      }

      if (typeof refreshStocksCache === 'function') {
        refreshStocksCache(true)?.catch?.(() => {})
      }

      checkAchievements().catch(() => {})
      handleStockSelect(selectedStock.symbol)

      if (tradeType === 'buy' || tradeType === 'cover') {
        setShowTradeCelebration(true)
        setTradeXpText('+10 XP')
        setTimeout(() => setShowTradeCelebration(false), 900)
        setTimeout(() => setTradeXpText(''), 1200)
      }
    } catch (error) {
      const data = error.response?.data
      if (data?.error === 'Psychological Pause' || data?.error === 'Short Selling Locked' || data?.error === 'Stop Loss Locked') {
        setMessage({
          type: 'error',
          text: (
            <div className="flex flex-col gap-2">
              <span className="font-bold underline">{data.error}</span>
              <p>{data.msg}</p>
              <button 
                onClick={() => {
                  const redirectId = data.lock_redirect || data.pause_redirect
                  window.location.href = `/lessons?module=${redirectId}`
                }}
                className="mt-1 text-xs bg-accent-red/20 hover:bg-accent-red/30 py-1 rounded border border-accent-red/30 transition-all font-bold"
              >
                Go to Module ->
              </button>
            </div>
          )
        })
      } else {
        setMessage({
          type: 'error',
          text: error.response?.data?.error || 'Trade failed. Please try again.',
        })
      }
    } finally {
      setTrading(false)
    }
  }

  const fetchPostMortem = async () => {
    try {
      const response = await api.get('/simulator/post-mortem/')
      setPostMortemReport(response.data.report)
      setShowPostMortem(true)
      setPostMortemReady(false)
    } catch (err) {
      console.error('Error fetching post mortem:', err)
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

  const unitPriceINR = selectedStock
    ? ((selectedStock.currency || 'INR') === 'USD'
      ? (selectedStock.current_price || 0) * USD_TO_INR
      : (selectedStock.current_price || 0))
    : 1

  const maxQuantity = tradeType === 'buy' || tradeType === 'short'
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
    <div className={`space-y-6 transition-colors duration-1000 ${stressTestActive ? 'bg-red-500/10 border-2 border-red-600 animate-pulse-subtle p-4 rounded-3xl' : ''}`}>
      {stressTestActive && (
        <div className="bg-red-600 text-white py-2 px-4 rounded-xl flex items-center justify-between animate-bounce border-4 border-white shadow-2xl">
          <div className="flex items-center gap-4">
            <AlertCircle className="w-6 h-6 animate-spin" />
            <span className="font-black text-xl italic tracking-tighter uppercase">⚠️ PANIC MODE: MASSIVE VOLATILITY DETECTED ⚠️</span>
          </div>
          <span className="font-bold">HODL OR DIE</span>
        </div>
      )}
      {showPostMortem && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-retro-bg/90 backdrop-blur-md animate-fade-in">
          <div className="w-full max-w-lg bg-retro-surface border-2 border-brand-2 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-2 bg-brand-2"></div>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-black text-brand-2 flex items-center gap-2 italic uppercase tracking-tighter">
                <TrendingUp className="w-6 h-6" /> Elite Post-Mortem Report
              </h3>
              <button 
                onClick={() => setShowPostMortem(false)}
                className="text-text-muted hover:text-text-main text-2xl font-bold"
              >
                ×
              </button>
            </div>
            <div className="bg-retro-bg/60 rounded-xl p-6 border border-brand-1/10 mb-8 font-medium leading-relaxed italic text-text-main">
              "{postMortemReport}"
            </div>
            <button 
              onClick={() => setShowPostMortem(false)}
              className="w-full py-4 bg-brand-2 text-white font-black rounded-xl hover:bg-brand-600 transition-all uppercase tracking-widest shadow-lg shadow-brand-2/20"
            >
              Acknowledged
            </button>
          </div>
        </div>
      )}

      {!selectedStock ? (
        <>
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
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <button 
               onClick={() => {
                  setSelectedStock(null);
                  setTrading(false);
                  setMessage(null);
                  setQuantity('');
               }}
               className="flex items-center gap-2 text-text-muted hover:text-text-main font-medium transition-colors"
            >
               <span className="text-lg leading-none">←</span> Back to Explore
            </button>

            {postMortemReady && (
              <button 
                onClick={fetchPostMortem}
                className="flex items-center gap-2 px-4 py-2 bg-brand-2/10 text-brand-2 rounded-lg font-bold border border-brand-2/20 animate-pulse hover:bg-brand-2 hover:text-white transition-all"
              >
                <Sparkles className="w-4 h-4" /> Analyze 10 Recent Trades
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-6">
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

                {priceHistory.length > 0 ? (
                  <>
                    <div className="mb-3 flex justify-end">
                      <div className="inline-flex rounded-lg border border-brand-1/20 bg-retro-board/60 p-1">
                        <button
                          onClick={() => setChartMode('line')}
                          className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${chartMode === 'line' ? 'bg-brand-1/20 text-text-main' : 'text-text-muted hover:text-text-main'}`}
                        >
                          Line
                        </button>
                        <button
                          onClick={() => setChartMode('candlestick')}
                          className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${chartMode === 'candlestick' ? 'bg-brand-1/20 text-text-main' : 'text-text-muted hover:text-text-main'}`}
                        >
                          Candlestick
                        </button>
                      </div>
                    </div>
                    {chartMode === 'line' ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={priceHistory}>
                          <defs>
                            <linearGradient id="colorPricePT" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor={selectedStock.change_percent >= 0 ? '#ff6b35' : '#d94c4c'} stopOpacity={0.3} />
                              <stop offset="95%" stopColor={selectedStock.change_percent >= 0 ? '#ff6b35' : '#d94c4c'} stopOpacity={0} />
                            </linearGradient>
                          </defs>
                          <XAxis dataKey="date" hide={true} />
                          <YAxis hide={true} domain={['auto', 'auto']} />
                          <Tooltip
                            contentStyle={{ backgroundColor: '#fafbf9', border: '1px solid rgba(255,107,53,0.3)', borderRadius: '8px' }}
                            labelStyle={{ color: '#ff6b35' }}
                            formatter={(value, name) => formatCurrency(value, selectedStock?.currency || 'INR')}
                          />
                          <Area type="monotone" dataKey="price" stroke={selectedStock.change_percent >= 0 ? '#ff6b35' : '#d94c4c'} strokeWidth={2} fill="url(#colorPricePT)" dot={false} />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                        <div className="h-[350px] mb-8 bg-retro-bg/30 rounded-2xl overflow-hidden border border-brand-1/10">
                          {selectedStock.price_history && (
                            <TradingViewChart 
                              data={selectedStock.price_history} 
                              colors={{
                                  background: 'transparent',
                                  textColor: '#94a3b8'
                              }}
                            />
                          )}
                        </div>
                      )}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 text-brand-1 animate-spin mb-3" />
                    <p className="text-text-muted">Loading chart data...</p>
                  </div>
                )}
              </div>

              {aiRecommendation && (
                <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-2/20 p-6 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-brand-2"></div>
                  <h3 className="font-bold text-text-main flex items-center gap-2 text-lg mb-4">
                     <Sparkles className="w-5 h-5 text-brand-2" /> Quantitative Analysis
                  </h3>
                  <p className="text-sm text-text-muted mb-3 font-medium leading-relaxed italic">{aiRecommendation.message}</p>
                </div>
              )}
            </div>

            <div className="lg:col-span-1">
              <div className="relative bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6 sticky top-24 overflow-hidden">
                <div className="grid grid-cols-2 gap-2 mb-6">
                  <button
                    onClick={() => setTradeType('buy')}
                    className={`py-3 text-xs rounded-md font-bold border transition-all ${tradeType === 'buy' ? 'bg-accent-green/20 text-accent-green border-accent-green/30' : 'text-text-muted border-transparent hover:bg-retro-board/50'}`}
                  >
                    Buy
                  </button>
                  <button
                    onClick={() => setTradeType('sell')}
                    className={`py-3 text-xs rounded-md font-bold border transition-all ${tradeType === 'sell' ? 'bg-accent-red/20 text-accent-red border-accent-red/30' : 'text-text-muted border-transparent hover:bg-retro-board/50'}`}
                  >
                    Sell
                  </button>
                  <button
                    onClick={() => setTradeType('short')}
                    className={`py-3 text-xs rounded-md font-bold border transition-all relative ${tradeType === 'short' ? 'bg-brand-2/20 text-brand-2 border-brand-2/30' : 'text-text-muted border-transparent hover:bg-retro-board/50'} ${!unlockedFeatures.short_selling ? 'opacity-50 grayscale' : ''}`}
                  >
                    Short
                    {!unlockedFeatures.short_selling && <span className="absolute -top-1 -right-1">🔒</span>}
                  </button>
                  <button
                    onClick={() => setTradeType('stop_loss')}
                    className={`py-3 text-xs rounded-md font-bold border transition-all relative ${tradeType === 'stop_loss' ? 'bg-brand-1/20 text-brand-1 border-brand-1/30' : 'text-text-muted border-transparent hover:bg-retro-board/50'} ${!unlockedFeatures.stop_loss ? 'opacity-50 grayscale' : ''}`}
                  >
                    Stop-Loss
                    {!unlockedFeatures.stop_loss && <span className="absolute -top-1 -right-1">🔒</span>}
                  </button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="text-[10px] uppercase tracking-widest font-black text-text-muted mb-2 block">Quantity (Lot Size)</label>
                    <input
                      type="number"
                      min="1"
                      max={maxQuantity}
                      value={quantity}
                      onChange={(e) => setQuantity(e.target.value)}
                      placeholder="0"
                      className="w-full px-4 py-4 rounded-xl border-2 border-brand-1/20 bg-retro-bg focus:border-brand-1 outline-none text-2xl font-black text-text-main transition-all"
                    />
                  </div>

                  <div className="pt-2 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-text-muted">Available Liquidity</span>
                      <span className="font-bold text-text-main">₹{portfolio.balance?.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between border-t border-brand-1/10 pt-3">
                      <span className="text-text-main font-black uppercase text-xs">Order Value</span>
                      <span className="text-lg font-black text-brand-1">{formatCurrency(calculateTotal())}</span>
                    </div>
                  </div>

                  {message && (
                    <div className={`rounded-xl p-4 flex items-start gap-2 border ${message.type === 'success' ? 'bg-accent-green/10 text-accent-green border-accent-green/20' : 'bg-accent-red/10 text-accent-red border-accent-red/30'}`}>
                      <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                      <div className="text-sm font-bold leading-tight">{message.text}</div>
                    </div>
                  )}

                  <button
                    onClick={handleTrade}
                    disabled={trading || !quantity || parseInt(quantity) <= 0}
                    className={`w-full py-5 rounded-xl font-black text-white transition-all transform active:scale-95 shadow-lg uppercase tracking-tighter ${
                      tradeType === 'buy' ? 'bg-accent-green hover:bg-green-600 shadow-accent-green/20' : 
                      tradeType === 'sell' ? 'bg-accent-red hover:bg-red-600 shadow-accent-red/20' :
                      tradeType === 'short' ? 'bg-brand-2 hover:bg-brand-2 shadow-brand-2/20' :
                      'bg-brand-1 hover:bg-brand-1 shadow-brand-1/20'
                    } disabled:opacity-30 disabled:cursor-not-allowed`}
                  >
                    {trading ? 'TRANSMITTING...' : `EXECUTE ${tradeType.replace('_', ' ')}: ${selectedStock.symbol}`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default PortfolioTrade
