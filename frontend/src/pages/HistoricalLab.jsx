import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Timer,
  Activity,
  History,
  Zap,
  Flame,
  AlertTriangle,
  Sparkles,
  Trophy,
  SkipForward,
  ChevronRight,
  RefreshCw,
} from 'lucide-react'
import api, { axios } from '../utils/api'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

const HistoricalLab = () => {
  const navigate = useNavigate()
  const [crises, setCrises] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [simData, setSimData] = useState([])
  const [isSimRunning, setIsSimRunning] = useState(false)
  const [currentNews, setCurrentNews] = useState(null)
  const [glitchActive, setGlitchActive] = useState(false)
  const [survivalReport, setSurvivalReport] = useState(null)
  
  const simInterval = useRef(null)
  const isFetching = useRef(false)

  useEffect(() => {
    fetchCrises()
    return () => clearInterval(simInterval.current)
  }, [])

  const fetchCrises = async () => {
    try {
      const response = await axios.get('/api/users/time-capsule/crises/')
      setCrises(response.data.crises || [])
      setLoading(false)
    } catch (error) {
      console.error('Error fetching crises:', error)
      setLoading(false)
    }
  }

  const startSimulation = async (crisisId) => {
    try {
      setLoading(true)
      const response = await axios.post(`/api/users/time-capsule/start/${crisisId}/`)
      setActiveSession(response.data)
      setSimData([{ day: 0, price: 100, balance: response.data.balance }])
      setIsSimRunning(true)
      setLoading(false)
      
      // Heartbeat every 2 seconds (representing a 'month' or fast-forwarded time)
      simInterval.current = setInterval(() => {
        fetchHeartbeat(response.data.session_id)
      }, 2000)
    } catch (error) {
      console.error('Error starting sim:', error)
      setLoading(false)
    }
  }

  const fetchHeartbeat = async (sessionId) => {
    if (isFetching.current) return
    isFetching.current = true
    try {
      const response = await axios.get(`/api/users/time-capsule/sim-data/${sessionId}/`)
      const d = response.data
      
      setSimData(prev => {
        const lastVal = prev.length > 0 ? prev[prev.length - 1].price : 100
        const newVal = lastVal * (1 + d.market_change)
        return [...prev, { day: d.current_day, price: newVal }].slice(-60)
      })

      if (d.news) {
        setCurrentNews(d.news)
        if (d.news.sentiment === 'panic') {
          triggerGlitch()
        }
      }

      if (d.current_day > 365) { // End of 1 year simulation
        endSimulation()
      }
    } catch (error) {
      console.error('Sim heartbeat failed:', error)
      // Don't clear interval immediately, maybe it's a transient error
    } finally {
      isFetching.current = false
    }
  }

  const triggerGlitch = () => {
    setGlitchActive(true)
    setTimeout(() => setGlitchActive(false), 1000)
  }

  const endSimulation = () => {
    clearInterval(simInterval.current)
    setIsSimRunning(false)
    // Generate mock survival report
    setSurvivalReport({
        score: Math.floor(Math.random() * 1000) + 500,
        insight: "You survived the crash with 'Diamond Hands'. While the market dropped 45%, your strategic caution preserved 80% of your capital. Real-world survivors of 2008 had to wait 2 years for this recovery—you did it in 12 minutes."
    })
  }

  const resetSim = () => {
    setActiveSession(null)
    setSimData([])
    setCurrentNews(null)
    setSurvivalReport(null)
    fetchCrises()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-retro-bg">
        <RefreshCw className="w-12 h-12 text-brand-1 animate-spin" />
      </div>
    )
  }

  return (
    <div className={`min-h-screen bg-retro-bg text-text-main pb-24 transition-all duration-300 ${glitchActive ? 'invert sepia saturate-200' : ''}`}>
      {/* Header */}
      <header className="bg-white border-b border-brand-1/10 pt-24 pb-12 px-6 lg:px-10">
        <div className="max-w-container mx-auto">
          <button
            onClick={() => navigate('/dashboard')}
            className="mb-8 bg-brand-1/10 hover:bg-brand-1/20 text-brand-1 px-5 py-2.5 rounded-full text-sm font-bold shadow-sm transition-all flex items-center gap-2 group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            Arena Dashboard
          </button>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-5xl font-black text-text-main mb-4 tracking-tighter flex items-center gap-4">
                <History className="w-12 h-12 text-brand-1" />
                Time Capsule
              </h1>
              <p className="text-xl text-text-muted font-medium max-w-2xl">
                Transport your portfolio back to history's most chaotic moments. 1 minute = 1 month. Can you survive the "Unsurvivable"?
              </p>
            </div>
            {isSimRunning && (
              <div className="flex items-center gap-4 bg-retro-surface px-6 py-4 rounded-[24px] border border-brand-1/20 shadow-lg animate-pulse">
                <Timer className="w-6 h-6 text-brand-1" />
                <div>
                   <p className="text-[10px] font-black uppercase tracking-widest text-text-muted">Sim Time Compression</p>
                   <p className="text-xl font-black text-brand-1">1 MIN : 1 MONTH</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 lg:px-10 mt-12">
        {!activeSession ? (
          /* Selection View */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {crises.map((crisis) => (
              <div 
                key={crisis.id}
                className="group bg-white rounded-[40px] p-10 border border-brand-1/10 shadow-card hover:shadow-card-hover transition-all duration-500 flex flex-col justify-between"
              >
                <div>
                  <div className="w-16 h-16 bg-retro-surface rounded-3xl flex items-center justify-center mb-8 border border-brand-1/5 group-hover:scale-110 group-hover:rotate-6 transition-all">
                    <Zap className="w-8 h-8 text-brand-1" />
                  </div>
                  <h3 className="text-3xl font-black mb-4 tracking-tight">{crisis.name}</h3>
                  <p className="text-text-muted mb-8 leading-relaxed font-medium">
                    {crisis.description}
                  </p>
                  <div className="flex gap-4 mb-10">
                     <span className="px-4 py-1.5 bg-accent-red/10 text-accent-red text-[10px] font-black uppercase rounded-full tracking-widest border border-accent-red/20">
                        {crisis.difficulty}
                     </span>
                     <span className="px-4 py-1.5 bg-brand-1/10 text-brand-1 text-[10px] font-black uppercase rounded-full tracking-widest border border-brand-1/20">
                        Historical
                     </span>
                  </div>
                </div>
                <button 
                  onClick={() => startSimulation(crisis.id)}
                  className="w-full py-5 bg-brand-1 text-white rounded-[24px] font-black uppercase tracking-widest text-sm shadow-xl hover:-translate-y-1 hover:brightness-110 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  Enter Capsule <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          /* simulation Active View */
          <div className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Left Column: Live Chart & Stats */}
              <div className="lg:col-span-8 space-y-6">
                 <div className="bg-white rounded-[40px] p-8 border border-brand-1/10 shadow-card overflow-hidden relative">
                    {glitchActive && (
                        <div className="absolute inset-0 bg-accent-red/5 z-0 animate-pulse pointer-events-none"></div>
                    )}
                    <div className="flex justify-between items-center mb-8 relative z-10">
                       <h2 className="text-2xl font-black tracking-tight">{activeSession.crisis_name} Index</h2>
                       <div className="flex items-center gap-6">
                          <div className="text-right">
                             <p className="text-[10px] font-black text-text-muted uppercase">Sim Day</p>
                             <p className="text-2xl font-black tabular-nums">{simData[simData.length-1]?.day || 0}</p>
                          </div>
                          <div className="h-10 w-[1px] bg-brand-1/10"></div>
                          <div className="text-right">
                             <p className="text-[10px] font-black text-text-muted uppercase">Session Equity</p>
                             <p className="text-2xl font-black text-brand-1 tabular-nums">
                                ₹{activeSession.balance.toLocaleString()}
                             </p>
                          </div>
                       </div>
                    </div>

                    <div className="h-[400px] w-full relative z-10">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={simData}>
                          <defs>
                            <linearGradient id="colorSim" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="var(--brand-1)" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="var(--brand-1)" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />
                          <XAxis dataKey="day" hide />
                          <YAxis domain={['auto', 'auto']} hide />
                          <Tooltip 
                            contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                            labelClassName="font-black"
                          />
                          <Area 
                            type="monotone" 
                            dataKey="price" 
                            stroke="var(--brand-1)" 
                            strokeWidth={4} 
                            fillOpacity={1} 
                            fill="url(#colorSim)" 
                            isAnimationActive={false}
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                 </div>

                 {/* Action Bar */}
                 <div className="flex gap-4">
                    <button className="flex-1 py-6 bg-accent-green text-white rounded-[32px] font-black uppercase tracking-widest shadow-lg hover:scale-[1.02] active:scale-95 transition-all">
                       Tactical Buy
                    </button>
                    <button className="flex-1 py-6 bg-accent-red text-white rounded-[32px] font-black uppercase tracking-widest shadow-lg hover:scale-[1.02] active:scale-95 transition-all">
                       Panic Sell
                    </button>
                 </div>
              </div>

              {/* Right Column: AI Guru & News */}
              <div className="lg:col-span-4 space-y-6">
                 {/* News Ticker */}
                 <div className="bg-white rounded-[32px] p-8 border border-brand-1/10 shadow-card">
                    <h3 className="text-xs font-black uppercase tracking-[0.4em] text-brand-1 mb-6 flex items-center gap-2">
                       <Activity className="w-4 h-4" /> Historical Ledger
                    </h3>
                    {currentNews ? (
                      <div className="animate-[slideIn_0.3s_ease-out]">
                         <h4 className="text-xl font-black mb-2 text-authority-navy uppercase">{currentNews.headline}</h4>
                         <p className="text-sm font-medium text-text-muted italic">"{currentNews.description}"</p>
                      </div>
                    ) : (
                      <p className="text-sm text-text-muted font-medium">Monitoring the ticker for era-shaking headlines...</p>
                    )}
                 </div>

                 {/* AI Persona */}
                 <div className="bg-brand-1 p-8 rounded-[40px] text-white shadow-card relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-3xl -mr-16 -mt-16"></div>
                    <h3 className="text-xs font-black uppercase tracking-[0.4em] opacity-60 mb-6 flex items-center gap-2">
                       <Sparkles className="w-4 h-4" /> The Ghost of Markets Past
                    </h3>
                    <p className="text-lg font-bold leading-relaxed italic border-l-2 border-white/20 pl-6">
                       {currentNews && currentNews.sentiment === 'panic' 
                         ? "Fear is palpable. The streets are bleeding. This isn't just a dip—it's a paradigm shift. Will you hold your ground, or cave to the abyss?"
                         : "The market is a pendulum of greed and fear. Right now, it's swinging toward reality. Stay disciplined, young trader."
                       }
                    </p>
                 </div>

                 {/* Dashboard Link for Stats */}
                  <div className="bg-retro-surface p-6 rounded-[32px] border border-brand-1/10">
                     <p className="text-[10px] font-black uppercase text-brand-1 tracking-widest mb-4">Survival Stats</p>
                     <div className="grid grid-cols-2 gap-4">
                        <div>
                           <p className="text-lg font-black tracking-tight">1.2x</p>
                           <p className="text-[10px] font-bold text-text-muted">Leverage Factor</p>
                        </div>
                        <div>
                           <p className="text-lg font-black tracking-tight text-accent-red">-12%</p>
                           <p className="text-[10px] font-bold text-text-muted">Drawdown</p>
                        </div>
                     </div>
                  </div>
              </div>
            </div>

            {/* Survival Report Modal Overlay */}
            {survivalReport && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100] flex items-center justify-center p-6 bg-retro-bg/80 animate-in fade-in duration-300">
                    <div className="bg-white rounded-[48px] p-12 max-w-2xl border-4 border-brand-1 shadow-2xl relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-brand-1 to-brand-2"></div>
                        <div className="flex flex-col items-center text-center">
                            <div className="w-24 h-24 bg-brand-1/10 rounded-full flex items-center justify-center mb-8">
                                <Trophy className="w-12 h-12 text-brand-1" />
                            </div>
                            <h2 className="text-4xl font-black mb-4 tracking-tighter uppercase line-clamp-1">Simulation Complete</h2>
                            <div className="bg-retro-surface px-8 py-4 rounded-full mb-8 border border-brand-1/10">
                                <p className="text-brand-1 font-black text-2xl uppercase tracking-[0.2em]">Survivor Score: {survivalReport.score}</p>
                            </div>
                            <p className="text-lg font-medium text-text-muted leading-relaxed mb-10 border-l-4 border-brand-1/20 pl-8 text-left italic">
                                "{survivalReport.insight}"
                            </p>
                            <div className="flex gap-4 w-full">
                                <button 
                                  onClick={resetSim}
                                  className="flex-1 py-5 bg-retro-surface text-brand-1 rounded-[24px] font-black uppercase tracking-widest border border-brand-1/20 hover:bg-brand-1/5 transition-all"
                                >
                                    Retry History
                                </button>
                                <button 
                                  onClick={() => navigate('/dashboard')}
                                  className="flex-1 py-5 bg-brand-1 text-white rounded-[24px] font-black uppercase tracking-widest shadow-xl hover:-translate-y-1 transition-all"
                                >
                                    Main Arena
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}

export default HistoricalLab
