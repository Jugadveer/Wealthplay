import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Search,
  Filter,
} from 'lucide-react'
import api from '../../utils/api'

const PortfolioHoldings = ({ portfolio, onRefresh }) => {
  const [holdings, setHoldings] = useState(portfolio.holdings || [])
  const [selectedHolding, setSelectedHolding] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    setHoldings(portfolio.holdings || [])
  }, [portfolio])

  const handleStockClick = async (symbol) => {
    setLoading(true)
    try {
      const response = await api.getStockDetail(symbol)
      const history = response.data.price_history || []
      setPriceHistory(history)
      setSelectedHolding({
        ...response.data,
        holding: response.data.holding,
      })
    } catch (error) {
      console.error('Error fetching stock detail:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (value) => {
    return `₹${value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPercent = (value) => {
    return `${value >= 0 ? '+' : ''}${value?.toFixed(2)}%`
  }

  const filteredHoldings = holdings.filter(
    (holding) =>
      holding.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
      holding.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  if (holdings.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-card p-12 text-center">
        <div className="w-20 h-20 rounded-full bg-muted-2 flex items-center justify-center mx-auto mb-4">
          <TrendingUp className="w-10 h-10 text-text-muted" />
        </div>
        <h3 className="text-xl font-bold text-text-main mb-2">No Holdings Yet</h3>
        <p className="text-text-muted mb-6">Start building your portfolio by buying stocks</p>
        <Link
          to="/portfolio/trade"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold hover:shadow-lg transition-all"
        >
          Start Trading
          <ArrowUpRight className="w-5 h-5" />
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-card p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search stocks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-muted-2 focus:border-brand-1 focus:ring-2 focus:ring-brand-1/20 outline-none"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 rounded-lg border border-muted-2 hover:border-brand-1 transition-colors">
            <Filter className="w-5 h-5 text-text-muted" />
            <span className="text-sm font-semibold text-text-main">Filter</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Holdings List */}
        <div className="lg:col-span-2 space-y-4">
          {filteredHoldings.map((holding) => (
            <div
              key={holding.symbol}
              onClick={() => handleStockClick(holding.symbol)}
              className={`bg-white rounded-xl shadow-card p-6 cursor-pointer transition-all hover:shadow-lg ${
                selectedHolding?.symbol === holding.symbol ? 'ring-2 ring-brand-1' : ''
              }`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 flex items-center justify-center">
                    <span className="text-white font-bold text-lg">{holding.symbol.slice(0, 2)}</span>
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-text-main">{holding.symbol}</h3>
                    <p className="text-sm text-text-muted">{holding.name}</p>
                  </div>
                </div>
                
                <div className={`flex items-center gap-1 ${holding.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {holding.change_percent >= 0 ? (
                    <TrendingUpIcon className="w-4 h-4" />
                  ) : (
                    <TrendingDownIcon className="w-4 h-4" />
                  )}
                  <span className="text-sm font-semibold">{formatPercent(holding.change_percent)}</span>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 pt-4 border-t border-muted-2">
                <div>
                  <p className="text-xs text-text-muted mb-1">Quantity</p>
                  <p className="font-semibold text-text-main">{holding.quantity}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">Avg Price</p>
                  <p className="font-semibold text-text-main">{formatCurrency(holding.avg_price)}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">Current Price</p>
                  <p className="font-semibold text-text-main">{formatCurrency(holding.current_price)}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-muted-2">
                <div>
                  <p className="text-xs text-text-muted mb-1">Invested</p>
                  <p className="font-semibold text-text-main">{formatCurrency(holding.invested)}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">Current Value</p>
                  <p className="font-semibold text-text-main">{formatCurrency(holding.current_value)}</p>
                </div>
                <div>
                  <p className="text-xs text-text-muted mb-1">P&L</p>
                  <p className={`font-semibold ${holding.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(holding.pnl)} ({formatPercent(holding.pnl_percent)})
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Stock Detail Panel */}
        {selectedHolding && (
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-card p-6 sticky top-20">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-text-main">Stock Details</h3>
                <button
                  onClick={() => setSelectedHolding(null)}
                  className="text-text-muted hover:text-text-main transition-colors"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-1 to-brand-2 flex items-center justify-center">
                      <span className="text-white font-bold">{selectedHolding.symbol.slice(0, 2)}</span>
                    </div>
                    <div>
                      <h4 className="font-bold text-lg text-text-main">{selectedHolding.symbol}</h4>
                      <p className="text-sm text-text-muted">{selectedHolding.name}</p>
                    </div>
                  </div>

                  <div className="mb-4">
                    <p className="text-2xl font-bold text-text-main mb-1">
                      {formatCurrency(selectedHolding.current_price)}
                    </p>
                    <p className={`text-sm font-semibold ${selectedHolding.change_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(selectedHolding.change_percent)}
                    </p>
                  </div>
                </div>

                {priceHistory.length > 0 && (
                  <div>
                    <h5 className="text-sm font-semibold text-text-muted mb-3">Price Chart (30 days)</h5>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={priceHistory}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                          dataKey="date"
                          stroke="#6b7280"
                          style={{ fontSize: '10px' }}
                          tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                        />
                        <YAxis
                          stroke="#6b7280"
                          style={{ fontSize: '10px' }}
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
                  </div>
                )}

                {selectedHolding.holding && (
                  <div className="pt-4 border-t border-muted-2">
                    <h5 className="text-sm font-semibold text-text-muted mb-3">Your Holding</h5>
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-sm text-text-muted">Quantity</span>
                        <span className="text-sm font-semibold text-text-main">{selectedHolding.holding.quantity}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-text-muted">Avg Price</span>
                        <span className="text-sm font-semibold text-text-main">{formatCurrency(selectedHolding.holding.avg_price)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-text-muted">Invested</span>
                        <span className="text-sm font-semibold text-text-main">{formatCurrency(selectedHolding.holding.invested)}</span>
                      </div>
                    </div>
                  </div>
                )}

                <div className="pt-4 border-t border-muted-2">
                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Category</span>
                      <span className="font-semibold text-text-main">{selectedHolding.category}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Sector</span>
                      <span className="font-semibold text-text-main">{selectedHolding.sector}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-text-muted">Market Cap</span>
                      <span className="font-semibold text-text-main">{selectedHolding.market_cap}</span>
                    </div>
                  </div>
                </div>

                <Link
                  to={`/portfolio/trade?symbol=${selectedHolding.symbol}`}
                  className="w-full px-4 py-3 rounded-xl bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold text-center hover:shadow-lg transition-all block"
                >
                  Trade {selectedHolding.symbol}
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PortfolioHoldings

