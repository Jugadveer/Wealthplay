import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import api from '../../utils/api'
import {
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Briefcase,
  Wallet,
  PieChart,
  Activity,
} from 'lucide-react'

const PortfolioOverview = ({ portfolio, onRefresh }) => {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHistory()
  }, [])

  const fetchHistory = async () => {
    try {
      const response = await api.getPortfolioHistory({ params: { days: 30 } })
      setHistory(response.data.history || [])
    } catch (error) {
      console.error('Error fetching portfolio history:', error)
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

  return (
    <div className="space-y-6">
      {/* Portfolio Value Chart */}
      <div className="bg-white rounded-xl shadow-card p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-text-main mb-1">Portfolio Value</h2>
            <p className="text-sm text-text-muted">Last 30 days</p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold text-text-main">{formatCurrency(portfolio.total_value)}</p>
            <p className={`text-sm font-semibold ${portfolio.total_pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(portfolio.total_pnl_percent)}
            </p>
          </div>
        </div>
        
        {!loading && history.length > 0 && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={history}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                </linearGradient>
              </defs>
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
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                }}
                formatter={(value) => formatCurrency(value)}
                labelFormatter={(label) => new Date(label).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#0ea5e9" 
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorValue)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <span className={`text-sm font-semibold ${portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(portfolio.total_pnl_percent)}
            </span>
          </div>
          <p className="text-sm text-text-muted mb-1">Total Returns</p>
          <p className="text-2xl font-bold text-text-main">
            {formatCurrency(portfolio.total_pnl)}
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
              <Briefcase className="w-6 h-6 text-blue-600" />
            </div>
            <span className="text-sm font-semibold text-text-muted">
              {portfolio.holdings_count || 0}
            </span>
          </div>
          <p className="text-sm text-text-muted mb-1">Holdings</p>
          <p className="text-2xl font-bold text-text-main">
            {formatCurrency(portfolio.invested)}
          </p>
          <p className="text-xs text-text-muted mt-1">Invested amount</p>
        </div>

        <div className="bg-white rounded-xl shadow-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
              <Wallet className="w-6 h-6 text-purple-600" />
            </div>
            <span className="text-sm font-semibold text-text-muted">
              {((portfolio.balance / portfolio.total_value) * 100).toFixed(1)}%
            </span>
          </div>
          <p className="text-sm text-text-muted mb-1">Cash Balance</p>
          <p className="text-2xl font-bold text-text-main">
            {formatCurrency(portfolio.balance)}
          </p>
          <p className="text-xs text-text-muted mt-1">Available for trading</p>
        </div>
      </div>

      {/* Top Holdings Preview */}
      {portfolio.holdings && portfolio.holdings.length > 0 && (
        <div className="bg-white rounded-xl shadow-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-text-main">Top Holdings</h2>
            <Link
              to="/portfolio/holdings"
              className="text-brand-1 font-semibold text-sm hover:text-brand-2 transition-colors flex items-center gap-1"
            >
              View All
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          
          <div className="space-y-4">
            {portfolio.holdings.slice(0, 5).map((holding) => (
              <div
                key={holding.symbol}
                className="flex items-center justify-between p-4 rounded-lg border border-muted-2 hover:border-brand-1/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-10 h-10 rounded-lg bg-brand-1/10 flex items-center justify-center">
                      <span className="text-brand-1 font-bold text-sm">{holding.symbol.slice(0, 2)}</span>
                    </div>
                    <div>
                      <p className="font-semibold text-text-main">{holding.symbol}</p>
                      <p className="text-xs text-text-muted">{holding.name}</p>
                    </div>
                  </div>
                </div>
                
                <div className="text-right">
                  <p className="font-semibold text-text-main">{formatCurrency(holding.current_value)}</p>
                  <p className={`text-sm font-semibold ${holding.pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPercent(holding.pnl_percent)}
                  </p>
                  <p className="text-xs text-text-muted">{holding.quantity} shares</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="bg-gradient-to-r from-brand-1 to-brand-2 rounded-xl p-6 text-white">
        <h2 className="text-xl font-bold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link
            to="/portfolio/trade"
            className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-all flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
              <ArrowUpRight className="w-5 h-5" />
            </div>
            <div>
              <p className="font-semibold">Start Trading</p>
              <p className="text-sm text-white/80">Buy or sell stocks</p>
            </div>
          </Link>
          
          <Link
            to="/portfolio/analysis"
            className="bg-white/20 backdrop-blur-sm rounded-lg p-4 hover:bg-white/30 transition-all flex items-center gap-3"
          >
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <p className="font-semibold">View Analysis</p>
              <p className="text-sm text-white/80">AI insights & recommendations</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default PortfolioOverview

