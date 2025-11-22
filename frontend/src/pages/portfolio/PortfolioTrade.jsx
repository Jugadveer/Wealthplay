import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Search,
  TrendingUp as BuyIcon,
  TrendingDown as SellIcon,
  Sparkles,
  AlertCircle,
} from 'lucide-react'
import api from '../../utils/api'

const PortfolioTrade = ({ portfolio, onRefresh }) => {
  const [searchParams] = useSearchParams()
  const [stocks, setStocks] = useState([])
  const [selectedStock, setSelectedStock] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [aiRecommendation, setAiRecommendation] = useState(null)
  const [tradeType, setTradeType] = useState('buy') // 'buy' or 'sell'
  const [quantity, setQuantity] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [trading, setTrading] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    fetchStocks()
    const symbolParam = searchParams.get('symbol')
    if (symbolParam) {
      handleStockSelect(symbolParam)
    }
  }, [searchParams])

  const fetchStocks = async () => {
    try {
      const response = await api.getStocks()
      setStocks(response.data.stocks || [])
    } catch (error) {
      console.error('Error fetching stocks:', error)
    }
  }

  const handleStockSelect = async (symbol) => {
    setLoading(true)
    try {
      const response = await api.getStockDetail(symbol)
      setSelectedStock(response.data)
      setPriceHistory(response.data.price_history || [])
      
      // Fetch AI recommendation
      const aiResponse = await api.getAIRecommendation({ symbol, action: 'analyze' })
      setAiRecommendation(aiResponse.data)
    } catch (error) {
      console.error('Error fetching stock detail:', error)
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
      const response = tradeType === 'buy' 
        ? await api.buyStock({ symbol: selectedStock.symbol, quantity: parseInt(quantity) })
        : await api.sellStock({ symbol: selectedStock.symbol, quantity: parseInt(quantity) })

      if (response.data.success) {
        setMessage({ type: 'success', text: response.data.message || 'Trade successful!' })
        setQuantity('')
        // Refresh portfolio immediately after successful trade
        if (onRefresh) {
          setTimeout(() => onRefresh(), 100) // Small delay to ensure backend update is complete
        }
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

  const formatCurrency = (value) => {
    return `₹${value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value?.toFixed(2)}%`
  }

  const calculateTotal = () => {
    if (!selectedStock || !quantity) return 0
    return parseFloat(selectedStock.current_price) * parseInt(quantity)
  }

  const maxQuantity = tradeType === 'buy'
    ? Math.floor(portfolio.balance / (selectedStock?.current_price || 1))
    : (selectedStock?.holding?.quantity || 0)

  const filteredStocks = stocks.filter(
    (stock) =>
      stock.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      stock.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Stock Search */}
      <div className="bg-white rounded-xl shadow-card p-6">
        <div className="mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
          <input
            type="text"
            placeholder="Search stocks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-muted-2 focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto">
          {filteredStocks.map((stock) => (
            <button
              key={stock.symbol}
              onClick={() => handleStockSelect(stock.symbol)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                selectedStock?.symbol === stock.symbol
                  ? 'border-brand-1 bg-brand-1/5'
                  : 'border-muted-2 hover:border-brand-1/50'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-bold text-text-main">{stock.symbol}</p>
                  <p className="text-xs text-text-muted">{stock.name}</p>
                </div>
                <span className={`text-sm font-semibold ${stock.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(stock.change_percent)}
                </span>
              </div>
              <p className="text-lg font-bold text-text-main">{formatCurrency(stock.current_price)}</p>
            </button>
          ))}
        </div>
      </div>

      {selectedStock && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Stock Details & Chart */}
          <div className="lg:col-span-2 space-y-6">
            {/* Stock Info Card */}
            <div className="bg-white rounded-xl shadow-card p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 flex items-center justify-center">
                    <span className="text-white font-bold text-xl">{selectedStock.symbol.slice(0, 2)}</span>
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-text-main">{selectedStock.symbol}</h2>
                    <p className="text-sm text-text-muted">{selectedStock.name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-text-main mb-1">
                    {formatCurrency(selectedStock.current_price)}
                  </p>
                  <p className={`text-sm font-semibold ${selectedStock.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(selectedStock.change_percent)}
                  </p>
                </div>
              </div>

              {priceHistory.length > 0 && (
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={priceHistory}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="date"
                      stroke="#6b7280"
                      style={{ fontSize: '12px' }}
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis
                      stroke="#6b7280"
                      style={{ fontSize: '12px' }}
                      tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#fff',
                        border: '1px solid #e5e7eb',
                        borderRadius: '8px',
                      }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    <Line
                      type="monotone"
                      dataKey="price"
                      stroke="#0ea5e9"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}

              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-muted-2">
                <div>
                  <p className="text-xs text-text-muted mb-1">Category</p>
                  <p className="font-semibold text-text-main">{selectedStock.category}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">Sector</p>
                  <p className="font-semibold text-text-main">{selectedStock.sector}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">Market Cap</p>
                  <p className="font-semibold text-text-main">{selectedStock.market_cap}</p>
                </div>
              </div>
            </div>

            {/* AI Recommendation */}
            {aiRecommendation && (
              <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-xl shadow-card p-6 border border-purple-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-text-main">AI Recommendation</h3>
                    <p className="text-sm text-text-muted">Based on market analysis</p>
                  </div>
                </div>

                <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg mb-4 ${
                  aiRecommendation.recommendation === 'buy' ? 'bg-green-100 text-green-700' :
                  aiRecommendation.recommendation === 'sell' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>
                  <span className="font-bold uppercase">{aiRecommendation.recommendation}</span>
                  <span className="text-sm">({Math.round(aiRecommendation.confidence * 100)}% confidence)</span>
                </div>

                <p className="text-sm text-text-main mb-3">{aiRecommendation.message}</p>

                {aiRecommendation.reasons && (
                  <ul className="space-y-1">
                    {aiRecommendation.reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-text-muted flex items-start gap-2">
                        <span className="text-purple-600">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          {/* Trade Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-card p-6 sticky top-20">
              <div className="flex gap-2 mb-6">
                <button
                  onClick={() => {
                    setTradeType('buy')
                    setQuantity('')
                    setMessage(null)
                  }}
                  className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                    tradeType === 'buy'
                      ? 'bg-green-500 text-white'
                      : 'bg-muted-2 text-text-muted'
                  }`}
                >
                  <BuyIcon className="w-5 h-5 inline mr-2" />
                  Buy
                </button>
                <button
                  onClick={() => {
                    setTradeType('sell')
                    setQuantity('')
                    setMessage(null)
                  }}
                  className={`flex-1 px-4 py-3 rounded-lg font-semibold transition-all ${
                    tradeType === 'sell'
                      ? 'bg-red-500 text-white'
                      : 'bg-muted-2 text-text-muted'
                  }`}
                >
                  <SellIcon className="w-5 h-5 inline mr-2" />
                  Sell
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-text-muted mb-2">
                    Quantity
                  </label>
                  <input
                    type="number"
                    min="1"
                    max={maxQuantity}
                    value={quantity}
                    onChange={(e) => setQuantity(e.target.value)}
                    placeholder="Enter quantity"
                    className="w-full px-4 py-3 rounded-lg border border-muted-2 focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none"
                  />
                  <p className="text-xs text-text-muted mt-1">
                    Max: {maxQuantity} shares available
                  </p>
                </div>

                <div className="pt-4 border-t border-muted-2 space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Price per share</span>
                    <span className="font-semibold text-text-main">
                      {formatCurrency(selectedStock.current_price)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-text-muted">Quantity</span>
                    <span className="font-semibold text-text-main">{quantity || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold pt-2 border-t border-muted-2">
                    <span>Total</span>
                    <span className="text-lg">{formatCurrency(calculateTotal())}</span>
                  </div>
                </div>

                {selectedStock.holding && tradeType === 'sell' && (
                  <div className="bg-muted-1 rounded-lg p-4">
                    <p className="text-xs text-text-muted mb-2">Your Holding</p>
                    <p className="text-sm font-semibold text-text-main">
                      {selectedStock.holding.quantity} shares @ {formatCurrency(selectedStock.holding.avg_price)}
                    </p>
                  </div>
                )}

                {message && (
                  <div className={`rounded-lg p-3 flex items-center gap-2 ${
                    message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                  }`}>
                    <AlertCircle className="w-5 h-5" />
                    <span className="text-sm">{message.text}</span>
                  </div>
                )}

                <button
                  onClick={handleTrade}
                  disabled={trading || !quantity || parseInt(quantity) <= 0}
                  className={`w-full px-4 py-4 rounded-xl font-semibold text-white transition-all ${
                    tradeType === 'buy'
                      ? 'bg-gradient-to-r from-green-500 to-green-600 hover:shadow-lg'
                      : 'bg-gradient-to-r from-red-500 to-red-600 hover:shadow-lg'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {trading ? 'Processing...' : `${tradeType === 'buy' ? 'Buy' : 'Sell'} Stock`}
                </button>

                <div className="bg-muted-1 rounded-lg p-4">
                  <p className="text-xs text-text-muted mb-2">Available Balance</p>
                  <p className="text-lg font-bold text-text-main">
                    {formatCurrency(portfolio.balance)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {!selectedStock && stocks.length > 0 && filteredStocks.length === 0 && (
        <div className="bg-white rounded-xl shadow-card p-12 text-center">
          <div className="w-20 h-20 rounded-full bg-muted-2 flex items-center justify-center mx-auto mb-4">
            <Search className="w-10 h-10 text-text-muted" />
          </div>
          <h3 className="text-xl font-bold text-text-main mb-2">No stocks found</h3>
          <p className="text-text-muted">Try a different search term</p>
        </div>
      )}
    </div>
  )
}

export default PortfolioTrade

