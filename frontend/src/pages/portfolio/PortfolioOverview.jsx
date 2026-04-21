import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'
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
  Loader2,
} from 'lucide-react'

const PortfolioOverview = ({ portfolio, onRefresh }) => {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchHistory()
  }, [portfolio?.holdings_count, portfolio?.balance, portfolio?.total_value])

  const fetchHistory = async () => {
    try {
      const response = await api.getPortfolioHistory({ params: { days: 30 } })
      const historyData = response.data.history || []
      setHistory(historyData)
    } catch (error) {
      console.error('Error fetching portfolio history:', error)
      setHistory([])
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

  const normalizedHistory = history.reduce((acc, entry) => {
    const key = entry.timestamp ? new Date(entry.timestamp).toISOString().slice(0, 10) : entry.date
    if (!key) return acc
    acc[key] = entry
    return acc
  }, {})

  const orderedHistory = Object.values(normalizedHistory).sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))

  const hasMeaningfulHistory = orderedHistory.length >= 2
  const chartPoints = orderedHistory
    .map((entry) => ({
      ...entry,
      invested_value: Number(entry.invested_value ?? 0),
      return_value: Number(entry.profit_value ?? 0),
    }))
    .map((entry) => ({
      ...entry,
      current_value: entry.invested_value + entry.return_value,
    }))
    .filter((entry) => Number.isFinite(entry.current_value) && Number.isFinite(entry.invested_value))

  const chartValues = chartPoints.flatMap((entry) => [entry.current_value, entry.invested_value])
  const chartMin = chartValues.length > 0 ? Math.min(...chartValues) : 0
  const chartMax = chartValues.length > 0 ? Math.max(...chartValues) : 0
  const chartPadding = chartMax > chartMin ? Math.max((chartMax - chartMin) * 0.2, chartMax * 0.08) : Math.max(chartMax * 0.15, 100)
  const chartDomain = chartValues.length > 0
    ? [Math.max(0, chartMin - chartPadding), chartMax + chartPadding]
    : ['auto', 'auto']

  return (
    <div className="space-y-6">
      {}
      <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-text-muted mb-1">Current Value</p>
            <h2 className="text-4xl font-bold text-text-main tracking-tight">
              {formatCurrency(portfolio.current_value || portfolio.total_value || 50000)}
            </h2>
            <p className="text-sm text-text-muted mt-1">
              Balance Remaining: <span className="font-semibold text-text-main">{formatCurrency(portfolio.balance || 0)}</span> <span>(Virtual Cash)</span>
            </p>
            <div className="flex items-center gap-2 mt-2">
              <p className={`text-sm font-semibold flex items-center gap-1 ${portfolio.total_pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                {portfolio.total_pnl >= 0 ? <TrendingUp className="w-4 h-4"/> : <TrendingDown className="w-4 h-4"/>}
                {formatCurrency(Math.abs(portfolio.total_pnl))} ({formatPercent(portfolio.total_pnl_percent)}) <span className="text-text-muted font-normal">Total returns</span>
              </p>
            </div>
          </div>
          <Link
            to="/portfolio/trade"
            className="px-4 py-2 rounded-full bg-brand-1/10 border border-brand-1/20 text-brand-1 text-sm font-semibold hover:bg-brand-1/15 transition-colors whitespace-nowrap"
          >
            Buy / Sell
          </Link>
        </div>
        
        {}
        <div className="mt-8">
          {!loading && hasMeaningfulHistory ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={chartPoints} margin={{ top: 10, right: 20, left: 8, bottom: 8 }}>
                <CartesianGrid stroke="#dce4de" strokeDasharray="3 3" vertical={false} />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                  tick={{ fill: '#5f6f68', fontSize: 11 }}
                  axisLine={{ stroke: '#cad4cc' }}
                  tickLine={{ stroke: '#cad4cc' }}
                />
                <YAxis 
                  domain={chartDomain}
                  tick={{ fill: '#5f6f68', fontSize: 11 }}
                  axisLine={{ stroke: '#cad4cc' }}
                  tickLine={{ stroke: '#cad4cc' }}
                  tickFormatter={(value) => `₹${Math.round(value)}`}
                  width={58}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fafbf9',
                    border: '1px solid rgba(255,107,53,0.28)',
                    borderRadius: '8px',
                    boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
                    color: '#9a3412',
                  }}
                  labelStyle={{ color: '#ff6b35', fontWeight: 700 }}
                  formatter={(value, name) => [formatCurrency(value), name === 'Invested Capital' ? 'Invested Capital' : 'Current Value']}
                  labelFormatter={(label) => new Date(label).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
                />
                <Legend
                  verticalAlign="top"
                  iconType="line"
                  wrapperStyle={{ paddingBottom: 12, color: '#5f6f68', fontSize: 12 }}
                />
                <Line 
                  type="monotone" 
                  dataKey="current_value" 
                  stroke="#ff6b35" 
                  strokeWidth={4}
                  dot={false}
                  activeDot={{ r: 4 }}
                  name="Current Value"
                />
                <Line 
                  type="monotone" 
                  dataKey="invested_value" 
                  stroke="#8b5cf6" 
                  strokeWidth={3}
                  strokeDasharray="6 4"
                  dot={{ r: 2, fill: '#8b5cf6', strokeWidth: 0 }}
                  name="Invested Capital"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : loading ? (
            <div className="h-60 flex items-center justify-center">
               <Loader2 className="w-8 h-8 text-brand-1 animate-spin" />
            </div>
          ) : (
            <div className="h-60 flex items-center justify-center border border-dashed border-brand-1/20 rounded-lg bg-retro-board/30">
               <div className="text-center px-6">
                 <PieChart className="w-10 h-10 text-text-muted mx-auto mb-3 opacity-60" />
                 <p className="text-text-main font-semibold">No chart data available</p>
                 <p className="text-text-muted text-sm mt-1">Make a trade to see data.</p>
               </div>
            </div>
          )}
        </div>
      </div>

      {}
      <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
        <div className="flex items-center justify-between mb-6">
           <h3 className="font-bold text-lg text-text-main">Your Holdings</h3>
           <Link to="/portfolio/trade" className="text-sm font-semibold text-brand-1 hover:underline">
             Open Trade
           </Link>
        </div>
        
        {portfolio.holdings && portfolio.holdings.length > 0 ? (
          <div className="overflow-x-auto">
             <table className="w-full text-left border-collapse">
               <thead>
                 <tr className="border-b border-brand-1/10 text-xs text-text-muted font-medium">
                   <th className="pb-3 text-left">Company</th>
                   <th className="pb-3 text-right">Current Price</th>
                   <th className="pb-3 text-right">Returns</th>
                   <th className="pb-3 text-right">Value</th>
                 </tr>
               </thead>
               <tbody>
                  {portfolio.holdings.map((holding) => (
                    <tr 
                      key={holding.symbol} 
                      onClick={() => navigate(`/portfolio/trade?symbol=${holding.symbol}`)}
                      className="border-b border-brand-1/5 hover:bg-retro-board/70 cursor-pointer transition-colors group"
                    >
                      <td className="py-4">
                        <div className="flex items-center gap-3">
                           <div className="w-10 h-10 rounded border border-brand-1/10 flex items-center justify-center bg-retro-board/70 group-hover:bg-brand-1/10 text-text-muted font-bold text-xs">
                             {holding.symbol.substring(0,2)}
                           </div>
                           <div>
                             <p className="font-semibold text-text-main">{holding.symbol}</p>
                             <p className="text-xs text-text-muted">{holding.quantity} Shares • Avg ₹{holding.avg_price?.toLocaleString('en-IN', {maximumFractionDigits:1})}</p>
                           </div>
                        </div>
                      </td>
                      <td className="py-4 text-right">
                        <p className="font-medium text-text-main">{formatCurrency(holding.current_price)}</p>
                      </td>
                      <td className="py-4 text-right">
                        <p className={`font-medium ${holding.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                          {formatCurrency(holding.pnl)}
                        </p>
                        <p className={`text-xs ${holding.pnl_percent >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                          {formatPercent(holding.pnl_percent)}
                        </p>
                      </td>
                      <td className="py-4 text-right">
                        <p className="font-semibold text-text-main">{formatCurrency(holding.current_value)}</p>
                      </td>
                    </tr>
                  ))}
               </tbody>
             </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <Briefcase className="w-12 h-12 text-text-muted mx-auto mb-3 opacity-50" />
            <p className="text-text-muted">You don't have any holdings yet.</p>
            <Link to="/portfolio/trade" className="mt-4 inline-block px-6 py-2 bg-brand-1 text-white text-sm font-semibold rounded-full hover:bg-brand-2 transition-colors">
              Explore Stocks
            </Link>
          </div>
        )}
      </div>

    </div>
  )
}

export default PortfolioOverview
