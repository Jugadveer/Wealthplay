/**
 * HTTP layer.
 *
 * One axios instance, one CSRF strategy, one error shape. The previous version
 * had three axios instances with overlapping interceptors and three separate
 * copies of the CSRF-cookie reader.
 */
import axios from 'axios'

const http = axios.create({ baseURL: '/api', withCredentials: true })

/** Read Django's CSRF cookie. */
function csrfCookie() {
  return document.cookie
    .split(';')
    .map((c) => c.trim().split('='))
    .find(([name]) => name === 'csrftoken')?.[1]
}

/** Ensure the CSRF cookie exists, asking the server once if it does not. */
export async function ensureCsrf() {
  const existing = csrfCookie()
  if (existing) return existing

  try {
    await http.get('/csrf-token/')
  } catch {
    // Not fatal: unsafe requests will surface a clearer 403 if it really is missing.
  }
  return csrfCookie()
}

http.interceptors.request.use((config) => {
  const token = csrfCookie()
  if (token) config.headers['X-CSRFToken'] = token

  // Let the browser set the multipart boundary itself.
  if (config.data instanceof FormData) delete config.headers['Content-Type']
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error

    // A 403 usually means the CSRF cookie rotated. Refresh it and retry once.
    if (response?.status === 403 && config && !config._retried) {
      config._retried = true
      const token = await ensureCsrf()
      if (token) {
        config.headers['X-CSRFToken'] = token
        return http(config)
      }
    }

    // Give every caller one readable string instead of digging through axios.
    error.message =
      response?.data?.error ||
      response?.data?.detail ||
      (response?.status === 401 ? 'Please sign in to continue.' : null) ||
      error.message ||
      'Something went wrong.'

    return Promise.reject(error)
  },
)

const get = (url, config) => http.get(url, config).then((r) => r.data)
const post = (url, body, config) => http.post(url, body, config).then((r) => r.data)

export const api = {
  // Account
  profile: () => get('/users/profile/'),
  login: (username, password) => post('/auth/login/', { username, password }),
  signup: (payload) => post('/auth/signup/', payload),
  logout: () => post('/auth/logout/', {}),
  saveOnboarding: (payload) => post('/users/onboarding/', payload),
  awardXp: (payload) => post('/users/award-xp/', payload),

  // Courses
  courses: () => get('/courses/json/'),
  course: (courseId) => get(`/courses/json/${courseId}/`),
  module: (courseId, moduleId) => get(`/courses/json/${courseId}/${moduleId}/`),
  answerQuestion: (payload) => post('/courses/answer/', payload),
  completeModule: (payload) => post('/courses/complete/', payload),

  // Mentor
  askMentor: (payload) => post('/chat/mentor/ask/', payload),
  mentorHistory: (courseId, moduleId) => get(`/chat/mentor/history/${courseId}/${moduleId}/`),

  // Portfolio
  portfolio: () => get('/users/portfolio/'),
  portfolioAnalysis: () => get('/users/portfolio/analysis/'),
  portfolioHistory: (days = 30) => get('/users/portfolio/history/', { params: { days } }),
  stocks: () => get('/users/portfolio/stocks/'),
  stock: (symbol) => get(`/users/portfolio/stocks/${symbol}/`),
  buy: (payload) => post('/users/portfolio/buy/', payload),
  sell: (payload) => post('/users/portfolio/sell/', payload),
  critiqueTrade: (payload) => post('/users/portfolio/critique/', payload),
  hindsight: (preset) => get('/users/portfolio/hindsight/', { params: { preset } }),
  copyTrading: () => get('/users/portfolio/copy-trading/'),
  followTrader: (payload) => post('/users/portfolio/copy-trading/follow/', payload),
  shareRationale: (payload) => post('/users/portfolio/copy-trading/post/', payload),
  tickersInfo: (symbols) => get('/users/portfolio/tickers-info/', { params: { symbols } }),

  // Market
  quotes: (symbols) => get('/market/quotes/', { params: { symbols } }),
  marketHistory: (symbol, days = 90) => get(`/market/history/${symbol}/`, { params: { days } }),
  news: (symbol) => get('/market/news/', { params: { symbol } }),
  marketNews: (limit = 8) => get('/market/news/', { params: { limit } }),

  // Challenges
  leaderboard: (type = 'scores') => get('/users/challenges/leaderboard/', { params: { type } }),
  challengeStats: () => get('/users/challenges/stats/'),
  calibration: () => get('/users/challenges/calibration/'),
  predictionQuestion: (difficulty) => get('/users/challenges/question/', { params: { difficulty } }),
  predictionHint: (symbol) => get('/users/challenges/hint/', { params: { symbol } }),
  submitPrediction: (payload) => post('/users/challenges/predict/', payload),

  // Scenarios
  startScenarioRun: () => post('/scenario/api/start/', {}),
  scenarioRun: (runId) => get(`/scenario/api/quiz/${runId}/`),
  answerScenario: (payload) => post('/scenario/api/submit-answer/', payload),
  nextScenario: (runId) => post(`/scenario/api/quiz/${runId}/next/`, {}),
  scenarioResult: (runId) => get(`/scenario/api/quiz/${runId}/result/`),

  // Achievements
  achievements: () => get('/users/achievements/'),
  checkAchievements: () => post('/users/achievements/check/', {}),
  markAchievementSeen: (id) => post('/users/achievements/notify/', { achievement_id: id }),

  // Goals
  goals: () => get('/users/goals/'),
  planGoal: (payload) => post('/users/goals/plan/', payload),
  createGoal: (payload) => post('/users/goals/create/', payload),
  updateGoal: (id, payload) => post(`/users/goals/${id}/update/`, payload),
  deleteGoal: (id) => http.delete(`/users/goals/${id}/delete/`).then((r) => r.data),
  linkGoal: (id, linked) => post(`/users/goals/${id}/link/`, { linked }),
  setContribution: (amount) =>
    post('/users/goals/contribution/', { monthly_contribution: amount }),
  payContribution: () => post('/users/goals/contribution/pay/', {}),

  // Daily
  today: () => get('/daily/today/'),
  tickerBoard: () => get('/daily/ticker/'),
  submitTicker: (payload) => post('/daily/ticker/guess/', payload),
  tickerSearch: (q) => get('/daily/ticker/search/', { params: { q } }),
  ledgerBoard: () => get('/daily/ledger/'),
  ledgerGuess: (word) => post('/daily/ledger/guess/', { word }),
  rankBoard: () => get('/daily/rank/'),
  rankSubmit: (order) => post('/daily/rank/', { order }),
  marketCall: () => get('/daily/call/'),
  submitCall: (payload) => post('/daily/call/', payload),
  numberSense: () => get('/daily/estimate/'),
  submitEstimate: (payload) => post('/daily/estimate/', payload),
  drill: () => get('/daily/drill/'),
  answerDrill: (payload) => post('/daily/drill/answer/', payload),
  streak: () => get('/daily/streak/'),
  recap: () => get('/daily/recap/'),

  // Time capsule
  crises: () => get('/users/time-capsule/crises/'),
  startCrisis: (id) => post(`/users/time-capsule/start/${id}/`, {}),
  crisisData: (sessionId) => get(`/users/time-capsule/sim-data/${sessionId}/`),
}

export default api
