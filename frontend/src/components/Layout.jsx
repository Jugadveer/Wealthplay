import { useState, useEffect, useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { MessageCircle, X, Send } from 'lucide-react'
import Header from './Header'
import AuthModal from './AuthModal'

const Layout = ({ children, showNav = true }) => {
  const { user } = useAuth()
  const location = useLocation()
  const [authModal, setAuthModal] = useState(null) 
  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi! I'm Nex, your AI mentor. Ask me anything about finance, markets, or investing.",
      timestamp: new Date(),
    },
  ])
  const messagesEndRef = useRef(null)
  const isDashboardRoute = location.pathname === '/dashboard' || location.pathname.startsWith('/dashboard/')
  const isScenarioQuizRoute = location.pathname.startsWith('/scenario/quiz')
  const isLessonDetailRoute = /^\/course\/[^/]+\/[^/]+$/.test(location.pathname)
  const isNonAuthDashboard = !user && isDashboardRoute
  const shouldShowGlobalChatIcon = showNav && !isScenarioQuizRoute && !isNonAuthDashboard && !isLessonDetailRoute

  
  useEffect(() => {
    const handleOpenAuthModal = (event) => {
      const mode = event.detail || 'signup' 
      console.log('Opening auth modal:', mode)
      setAuthModal(mode)
    }

    window.addEventListener('openAuthModal', handleOpenAuthModal)
    return () => window.removeEventListener('openAuthModal', handleOpenAuthModal)
  }, [])

  
  useEffect(() => {
    if (authModal) {
      console.log('Auth modal is now:', authModal)
    }
  }, [authModal])

  
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        const { getCsrfToken } = await import('../utils/api')
        await getCsrfToken()
      } catch (error) {
        console.warn('Could not fetch CSRF token on mount:', error)
      }
    }
    fetchCsrfToken()
  }, [])

  useEffect(() => {
    if (!shouldShowGlobalChatIcon && chatOpen) {
      setChatOpen(false)
    }
  }, [shouldShowGlobalChatIcon, chatOpen])

  useEffect(() => {
    if (chatOpen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [chatOpen, messages])

  const handleGlobalChatSend = async (e) => {
    e.preventDefault()
    const text = chatInput.trim()
    if (!text) return

    const userMessage = { role: 'user', text, timestamp: new Date() }
    setMessages((prev) => [...prev, userMessage])
    setChatInput('')

    try {
      const { axios } = await import('../utils/api')
      const response = await axios.post('/api/chat/mentor/inquiry/', { question: text })
      const reply = response?.data?.reply || 'I could not generate a response right now. Please try again.'

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: reply, timestamp: new Date() },
      ])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: 'I am having trouble connecting right now. Please try again in a moment.',
          timestamp: new Date(),
        },
      ])
    }
  }

  return (
    <div className={`min-h-screen font-sans ${isDashboardRoute ? 'bg-retro-surface text-text-main' : 'bg-retro-bg text-text-main'}`}>
      {showNav && <Header onAuthClick={setAuthModal} />}
      
      <main className={showNav ? 'pt-28' : ''}>{children}</main>

      {shouldShowGlobalChatIcon && chatOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-retro-surface border border-brand-1/30 rounded-2xl shadow-modal z-50 flex flex-col overflow-hidden animate-[modalEnter_360ms_ease-out_forwards]">
          <div className="bg-retro-bg text-text-main border-b border-brand-1/20 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-brand-1 rounded-full animate-pulse"></div>
              <span className="font-bold text-text-main">Nex</span>
              <span className="text-sm text-text-muted">AI Mentor</span>
            </div>
            <button
              onClick={() => setChatOpen(false)}
              className="w-8 h-8 rounded-full bg-brand-1/10 hover:bg-brand-1/20 transition-colors flex items-center justify-center"
              aria-label="Close chat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-retro-bg">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-brand-1/20 border border-brand-1/30 text-text-main'
                      : 'bg-retro-surface border border-brand-1/10 text-text-main shadow-sm'
                  }`}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                  <p className="text-xs opacity-70 mt-1">
                    {msg.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) || ''}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleGlobalChatSend} className="p-4 border-t border-brand-1/20 bg-retro-surface">
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask Nex about markets, money, or investing..."
                className="flex-1 px-4 py-3 rounded-xl border border-brand-1/20 bg-retro-bg text-text-main focus:border-brand-1 focus:ring-4 focus:ring-brand-1/20 outline-none transition-all"
              />
              <button
                type="submit"
                className="px-4 py-3 rounded-xl bg-brand-1/10 text-brand-1 border border-brand-1/20 hover:bg-brand-1/15 transition-all active:scale-95"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>
      )}

      {shouldShowGlobalChatIcon && (
        <button
          onClick={() => {
            if (!user) {
              setAuthModal('login')
              return
            }
            setChatOpen((prev) => !prev)
          }}
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-brand-2 to-brand-1 text-white shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-180 z-50 flex items-center justify-center"
          aria-label="Open AI mentor"
          title="AI Mentor"
        >
          <MessageCircle className="w-6 h-6" />
        </button>
      )}

      {}
      {authModal && (
        <AuthModal
          mode={authModal}
          onClose={() => setAuthModal(null)}
          onSwitch={() => setAuthModal(authModal === 'login' ? 'signup' : 'login')}
        />
      )}
    </div>
  )
}

export default Layout

