import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useGlobalData } from '../contexts/GlobalDataContext'
import api from '../utils/api'
import PortfolioOverview from './portfolio/PortfolioOverview'
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
import GoalTracker from '../components/GoalTracker'

const Portfolio = () => {
  const location = useLocation()
  const { user } = useAuth()
  const {
    stocks: globalStocks,
    refreshStocks,
    portfolio: globalPortfolio,
    refreshPortfolio,
  } = useGlobalData()

  const normalizePortfolio = (data) => {
    if (!data) return null
    const holdings = data.holdings || data.assets || []
    const invested = data.invested ?? holdings.reduce((sum, a) => {
      const qty = Number(a.quantity || 0)
      const avg = Number(a.avg_price ?? a.average_buy_price ?? 0)
      return sum + (qty * avg)
    }, 0)
    const current_value = data.current_value ?? holdings.reduce((sum, a) => {
      const value = Number(a.current_value ?? a.total_value ?? 0)
      return sum + value
    }, 0)
    const total_pnl = data.total_pnl ?? (current_value - invested)
    const total_pnl_percent = data.total_pnl_percent ?? (invested > 0 ? (total_pnl / invested) * 100 : 0)

    return {
      balance: data.balance ?? data.cash_balance ?? 50000,
      invested,
      current_value,
      total_value: data.total_value ?? ((data.balance ?? data.cash_balance ?? 50000) + current_value),
      total_pnl,
      total_pnl_percent,
      holdings,
      holdings_count: data.holdings_count ?? holdings.length,
    }
  }

  const [portfolio, setPortfolio] = useState(() => normalizePortfolio(globalPortfolio))
  const [loading, setLoading] = useState(!globalPortfolio)
  const [activeTab, setActiveTab] = useState('holdings')

  useEffect(() => {
    const path = location.pathname.split('/').pop()
    if (path === 'portfolio' || path === 'overview' || !path) {
      setActiveTab('holdings')
    } else {
      setActiveTab(path)
    }
  }, [location.pathname])

  useEffect(() => {
    if (globalPortfolio) {
      setPortfolio(normalizePortfolio(globalPortfolio))
      setLoading(false)
    }
    fetchPortfolio(false)
  }, [])

  useEffect(() => {
    if (!globalPortfolio) return
    setPortfolio(normalizePortfolio(globalPortfolio))
    setLoading(false)
  }, [globalPortfolio])

  const fetchPortfolio = async (force = true) => {
    try {
      const data = typeof refreshPortfolio === 'function'
        ? await refreshPortfolio(force)
        : null

      if (data) {
        setPortfolio(normalizePortfolio(data))
        return
      }

      const response = await api.getPortfolio()
      setPortfolio(normalizePortfolio(response.data))
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
      <div className="flex items-center justify-center min-h-screen bg-retro-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg text-text-main flex flex-col">
      {}
      <div className="max-w-7xl mx-auto px-4 lg:px-10 mt-6 w-full">
        <div className="bg-retro-surface/50 border border-brand-1/10 p-1 rounded-xl inline-flex gap-2">
          <Link 
            to="/portfolio/trade" 
            className={`px-6 py-2 rounded-lg font-bold text-sm transition-all ${activeTab === 'trade' ? 'bg-brand-1/20 text-text-main shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
          >
            Explore
          </Link>
          <Link 
            to="/portfolio/holdings" 
            className={`px-6 py-2 rounded-lg font-bold text-sm transition-all ${activeTab === 'holdings' || activeTab === 'overview' ? 'bg-brand-1/20 text-text-main shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/portfolio/analysis" 
            className={`px-6 py-2 rounded-lg font-bold text-sm transition-all ${activeTab === 'analysis' ? 'bg-brand-1/20 text-text-main shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
          >
            Analysis
          </Link>
        </div>
      </div>

      {}
      <div className="md:hidden bg-retro-surface border-b border-brand-1/20 flex overflow-x-auto hide-scrollbar sticky top-16 z-10">
         <Link to="/portfolio/trade" className={`px-6 py-3 font-medium text-sm whitespace-nowrap border-b-2 ${activeTab === 'trade' ? 'border-brand-1 text-brand-1' : 'border-transparent text-text-muted'}`}>Explore</Link>
         <Link to="/portfolio/holdings" className={`px-6 py-3 font-medium text-sm whitespace-nowrap border-b-2 ${activeTab === 'holdings' || activeTab === 'overview' ? 'border-brand-1 text-brand-1' : 'border-transparent text-text-muted'}`}>Dashboard</Link>
         <Link to="/portfolio/analysis" className={`px-6 py-3 font-medium text-sm whitespace-nowrap border-b-2 ${activeTab === 'analysis' ? 'border-brand-1 text-brand-1' : 'border-transparent text-text-muted'}`}>Analysis</Link>
      </div>

      {}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 py-6 lg:px-10 lg:py-8">
        <div className={activeTab === 'overview' || activeTab === 'holdings' ? 'block' : 'hidden'}>
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-8 space-y-6">
              <PortfolioOverview portfolio={portfolioData} onRefresh={fetchPortfolio} />
            </div>
            <div className="lg:col-span-4 space-y-6">
              {}
              <div className="bg-retro-surface/80 rounded-xl shadow-card border border-brand-1/20 p-6 sticky top-24">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-bold text-text-main">Investment Summary</h3>
                  <Link
                    to="/portfolio/trade"
                    className="text-sm font-semibold text-brand-1 hover:underline"
                  >
                    Trade Stocks
                  </Link>
                </div>
                <div className="space-y-4">
                   <div className="flex justify-between items-center pb-4 border-b border-brand-1/10">
                     <span className="text-text-muted text-sm">Invested Value</span>
                     <span className="font-semibold text-text-main">₹{portfolioData.invested?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                   </div>
                   <div className="flex justify-between items-center pb-4 border-b border-brand-1/10">
                     <span className="text-text-muted text-sm">Current Value</span>
                     <span className="font-semibold text-text-main">₹{portfolioData.current_value?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                   </div>
                   <div className="flex justify-between items-center pb-4 border-b border-brand-1/10">
                     <span className="text-text-muted text-sm">Total Returns</span>
                     <span className={`font-bold ${portfolioData.total_pnl >= 0 ? 'text-accent-green' : 'text-accent-red'}`}>
                       {portfolioData.total_pnl >= 0 ? '+' : ''}₹{portfolioData.total_pnl?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                     </span>
                   </div>
                   <div className="flex justify-between items-center pt-2">
                     <span className="text-text-muted text-sm">Available Cash</span>
                     <span className="font-semibold text-text-main">₹{portfolioData.balance?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                   </div>
                   <div className="flex justify-between items-center pt-2">
                     <span className="text-text-muted text-sm flex items-center gap-1">
                       <Briefcase className="w-4 h-4"/> Holdings
                     </span>
                     <span className="font-semibold text-text-main">{portfolioData.holdings_count} Assets</span>
                   </div>
                </div>
              </div>

              {/* Goal Tracker Integration */}
              <GoalTracker compact={true} />
            </div>
          </div>
        </div>
        <div className={activeTab === 'trade' ? 'block' : 'hidden'}>
          <PortfolioTrade
            portfolio={portfolioData}
            onRefresh={fetchPortfolio}
            stocksCache={globalStocks}
            refreshStocksCache={refreshStocks}
          />
        </div>
        <div className={activeTab === 'analysis' ? 'block' : 'hidden'}>
          <PortfolioAnalysis portfolio={portfolioData} stocksCache={globalStocks} onRefresh={fetchPortfolio} />
        </div>
      </div>
    </div>
  )
}

export default Portfolio
