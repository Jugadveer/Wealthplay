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
  const [portfolio, setPortfolio] = useState(() => {
    if (!user) return null;
    return readCachedJson(`wp_portfolio_cache_${user.id}`, null);
  });
  const [courses, setCourses] = useState([]);
  const [achievements, setAchievements] = useState(() => {
    if (!user) return [];
    return readCachedJson(`wp_achievements_cache_${user.id}`, []);
  });
  
  
  const [loadingStocks, setLoadingStocks] = useState(false);
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [loadingAchievements, setLoadingAchievements] = useState(false);
  
  
  const fetchStocks = useCallback(async (force = false) => {
    if (loadingStocks) return;
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
  }, [loadingStocks]);

  const fetchPortfolio = useCallback(async (force = false) => {
    if (loadingPortfolio) return;
    setLoadingPortfolio(true);
    try {
      const response = await api.getPortfolio();
      setPortfolio(response.data);
      if (user) writeCachedJson(`wp_portfolio_cache_${user.id}`, response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching global portfolio:', error);
      return null;
    } finally {
      setLoadingPortfolio(false);
    }
  }, [user, loadingPortfolio]);

  const fetchCourses = useCallback(async () => {
    if (loadingCourses) return;
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
  }, [loadingCourses]);

  const fetchAchievements = useCallback(async (force = false) => {
    if (loadingAchievements) return;
    setLoadingAchievements(true);
    try {
      const response = force ? await api.checkAchievements() : await api.getAchievements();
      const achievementsData = Array.isArray(response.data) ? response.data : (response.data.achievements || []);
      setAchievements(achievementsData);
      if (user) writeCachedJson(`wp_achievements_cache_${user.id}`, achievementsData);
      return achievementsData;
    } catch (error) {
      console.error('Error fetching global achievements:', error);
      return [];
    } finally {
      setLoadingAchievements(false);
    }
  }, [user, loadingAchievements]);

  
  const isHydrated = useRef(false);

  // Data hydration and cleanup
  useEffect(() => {
    if (user?.id) {
      if (isHydrated.current !== user.id) {
        fetchStocks();
        fetchPortfolio();
        fetchCourses();
        fetchAchievements(false);
        isHydrated.current = user.id;
      }
    } else {
      // Clear data on logout
      setPortfolio(null);
      setAchievements([]);
      isHydrated.current = false;
    }
  }, [user?.id, fetchStocks, fetchPortfolio, fetchCourses, fetchAchievements]);

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
