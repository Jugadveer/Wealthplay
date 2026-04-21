import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import api from '../utils/api';
import { useAuth } from './AuthContext';

const GlobalDataContext = createContext(null);

const readCachedJson = (key, fallback) => {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
};

const writeCachedJson = (key, value) => {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Ignore storage failures and continue with in-memory cache.
  }
};

export const GlobalDataProvider = ({ children }) => {
  const { user } = useAuth();
  
  
  const [stocks, setStocks] = useState(() => readCachedJson('wp_stocks_cache', []));
  const [portfolio, setPortfolio] = useState(() => readCachedJson('wp_portfolio_cache', null));
  const [courses, setCourses] = useState([]);
  const [achievements, setAchievements] = useState(() => readCachedJson('wp_achievements_cache', []));
  
  
  const [loadingStocks, setLoadingStocks] = useState(false);
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [loadingAchievements, setLoadingAchievements] = useState(false);
  
  
  const fetchStocks = useCallback(async (force = false) => {
    setLoadingStocks(true);
    try {
      const response = await api.getStocks();
      const stocksData = response.data.stocks || [];
      setStocks(stocksData);
      writeCachedJson('wp_stocks_cache', stocksData);
      return stocksData;
    } catch (error) {
      console.error('Error fetching global stocks:', error);
      return [];
    } finally {
      setLoadingStocks(false);
    }
  }, []);

  const fetchPortfolio = useCallback(async (force = false) => {
    setLoadingPortfolio(true);
    try {
      const response = await api.getPortfolio();
      setPortfolio(response.data);
      writeCachedJson('wp_portfolio_cache', response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching global portfolio:', error);
      return null;
    } finally {
      setLoadingPortfolio(false);
    }
  }, []);

  const fetchCourses = useCallback(async () => {
    // Return early if already fetching to prevent context loops
    setLoadingCourses(true);
    try {
      const response = await api.getCourses();
      const data = response.data || [];
      setCourses(data);
      return data;
    } catch (error) {
      console.error('Error fetching global courses:', error);
      return [];
    } finally {
      setLoadingCourses(false);
    }
  }, []);

  const fetchAchievements = useCallback(async (force = false) => {
    setLoadingAchievements(true);
    try {
      const response = await api.getAchievements();
      const achievementsData = response.data.achievements || [];
      setAchievements(achievementsData);
      writeCachedJson('wp_achievements_cache', achievementsData);
      return achievementsData;
    } catch (error) {
      console.error('Error fetching global achievements:', error);
      return [];
    } finally {
      setLoadingAchievements(false);
    }
  }, []);

  
  const isHydrated = useRef(false);

  // Data hydration and cleanup
  useEffect(() => {
    if (user) {
      if (!isHydrated.current) {
        console.log('User authenticated, single-pass pre-loading global assets...');
        isHydrated.current = true;
        
        fetchStocks(false);
        fetchPortfolio(false);
        fetchCourses();
        fetchAchievements(false);
      }
    } else {
      if (isHydrated.current) {
        console.log('User logged out, clearing global assets...');
        isHydrated.current = false;
        
        setStocks([]);
        setPortfolio(null);
        setCourses([]);
        setAchievements([]);
        
        writeCachedJson('wp_stocks_cache', []);
        writeCachedJson('wp_portfolio_cache', null);
        writeCachedJson('wp_achievements_cache', []);
      }
    }
  }, [user, fetchStocks, fetchPortfolio, fetchCourses, fetchAchievements]);

  useEffect(() => {
    if (!user) return;

    const handlePortfolioUpdated = () => {
      fetchPortfolio(true);
    };
    const handleAchievementsUpdated = () => {
      fetchAchievements(true);
    };

    window.addEventListener('portfolio-updated', handlePortfolioUpdated);
    window.addEventListener('achievement-updated', handleAchievementsUpdated);
    return () => {
      window.removeEventListener('portfolio-updated', handlePortfolioUpdated);
      window.removeEventListener('achievement-updated', handleAchievementsUpdated);
    };
  }, [user, fetchPortfolio, fetchAchievements]);

  return (
    <GlobalDataContext.Provider value={{ 
      stocks, 
      loadingStocks,
      refreshStocks: fetchStocks,
      
      portfolio,
      loadingPortfolio,
      refreshPortfolio: fetchPortfolio,
      
      courses,
      loadingCourses,
      refreshCourses: fetchCourses,
      
      achievements,
      loadingAchievements,
      refreshAchievements: fetchAchievements
    }}>
      {children}
    </GlobalDataContext.Provider>
  );
};

export const useGlobalData = () => {
  const context = useContext(GlobalDataContext);
  if (!context) {
    throw new Error('useGlobalData must be used within a GlobalDataProvider');
  }
  return context;
};


export const usePortfolio = () => {
  const data = useGlobalData();
  return {
    portfolio: data.portfolio,
    refreshPortfolio: data.refreshPortfolio,
    loading: data.loadingPortfolio,
    stocksCache: data.stocks, 
    setPortfolioData: data.refreshPortfolio 
  };
};
