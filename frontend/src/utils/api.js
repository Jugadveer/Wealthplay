import axios from 'axios'

// Configure axios defaults
axios.defaults.withCredentials = true
// Don't set Content-Type by default - let axios handle it based on data type

// Create API instance for /api routes
const apiAxios = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

// Create regular axios for non-/api routes  
const regularAxios = axios.create({
  baseURL: '',
  withCredentials: true,
})

// Get CSRF token from cookies or API
export const getCsrfToken = async () => {
  // First try to get from cookies
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      return value
    }
  }
  
  // If not in cookies, fetch from API
  try {
    const response = await axios.get('/api/csrf-token/', {
      withCredentials: true,
    })
    if (response.data?.csrfToken) {
      // Set cookie manually
      document.cookie = `csrftoken=${response.data.csrfToken}; path=/; SameSite=Lax`
      return response.data.csrfToken
    }
  } catch (error) {
    console.warn('Could not fetch CSRF token:', error)
  }
  
  return ''
}

// Add CSRF token to requests (async version)
const addCsrfTokenAsync = async (config) => {
  const token = await getCsrfToken()
  if (token) {
    config.headers['X-CSRFToken'] = token
  }
  // Ensure credentials are sent
  config.withCredentials = true
  return config
}

// Sync version for interceptors (gets from cookie)
const addCsrfToken = (config) => {
  const cookies = document.cookie.split(';')
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=')
    if (name === 'csrftoken') {
      config.headers['X-CSRFToken'] = value
      break
    }
  }
  // Ensure credentials are sent
  config.withCredentials = true
  return config
}

// Add interceptors to all axios instances
// Note: For FormData requests, don't set Content-Type - axios will set it with boundary
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
  
  // Don't set Content-Type for FormData - axios will handle it
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  } else if (!config.headers['Content-Type']) {
    // Only set Content-Type for non-FormData if not already set
    config.headers['Content-Type'] = 'application/json'
  }
  
  return config
}

axios.interceptors.request.use(addCsrfTokenWithFormData)
apiAxios.interceptors.request.use(addCsrfTokenWithFormData)
regularAxios.interceptors.request.use(addCsrfTokenWithFormData)

// Handle 401 errors globally (silently, as they're expected for non-authenticated users)
const handleResponseError = (error) => {
  // Don't log 401 errors as they're expected for non-authenticated users
  if (error.response?.status === 401) {
    // Silently handle - just return the error
    return Promise.reject(error)
  }
  return Promise.reject(error)
}

apiAxios.interceptors.response.use((response) => response, handleResponseError)
regularAxios.interceptors.response.use((response) => response, handleResponseError)

// API functions
export const api = {
  // User Profile
  getProfile: () => apiAxios.get('/users/profile/'),

  // Goals
  getGoals: () => apiAxios.get('/users/goals/api/'),
  createGoal: (data) => apiAxios.post('/users/goals/api/create/', data),
  updateGoal: (goalId, data) => apiAxios.post(`/users/goals/api/${goalId}/update/`, data),
  deleteGoal: (goalId) => apiAxios.delete(`/users/goals/api/${goalId}/delete/`),

  // Courses
  getCourses: () => apiAxios.get('/courses/json/'),
  getCourse: (courseId) => regularAxios.get(`/api/courses/json/${courseId}/`),
  getModule: (courseId, moduleId) => regularAxios.get(`/api/courses/json/${courseId}/${moduleId}/`),

  // Chat/Mentor
  sendMessage: (data) => regularAxios.post('/api/chat/mentor/respond/', data),

  // Scenarios
  startQuiz: () => apiAxios.post('/scenario/api/start/'),
  getQuiz: (runId) => apiAxios.get(`/scenario/api/quiz/${runId}/`),
  submitAnswer: (data) => apiAxios.post('/scenario/api/submit-answer/', data),
  nextQuestion: (runId) => apiAxios.post(`/scenario/api/quiz/${runId}/next/`),
  getQuizResult: (runId) => apiAxios.get(`/scenario/api/quiz/${runId}/result/`),

  // Onboarding
  saveOnboarding: (data) => apiAxios.post('/users/onboarding/', data),

  // XP
  awardXP: (data) => apiAxios.post('/users/award-xp/', data),

  // Portfolio
  getPortfolio: () => apiAxios.get('/users/portfolio/'),
  getStocks: () => apiAxios.get('/users/portfolio/stocks/'),
  getStockDetail: (symbol) => apiAxios.get(`/users/portfolio/stocks/${symbol}/`),
  buyStock: (data) => apiAxios.post('/users/portfolio/buy/', data),
  sellStock: (data) => apiAxios.post('/users/portfolio/sell/', data),
  getPortfolioHistory: (config) => apiAxios.get('/users/portfolio/history/', config),
  getAIRecommendation: (data) => apiAxios.post('/users/portfolio/ai-recommendation/', data),

  // Challenges
  getLeaderboard: (type = 'scores') => apiAxios.get(`/users/challenges/leaderboard/?type=${type}`),
  getUserChallengeStats: () => apiAxios.get('/users/challenges/stats/'),
  getRandomStockQuestion: () => apiAxios.get('/users/challenges/question/'),
  submitStockPrediction: (data) => apiAxios.post('/users/challenges/predict/', data),
  
  // Achievements
  getAchievements: () => apiAxios.get('/users/achievements/'),
  checkAchievements: () => apiAxios.post('/users/achievements/check/'),
  markAchievementNotified: (achievementId) => apiAxios.post('/users/achievements/notify/', { achievement_id: achievementId }),
}

// Export axios instance for direct use if needed
export { regularAxios as axios }

export default api

