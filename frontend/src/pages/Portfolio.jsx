import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../utils/api'
import PortfolioOverview from './portfolio/PortfolioOverview'
import PortfolioHoldings from './portfolio/PortfolioHoldings'
import PortfolioTrade from './portfolio/PortfolioTrade'
import PortfolioAnalysis from './portfolio/PortfolioAnalysis'
import {
  TrendingUp,
  Briefcase,
  Plus,
  BarChart3,
  Home,
  Wallet,
} from 'lucide-react'

const Portfolio = () => {
  const location = useLocation()
  const { user } = useAuth()
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    // Set active tab based on route
    const path = location.pathname.split('/').pop()
    if (path === 'portfolio' || path === 'overview' || !path) {
      setActiveTab('overview')
    } else {
      setActiveTab(path)
    }
    fetchPortfolio()
  }, [location.pathname])

  const fetchPortfolio = async () => {
    try {
      const response = await api.getPortfolio()
      setPortfolio(response.data)
    } catch (error) {
      console.error('Error fetching portfolio:', error)
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Home, path: '/portfolio/overview' },
    { id: 'holdings', label: 'Holdings', icon: Briefcase, path: '/portfolio/holdings' },
    { id: 'trade', label: 'Trade', icon: Plus, path: '/portfolio/trade' },
    { id: 'analysis', label: 'Analysis', icon: BarChart3, path: '/portfolio/analysis' },
  ]

  // If portfolio is null but not loading, use default values
  const portfolioData = portfolio || {
    balance: 50000.00,
    invested: 0.00,
    current_value: 0.00,
    total_value: 50000.00,
    total_pnl: 0.00,
    total_pnl_percent: 0.00,
    holdings: [],
    holdings_count: 0,
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <div className="bg-gradient-to-br from-brand-1 to-brand-2 text-white">
        <div className="max-w-container mx-auto px-6 py-8 lg:px-10">
          <div className="mb-6">
            <h1 className="text-3xl font-bold mb-2">Portfolio</h1>
            <p className="text-white/80">Practice trading with virtual money</p>
          </div>

          {/* Portfolio Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="w-5 h-5 text-white/80" />
                <span className="text-sm text-white/80">Total Value</span>
              </div>
              <p className="text-2xl font-bold">₹{portfolioData.total_value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <p className={`text-sm mt-1 ${portfolioData.total_pnl >= 0 ? 'text-green-200' : 'text-red-200'}`}>
                {portfolioData.total_pnl >= 0 ? '+' : ''}₹{portfolioData.total_pnl?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 
                ({portfolioData.total_pnl_percent >= 0 ? '+' : ''}{portfolioData.total_pnl_percent?.toFixed(2)}%)
              </p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 text-white/80" />
                <span className="text-sm text-white/80">Invested</span>
              </div>
              <p className="text-2xl font-bold">₹{portfolioData.invested?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <p className="text-sm mt-1 text-white/60">Across {portfolioData.holdings_count || 0} holdings</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <Briefcase className="w-5 h-5 text-white/80" />
                <span className="text-sm text-white/80">Current Value</span>
              </div>
              <p className="text-2xl font-bold">₹{portfolioData.current_value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <p className="text-sm mt-1 text-white/60">Market value</p>
            </div>

            <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20">
              <div className="flex items-center gap-2 mb-2">
                <Wallet className="w-5 h-5 text-white/80" />
                <span className="text-sm text-white/80">Available Balance</span>
              </div>
              <p className="text-2xl font-bold">₹{portfolioData.balance?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
              <p className="text-sm mt-1 text-white/60">Cash available</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b border-muted-2 sticky top-0 z-10">
        <div className="max-w-container mx-auto px-6 lg:px-10">
          <div className="flex gap-1 overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <Link
                  key={tab.id}
                  to={tab.path}
                  className={`flex items-center gap-2 px-6 py-4 font-semibold transition-all border-b-2 ${
                    isActive
                      ? 'border-brand-1 text-brand-1'
                      : 'border-transparent text-text-muted hover:text-text-main'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-container mx-auto px-6 py-8 lg:px-10">
        {activeTab === 'overview' && <PortfolioOverview portfolio={portfolioData} onRefresh={fetchPortfolio} />}
        {activeTab === 'holdings' && <PortfolioHoldings portfolio={portfolioData} onRefresh={fetchPortfolio} />}
        {activeTab === 'trade' && <PortfolioTrade portfolio={portfolioData} onRefresh={fetchPortfolio} />}
        {activeTab === 'analysis' && <PortfolioAnalysis portfolio={portfolioData} onRefresh={fetchPortfolio} />}
      </div>
    </div>
  )
}

export default Portfolio

