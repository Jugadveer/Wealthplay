import { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis } from 'recharts'
import {
  TrendingUp,
  TrendingDown,
  Sparkles,
  AlertCircle,
  Target,
  BarChart3,
  PieChart as PieChartIcon,
} from 'lucide-react'
import api from '../../utils/api'

const PortfolioAnalysis = ({ portfolio, onRefresh }) => {
  const [analysis, setAnalysis] = useState(null)
  const [aiRecommendations, setAiRecommendations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalysis()
  }, [portfolio])

  const fetchAnalysis = async () => {
    setLoading(true)
    try {
      // Fetch AI recommendations for all holdings
      const recommendations = []
      if (portfolio.holdings && portfolio.holdings.length > 0) {
        for (const holding of portfolio.holdings.slice(0, 5)) {
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

      // Calculate portfolio analysis
      const totalInvested = portfolio.invested || 0
      const totalValue = portfolio.current_value || 0
      const totalPnL = portfolio.total_pnl || 0
      const totalPnLPercent = portfolio.total_pnl_percent || 0

      // Sector distribution
      const sectorData = {}
      portfolio.holdings?.forEach((holding) => {
        // Mock sector from symbol - in production, fetch from stock detail
        const sector = 'Technology' // Would come from API
        sectorData[sector] = (sectorData[sector] || 0) + holding.current_value
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

  const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Performance */}
      <div className="bg-white rounded-xl shadow-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-brand-1/10 flex items-center justify-center">
            <BarChart3 className="w-6 h-6 text-brand-1" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-main">Portfolio Performance</h2>
            <p className="text-sm text-text-muted">Detailed analysis of your investments</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-muted-1 rounded-lg p-4">
            <p className="text-xs text-text-muted mb-1">Total Invested</p>
            <p className="text-xl font-bold text-text-main">{formatCurrency(analysis?.totalInvested)}</p>
          </div>
          <div className="bg-muted-1 rounded-lg p-4">
            <p className="text-xs text-text-muted mb-1">Current Value</p>
            <p className="text-xl font-bold text-text-main">{formatCurrency(analysis?.totalValue)}</p>
          </div>
          <div className="bg-muted-1 rounded-lg p-4">
            <p className="text-xs text-text-muted mb-1">Total Returns</p>
            <p className={`text-xl font-bold ${analysis?.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(analysis?.totalPnL)}
            </p>
          </div>
          <div className="bg-muted-1 rounded-lg p-4">
            <p className="text-xs text-text-muted mb-1">Return %</p>
            <p className={`text-xl font-bold ${analysis?.totalPnLPercent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(analysis?.totalPnLPercent)}
            </p>
          </div>
        </div>
      </div>

      {/* Sector Distribution */}
      {analysis?.sectorDistribution && analysis.sectorDistribution.length > 0 && (
        <div className="bg-white rounded-xl shadow-card p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-xl bg-purple-100 flex items-center justify-center">
              <PieChartIcon className="w-6 h-6 text-purple-600" />
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
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {analysis.sectorDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>

            <div className="space-y-3">
              {analysis.sectorDistribution.map((sector, index) => (
                <div key={sector.name} className="flex items-center justify-between p-3 rounded-lg bg-muted-1">
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

      {/* AI Recommendations */}
      <div className="bg-white rounded-xl shadow-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-text-main">AI Recommendations</h2>
            <p className="text-sm text-text-muted">AI-powered insights for your holdings</p>
          </div>
        </div>

        {aiRecommendations.length === 0 ? (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-text-muted mx-auto mb-4 opacity-50" />
            <p className="text-text-muted">No holdings to analyze yet</p>
            <p className="text-sm text-text-muted mt-2">Start building your portfolio to get AI insights</p>
          </div>
        ) : (
          <div className="space-y-4">
            {aiRecommendations.map((item) => (
              <div
                key={item.symbol}
                className="border border-muted-2 rounded-xl p-6 hover:border-brand-1/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold text-text-main">{item.symbol}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        item.recommendation.recommendation === 'buy'
                          ? 'bg-green-100 text-green-700'
                          : item.recommendation.recommendation === 'sell'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
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

                <div className="mt-4 pt-4 border-t border-muted-2 grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-text-muted mb-1">Current Value</p>
                    <p className="font-semibold text-text-main">{formatCurrency(item.current_value)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">P&L</p>
                    <p className={`font-semibold ${item.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(item.pnl_percent)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-text-muted mb-1">Quantity</p>
                    <p className="font-semibold text-text-main">{item.quantity} shares</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Portfolio Insights */}
      <div className="bg-gradient-to-br from-brand-1/10 to-purple-100 rounded-xl shadow-card p-6">
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
            <TrendingUp className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
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

