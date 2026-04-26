import axios from 'axios'


axios.defaults.withCredentials = true



const apiAxios = axios.create({
  baseURL: '/api',
  withCredentials: true,
})


const regularAxios = axios.create({
  baseURL: '',
  withCredentials: true,
})


export const getCsrfToken = async () => {
  
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return value
    }
  }
  
  
  try {
    const response = await axios.get('/api/csrf-token/', {
      withCredentials: true,
    })
    if (response.data?.csrfToken) {
      
      document.cookie = `csrftoken=${response.data.csrfToken}; path=/; SameSite=Lax`
      return response.data.csrfToken
    }
  } catch (error) {
    console.warn('Could not fetch CSRF token:', error)
  }
  
  return ''
}


const addCsrfTokenAsync = async (config) => {
  const token = await getCsrfToken()
  if (token) {
    config.headers['X-CSRFToken'] = token
  }
  
  config.withCredentials = true
  return config
}


const addCsrfToken = (config) => {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      config.headers['X-CSRFToken'] = value
      break
    }
  }
  
  config.withCredentials = true
  return config
}



const addCsrfTokenWithFormData = (config) => {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      config.headers['X-CSRFToken'] = value
      break
    }
  }
  config.withCredentials = true
  
  
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  } else if (!config.headers['Content-Type']) {
    
    config.headers['Content-Type'] = 'application/json'
  }
  
  return config
}

axios.interceptors.request.use(addCsrfTokenWithFormData)
apiAxios.interceptors.request.use(addCsrfTokenWithFormData)
regularAxios.interceptors.request.use(addCsrfTokenWithFormData)


const handleResponseError = async (error) => {
  const originalRequest = error.config;
  
  
  if (error.response?.status === 403 && !originalRequest._retry) {
    originalRequest._retry = true;
    try {
      
      console.log("Refreshing CSRF token due to 403...");
      const newToken = await getCsrfToken();
      if (newToken) {
        originalRequest.headers['X-CSRFToken'] = newToken;
        
        return axios(originalRequest);
      }
    } catch (refreshError) {
      console.error("Failed to refresh CSRF token", refreshError);
    }
  }
  
  
  if (error.response?.status === 401) {
    return Promise.reject(error);
  }
  
  return Promise.reject(error);
}

apiAxios.interceptors.response.use((response) => response, handleResponseError)
regularAxios.interceptors.response.use((response) => response, handleResponseError)
axios.interceptors.response.use((response) => response, handleResponseError)


export const api = {
  
  getProfile: () => apiAxios.get('/users/profile/'),

  
  getGoals: () => apiAxios.get('/users/goals/api/'),
  createGoal: (data) => apiAxios.post('/users/goals/api/create/', data),
  updateGoal: (goalId, data) => apiAxios.post(`/users/goals/api/${goalId}/update/`, data),
  deleteGoal: (goalId) => apiAxios.delete(`/users/goals/api/${goalId}/delete/`),

  
  getCourses: () => apiAxios.get('/courses/json/'),
  getCourse: (courseId) => regularAxios.get(`/api/courses/json/${courseId}/`),
  getModule: (courseId, moduleId) => regularAxios.get(`/api/courses/json/${courseId}/${moduleId}/`),
  generateDynamicCourse: (ticker) => regularAxios.post('/api/courses/api/generate_dynamic/', { ticker }),

  
  sendMessage: (data) => regularAxios.post('/api/chat/mentor/respond/', data),

  
  startQuiz: () => apiAxios.post('/scenario/api/start/'),
  getQuiz: (runId) => apiAxios.get(`/scenario/api/quiz/${runId}/`),
  submitAnswer: (data) => apiAxios.post('/scenario/api/submit-answer/', data),
  nextQuestion: (runId) => apiAxios.post(`/scenario/api/quiz/${runId}/next/`),
  getQuizResult: (runId) => apiAxios.get(`/scenario/api/quiz/${runId}/result/`),

  
  saveOnboarding: (data) => apiAxios.post('/users/onboarding/', data),

  
  awardXP: (data) => apiAxios.post('/users/award-xp/', data),

  
  getPortfolio: () => apiAxios.get('/users/portfolio/'),
  tradeAsset: (data) => {
    const endpoint = data.action?.toLowerCase() === 'buy' ? '/users/portfolio/buy/' : '/users/portfolio/sell/'
    return apiAxios.post(endpoint, data)
  },
  getPortfolioAnalytics: () => apiAxios.get('/users/portfolio/analytics/'),

  
  getStocks: () => apiAxios.get('/users/portfolio/stocks/'),
  getStockDetail: (symbol) => apiAxios.get(`/users/portfolio/stocks/${symbol}/`),

  
  getLeaderboard: (type = 'scores') => apiAxios.get(`/users/challenges/leaderboard/?type=${type}`),
  getUserChallengeStats: () => apiAxios.get('/users/challenges/stats/'),
  getRandomStockQuestion: (difficulty) => apiAxios.get('/users/challenges/question/', { params: { difficulty } }),
  submitStockPrediction: (data) => apiAxios.post('/users/challenges/predict/', data),
  
  
  getAchievements: () => apiAxios.get('/users/achievements/'),
  checkAchievements: () => apiAxios.post('/users/achievements/check/'),
  markAchievementNotified: (achievementId) => apiAxios.post('/users/achievements/notify/', { achievement_id: achievementId }),

  
  getPortfolioHistory: (config) => apiAxios.get('/users/portfolio/history/', config),
  getAIRecommendation: (data) => apiAxios.post('/users/portfolio/ai-recommendation/', data),
  getProactiveMentorNudge: () => apiAxios.get('/users/portfolio/proactive-mentor/'),
  getPortfolioESG: () => apiAxios.get('/users/portfolio/esg/'),
  getHindsightReplay: (data) => apiAxios.post('/users/portfolio/hindsight-replay/', data),
  getCopyTradingHub: () => apiAxios.get('/users/portfolio/copy-trading/'),
  followCopyTrader: (data) => apiAxios.post('/users/portfolio/copy-trading/follow/', data),
  postTradeRationale: (data) => apiAxios.post('/users/portfolio/copy-trading/post/', data),
  
  // Time Capsule
  listCrises: () => apiAxios.get('/users/time-capsule/crises/'),
  startTimeCapsuleSession: (crisisId) => apiAxios.post(`/users/time-capsule/start/${crisisId}/`),
  getTimeCapsuleSimData: (sessionId) => apiAxios.get(`/users/time-capsule/sim-data/${sessionId}/`),
  
  getTickersInfo: (symbols) => apiAxios.get('/users/portfolio/tickers-info/', { params: { symbols } }),
}


export { apiAxios, regularAxios as axios }

export default api

