import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getCsrfToken } from '../utils/api';

const AuthWrapper = ({ children }) => {
  const { user, checkAuth } = useAuth();
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    let intervalId;
    let cancelled = false;

    const initializeAuth = async () => {
      try {
        
        await getCsrfToken();
        await checkAuth();
      } finally {
        if (!cancelled) {
          setIsReady(true);
        }

        
        intervalId = setInterval(() => {
          getCsrfToken();
        }, 15 * 60 * 1000); 
      }
    };

    initializeAuth();

    return () => {
      cancelled = true;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, []);

  if (!isReady) return <div className="min-h-screen bg-retro-bg flex items-center justify-center">
    <div className="animate-pulse bg-accent-green w-12 h-12 rounded-full"></div>
  </div>;

  return <>{children}</>;
};

export default AuthWrapper;
