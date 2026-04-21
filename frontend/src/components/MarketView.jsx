import React, { useEffect, useState, useRef } from 'react';
import api from '../utils/api';
import { Activity, Newspaper, TrendingUp, TrendingDown } from 'lucide-react';
import TradingViewChart from './TradingViewChart';

const HIGHLIGHT_TERMS = [
  'Relative Strength Index',
  'RSI',
  'Resistance',
  'Support',
  'Moving Average',
  'MACD',
  'Volume',
  'Breakout',
  'Momentum',
]

const highlightSummary = (text) => {
  if (!text) return text
  return text.split(/(\s+)/).map((part, idx) => {
    const normalized = part.replace(/[^a-zA-Z]/g, '').toLowerCase()
    const shouldHighlight = HIGHLIGHT_TERMS.some((term) =>
      term.toLowerCase().split(' ').some((token) => token === normalized)
    )
    if (!shouldHighlight) {
      return <React.Fragment key={`txt-${idx}`}>{part}</React.Fragment>
    }
    return (
      <strong key={`hl-${idx}`} className="text-text-main font-semibold">
        {part}
      </strong>
    )
  })
}

const MarketView = () => {
  const [activeSymbol, setActiveSymbol] = useState('AAPL');
  const [currencies] = useState(['AAPL', 'RELIANCE.NS', '^NSEI', '^GSPC', 'BTC-USD', 'TSLA', 'MSFT', 'NVDA']);
  const [prices, setPrices] = useState({});
  const [news, setNews] = useState([]);
  const [loadingNews, setLoadingNews] = useState(false);
  const [chartData, setChartData] = useState([]);
  const [isChartReady, setIsChartReady] = useState(false);
  const socketRef = useRef(null);
  const activeSymbolRef = useRef(activeSymbol);
  const currenciesRef = useRef(currencies);

  useEffect(() => {
    activeSymbolRef.current = activeSymbol;
  }, [activeSymbol]);

  useEffect(() => {
    currenciesRef.current = currencies;
  }, [currencies]);

  
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/market/');
    socketRef.current = ws;
    let shouldClose = false;

    ws.onopen = () => {
      if (shouldClose) {
        ws.close();
        return;
      }

      if (ws.readyState === WebSocket.OPEN) {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ action: 'set_symbols', symbols: currenciesRef.current }));
      }
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'prices') {
          setPrices(message.data);
          
          const currentSymbol = activeSymbolRef.current;
          if (message.data[currentSymbol]) {
            const currentPrice = message.data[currentSymbol].price;
            setChartData(prev => {
              const now = new Date();
              // Use ISO string so the chart component can parse it robustly
              const newData = [...prev, { 
                time: now.toISOString(), 
                price: currentPrice,
                open: currentPrice, 
                high: currentPrice, 
                low: currentPrice, 
                close: currentPrice 
              }];
              return newData.slice(-100); // Keep a bit more history
            });
          }
        }
      } catch (err) {
        console.error("WS error", err);
      }
    };

    return () => {
      shouldClose = true;
      if (socketRef.current === ws) {
        socketRef.current = null;
      }

      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, []);

  useEffect(() => {
    setIsChartReady(true);
  }, []);

  
  // Fetch historical data for candlestick chart
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await api.getStockDetail(activeSymbol);
        if (res.data && res.data.price_history) {
          setChartData(res.data.price_history);
        }
      } catch (err) {
        console.error("Failed to fetch history", err);
      }
    };
    fetchHistory();
  }, [activeSymbol]);

  
  useEffect(() => {
    const fetchNews = async () => {
      setLoadingNews(true);
      try {
        const { axios } = await import('../utils/api');
        const res = await axios.get(`/api/market/news/?symbol=${activeSymbol}`);
        if (res.data && res.data.news) {
          setNews(res.data.news);
        }
      } catch (err) {
        console.error("Failed to fetch news", err);
      } finally {
        setLoadingNews(false);
      }
    };
    fetchNews();
  }, [activeSymbol]);

  const activePriceData = prices[activeSymbol];
  const isUp = activePriceData ? activePriceData.change >= 0 : true;
  const formatSymbol = (sym) => {
    const cleaned = sym.replace('^', '').replace('.NS', '')
    return cleaned || sym
  }

  return (
    <div className="bg-retro-surface rounded-2xl shadow-card p-6 flex flex-col h-full">
      
      {}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-text-main tracking-tight flex items-center gap-2">
            <Activity className="w-6 h-6 text-brand-1" /> Market Intelligence
          </h2>
          <p className="text-sm font-medium text-text-muted mt-1">Live global market feeds</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {currencies.map(sym => (
            <button
              key={sym}
              onClick={() => setActiveSymbol(sym)}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                activeSymbol === sym 
                ? 'bg-brand-1 text-white shadow-md' 
                : 'bg-retro-surface text-text-main hover:bg-brand-1/5 border border-brand-1/20'
              }`}
            >
              {formatSymbol(sym)}
            </button>
          ))}
        </div>
      </div>

      {}
      <div className="flex gap-4 overflow-x-auto pb-4 hide-scrollbar mb-2">
        {currencies.map(sym => {
          const dt = prices[sym];
          if (!dt) return null;
          const up = dt.change >= 0;
          return (
            <div key={sym} className="flex-shrink-0 flex flex-col items-center bg-brand-1/5 px-5 py-3 rounded-xl border border-brand-1/10 min-w-[140px]">
              <span className="text-xs font-bold text-text-muted mb-1">{formatSymbol(sym)}</span>
              <span className="text-lg font-bold text-text-main">{dt.price.toFixed(2)}</span>
              <span className={`text-sm font-bold flex items-center gap-1 ${up ? 'text-accent-green' : 'text-accent-red'}`}>
                {up ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {Math.abs(dt.percent).toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>

      {}
      <div className="w-full relative rounded-2xl bg-slate-50 p-4 mb-8 shadow-sm">
        <div className="absolute top-4 left-6 z-10 pointer-events-none">
            <h3 className="text-xl font-bold text-text-main">{activeSymbol}</h3>
            <p className="text-sm font-medium text-text-muted">Live Tracker</p>
        </div>
        
        <div className="w-full h-[350px] mt-12 bg-white rounded-xl overflow-hidden border border-slate-200">
          {chartData.length > 0 && (
            <TradingViewChart 
              data={chartData} 
              colors={{
                background: '#ffffff',
                textColor: '#1e293b'
              }}
            />
          )}
        </div>
      </div>

      {}
      <div>
        <h3 className="text-xl font-bold text-text-main mb-6 flex items-center gap-2">
          <Newspaper className="w-6 h-6 text-brand-1" />
          AI News Summaries & Sentiment
        </h3>
        
        {loadingNews ? (
          <div className="animate-pulse space-y-4">
            <div className="h-28 bg-brand-1/5 rounded-xl"></div>
          </div>
        ) : news.length > 0 ? (
          <div className="space-y-4 max-w-3xl mx-auto">
            {news.map((item, i) => (
              <div key={i} className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm hover:shadow-md transition-all group">
                <div className="flex justify-between items-start mb-4">
                  <a href={item.link} target="_blank" rel="noopener noreferrer" className="text-xl font-bold text-text-main group-hover:text-brand-1 transition-colors leading-tight">
                    {item.title}
                  </a>
                  <span className="text-[10px] font-bold bg-brand-1/10 text-brand-1 px-2 py-1 rounded uppercase flex-shrink-0 ml-4">
                    Top Story
                  </span>
                </div>
                <p className="text-xs font-bold text-text-muted mb-6 uppercase tracking-widest flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-1 animate-pulse"></span>
                  {item.publisher} • {new Date(item.providerPublishTime * 1000).toLocaleDateString()}
                </p>
                <div className="bg-brand-1/[0.03] p-6 rounded-2xl text-base text-text-main/90 font-medium leading-relaxed border border-brand-1/10 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-brand-1 opacity-20"></div>
                  {highlightSummary(item.summary)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-brand-1/5 rounded-2xl border border-dashed border-brand-1/30">
             <Newspaper className="w-9 h-9 text-brand-1 mx-auto mb-3 opacity-70" />
             <p className="text-text-main font-semibold mb-1">AI scanning in progress</p>
             <p className="text-text-muted">The AI is currently scanning the markets for {activeSymbol} news. Check back in a few minutes.</p>
          </div>
        )}
      </div>
      
    </div>
  );
};

export default MarketView;
