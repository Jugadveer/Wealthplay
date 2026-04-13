import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import { useAuth } from './AuthContext';

const GlobalDataContext = createContext(null);

export const GlobalDataProvider = ({ children }) => {
  const { user } = useAuth();
  
  
  const [stocks, setStocks] = useState([]);
  const [portfolio, setPortfolio] = useState(null);
  const [courses, setCourses] = useState([]);
  const [achievements, setAchievements] = useState([]);
  
  
  const [loadingStocks, setLoadingStocks] = useState(false);
  const [loadingPortfolio, setLoadingPortfolio] = useState(false);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [loadingAchievements, setLoadingAchievements] = useState(false);
  
  
  const fetchStocks = useCallback(async () => {
    if (loadingStocks) return stocks;
    setLoadingStocks(true);
    try {
      const response = await api.getStocks();
      const stocksData = response.data.stocks || [];
      setStocks(stocksData);
      return stocksData;
    } catch (error) {
      console.error('Error fetching global stocks:', error);
      return [];
    } finally {
      setLoadingStocks(false);
    }
  }, [loadingStocks, stocks]);

  const fetchPortfolio = useCallback(async () => {
    if (loadingPortfolio) return;
    setLoadingPortfolio(true);
    try {
      const response = await api.getPortfolio();
      setPortfolio(response.data);
    } catch (error) {
      console.error('Error fetching global portfolio:', error);
    } finally {
      setLoadingPortfolio(false);
    }
  }, [loadingPortfolio]);

  const fetchCourses = useCallback(async () => {
    if (loadingCourses) return;
    setLoadingCourses(true);
    try {
      const response = await api.getCourses();
      setCourses(response.data || []);
    } catch (error) {
      console.error('Error fetching global courses:', error);
    } finally {
      setLoadingCourses(false);
    }
  }, [loadingCourses]);

  const fetchAchievements = useCallback(async () => {
    if (loadingAchievements) return;
    setLoadingAchievements(true);
    try {
      const response = await api.getAchievements();
      setAchievements(response.data.achievements || []);
    } catch (error) {
      console.error('Error fetching global achievements:', error);
    } finally {
      setLoadingAchievements(false);
    }
  }, [loadingAchievements]);

  
  useEffect(() => {
    if (user) {
      console.log('User authenticated, pre-loading global assets...');
      
      fetchStocks();
      fetchPortfolio();
      fetchCourses();
      fetchAchievements();
    } else {
      
      setStocks([]);
      setPortfolio(null);
      setCourses([]);
      setAchievements([]);
    }
  }, [user]); 

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
