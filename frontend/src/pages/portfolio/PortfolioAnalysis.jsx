import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  AlertCircle,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
  Loader2,
} from 'lucide-react'
import api from '../../utils/api'

const PortfolioAnalysis = ({ portfolio, onRefresh }) => {
  const [analysis, setAnalysis] = useState(null)
  const [aiRecommendations, setAiRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalysis()
  }, [portfolio.holdings_count, portfolio.holdings])

  const fetchAnalysis = async () => {
    setLoading(true)
    try {
      const recommendations = []
      const holdingsArray = Array.isArray(portfolio.holdings) ? portfolio.holdings : []
      if (holdingsArray.length > 0) {
        for (const holding of holdingsArray.slice(0, 5)) {
          try {
            const response = await api.getAIRecommendation({ symbol: holding.symbol, action: 'analyze' })
            recommendations.push({
              ...holding,
              recommendation: response.data,
            })
          } catch (error) {
            console.error(`Error fetching recommendation for ${holding.symbol}:`, error)
          }
        }
      }
      setAiRecommendations(recommendations)

      const totalInvested = portfolio.invested || 0
      const totalValue = portfolio.current_value || 0
      const totalPnL = portfolio.total_pnl || 0
      const totalPnLPercent = portfolio.total_pnl_percent || 0

      const sectorData = {}
      holdingsArray.forEach((holding) => {
        const sector = holding.sector || 'Other'
        sectorData[sector] = (sectorData[sector] || 0) + (holding.current_value || 0)
      })

      const sectorDistribution = Object.entries(sectorData).map(([name, value]) => ({
        name,
        value: parseFloat(value),
        percent: ((value / totalValue) * 100).toFixed(1),
      }))

      setAnalysis({
        totalInvested,
        totalValue,
        totalPnL,
        totalPnLPercent,
        sectorDistribution,
      })
    } catch (error) {
      console.error('Error fetching analysis:', error)
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

  const COLORS = ['#ff6b35', '#f59e0b', '#fb923c', '#d94c4c', '#fdba74', '#f97316']

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-12 h-12 text-brand-1 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {}
      <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center border border-brand-1/10">
            <BarChart3 className="w-6 h-6 text-brand-1" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-main">Portfolio Performance</h2>
            <p className="text-sm text-text-muted">Detailed analysis of your investments</p>
          </div>
        </div>

        <div className="mb-4 flex justify-end">
          <Link
            to="/portfolio/trade"
            className="px-4 py-2 rounded-full bg-brand-1/10 border border-brand-1/20 text-brand-1 text-sm font-semibold hover:bg-brand-1/15 transition-colors"
          >
            Explore / Buy / Sell
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-retro-surface rounded-lg p-4 border border-brand-1/10 shadow-sm">
            <p className="text-xs text-text-muted mb-1">Total Invested</p>
            <p className="text-xl font-bold text-text-main">{formatCurrency(analysis?.totalInvested)}</p>
          </div>
          <div className="bg-retro-surface rounded-lg p-4 border border-brand-1/10 shadow-sm">
            <p className="text-xs text-text-muted mb-1">Current Value</p>
            <p className="text-xl font-bold text-text-main">{formatCurrency(analysis?.totalValue)}</p>
          </div>
          <div className="bg-retro-surface rounded-lg p-4 border border-brand-1/10 shadow-sm">
            <p className="text-xs text-text-muted mb-1">Total Returns</p>
            <p className={`text-xl font-bold ${analysis?.totalPnL >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              {formatCurrency(analysis?.totalPnL)}
            </p>
          </div>
          <div className="bg-retro-surface rounded-lg p-4 border border-brand-1/10 shadow-sm">
            <p className="text-xs text-text-muted mb-1">Return %</p>
            <p className={`text-xl font-bold ${analysis?.totalPnLPercent >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
              {formatPercent(analysis?.totalPnLPercent)}
            </p>
          </div>
        </div>
      </div>

      {}
      {analysis?.sectorDistribution && analysis.sectorDistribution.length > 0 && (
        <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center border border-brand-1/10">
              <PieChartIcon className="w-6 h-6 text-brand-1" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-text-main">Sector Distribution</h2>
              <p className="text-sm text-text-muted">Your portfolio by sectors</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analysis.sectorDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={false}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {analysis.sectorDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: '#fafbf9',
                    border: '1px solid rgba(255,107,53,0.3)',
                    borderRadius: '8px',
                    color: '#9a3412',
                  }}
                  formatter={(value, name, props) => [
                    formatCurrency(value),
                    `${props.payload.name} (${props.payload.percent}%)`
                  ]}
                />
                <Legend 
                  formatter={(value, entry) => `${entry.payload.name} (${entry.payload.percent}%)`}
                  wrapperStyle={{ paddingTop: '20px', color: '#ff6b35' }}
                />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-3">
              {analysis.sectorDistribution.map((sector, index) => (
                <div key={sector.name} className="flex items-center justify-between p-3 rounded-lg bg-retro-surface border border-brand-1/10">
                  <div className="flex items-center gap-3">
                    <div
                      className="w-4 h-4 rounded-full"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    ></div>
                    <span className="font-semibold text-text-main">{sector.name}</span>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-text-main">{formatCurrency(sector.value)}</p>
                    <p className="text-xs text-text-muted">{sector.percent}%</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {}
      <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center border border-brand-1/10">
            <Sparkles className="w-6 h-6 text-brand-1" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-main">AI Recommendations</h2>
            <p className="text-sm text-text-muted">AI-powered insights for your holdings</p>
          </div>
        </div>

        {aiRecommendations.length === 0 ? (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-30" />
            <p className="text-text-muted">No holdings to analyze yet</p>
            <p className="text-sm text-text-muted mt-2">Start building your portfolio to get AI insights</p>
          </div>
        ) : (
          <div className="space-y-4">
            {aiRecommendations.map((item) => (
              <div
                key={item.symbol}
                className="border border-brand-1/15 rounded-xl p-6 hover:border-brand-1/40 transition-colors bg-retro-surface"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold text-text-main">{item.symbol}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        item.recommendation.recommendation === 'buy'
                          ? 'bg-accent-green/15 text-accent-green'
                          : item.recommendation.recommendation === 'sell'
                          ? 'bg-accent-red/15 text-accent-red'
                          : 'bg-yellow-500/15 text-yellow-400'
                      }`}>
                        {item.recommendation.recommendation.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-text-muted">{item.name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-text-muted">Confidence</p>
                    <p className="text-lg font-bold text-text-main">
                      {Math.round(item.recommendation.confidence * 100)}%
                    </p>
                  </div>
                </div>

                <p className="text-sm text-text-main mb-3">{item.recommendation.message}</p>

                {item.recommendation.reasons && (
                  <ul className="space-y-2">
                    {item.recommendation.reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-text-muted flex items-start gap-2">
                        <Target className="w-4 h-4 text-brand-1 mt-0.5 flex-shrink-0" />
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-4 pt-4 border-t border-brand-1/10 grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-text-muted mb-1">Current Value</p>
                    <p className="font-semibold text-text-main">{formatCurrency(item.current_value)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">P&L</p>
                    <p className={`font-semibold ${item.pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                      {formatPercent(item.pnl_percent)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Quantity</p>
                    <p className="font-semibold text-text-main">{item.quantity} shares</p>
                  </div>
                </div>

                <div className="mt-4">
                  <Link
                    to={`/portfolio/trade?symbol=${item.symbol}`}
                    className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-brand-1/10 border border-brand-1/20 text-brand-1 text-sm font-semibold hover:bg-brand-1/15 transition-colors"
                  >
                    Trade {item.symbol}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {}
      <div className="bg-retro-surface rounded-xl shadow-card p-6 border border-brand-1/20">
        <h3 className="text-lg font-bold text-text-main mb-4">Portfolio Insights</h3>
        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-brand-1 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-text-main mb-1">Diversification</p>
              <p className="text-sm text-text-muted">
                Your portfolio has {portfolio.holdings_count || 0} holdings across different sectors.
                {portfolio.holdings_count < 5 && ' Consider diversifying further for better risk management.'}
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <TrendingUp className="w-5 h-5 text-accent-green mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-semibold text-text-main mb-1">Performance</p>
              <p className="text-sm text-text-muted">
                Your portfolio is showing {portfolio.total_pnl_percent >= 0 ? 'positive' : 'negative'} returns.
                {portfolio.total_pnl_percent >= 0
                  ? ' Great job! Keep monitoring your investments regularly.'
                  : ' Review your holdings and consider rebalancing.'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PortfolioAnalysis
