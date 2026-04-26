import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import api, { axios } from '../utils/api'
import {
  ArrowLeft,
  ArrowRight,
  Info,
  FileText,
  Lightbulb,
  CheckCircle2,
  MessageCircle,
  X,
  Send,
  ChevronDown,
  ChevronUp,
  Star,
  Play,
  Sparkles,
} from 'lucide-react'

const LessonDetail = () => {
  const { courseId, moduleId } = useParams()
  const navigate = useNavigate()
  const [module, setModule] = useState(null)
  const [course, setCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [overviewOpen, setOverviewOpen] = useState(false)
  const [explainOpen, setExplainOpen] = useState(false)
  const [flashCards, setFlashCards] = useState([])
  const [currentFlashCard, setCurrentFlashCard] = useState(0)
  const [flashCardRevealed, setFlashCardRevealed] = useState(false)
  const [flippedFlashCards, setFlippedFlashCards] = useState(new Set()) 
  const [mcqs, setMcqs] = useState([])
  const [mcqProgress, setMcqProgress] = useState({}) 
  const [moduleProgress, setModuleProgress] = useState(null) 

  const flippedCardCount = flippedFlashCards.size
  const correctMcqCount = Object.values(mcqProgress).filter(m => m?.correct).length
  const totalActivities = flashCards.length + mcqs.length
  const completedActivities = flippedCardCount + correctMcqCount
  const derivedModuleProgressPercent = totalActivities > 0
    ? Math.min(100, Math.round((completedActivities / totalActivities) * 100))
    : 0
  const displayModuleProgress = moduleProgress
    ? {
        ...moduleProgress,
        progress_percent: Math.max(moduleProgress.progress_percent || 0, derivedModuleProgressPercent),
        flashcards_flipped: Math.max(moduleProgress.flashcards_flipped || 0, flippedCardCount),
        mcqs_completed: Math.max(moduleProgress.mcqs_completed || 0, correctMcqCount),
      }
    : null

  useEffect(() => {
    loadModule()
  }, [courseId, moduleId])

  const loadModule = async () => {
    try {
      setLoading(true)
      
      const courseResponse = await api.getCourse(courseId)
      setCourse(courseResponse.data)

      
      const moduleResponse = await api.getModule(courseId, moduleId)
      const moduleData = moduleResponse.data.module || moduleResponse.data

      setModule(moduleData)
      
      const mcqsData = moduleData.mcqs || []
      setMcqs(mcqsData)
      
      
      if (moduleData.flash_cards && moduleData.flash_cards.length > 0) {
        
        const transformedCards = moduleData.flash_cards.map((card, idx) => ({
          id: card.id !== undefined ? String(card.id) : (card.topic ? String(card.topic) : `card-${idx}`),
          question: card.question || card.topic || '',
          answer: card.answer || card.theory_content || '',
          topic: card.topic,
          theory_title: card.theory_title,
          theory_content: card.theory_content,
          reward: { xp: 25 }
        }))
        setFlashCards(transformedCards)
        
        
        loadFlashCardProgress(courseId, moduleId)
      } else {
        
        try {
          const fullModuleId = `${courseId}_${moduleId}`
          const flashResponse = await axios.get(
            `/api/courses/api/module/${fullModuleId}/flash-cards/`
          )
          const flashCardsData = flashResponse.data.flash_cards || []
          setFlashCards(flashCardsData)
        } catch (err) {
          console.error('Error loading flash cards:', err)
          setFlashCards([])
        }
      }
      setMessages([
        {
          role: 'assistant',
          text: `Hi! I'm Nex, your AI mentor for "${moduleData.title}". Ask me anything about this topic!`,
        },
      ])
      
      
      loadModuleProgress(courseId, moduleId)
      
      loadMCQProgress(courseId, moduleId)
    } catch (error) {
      console.error('Error loading module:', error)
    } finally {
      setLoading(false)
    }
  }

  
  const loadFlashCardProgress = async (courseId, moduleId) => {
    try {
      const response = await axios.get(
        `/api/users/progress/flashcards/?course_id=${courseId}&module_id=${moduleId}`
      )
      if (response.data.flipped_cards) {
        setFlippedFlashCards(new Set(response.data.flipped_cards))
      }
    } catch (error) {
      console.error('Error loading flashcard progress:', error)
    }
  }

  
  const loadMCQProgress = async (courseId, moduleId) => {
    try {
      const response = await axios.get(
        `/api/users/progress/mcqs/?course_id=${courseId}&module_id=${moduleId}`
      )
      if (response.data.mcq_progress) {
        setMcqProgress(response.data.mcq_progress)
      }
    } catch (error) {
      console.error('Error loading MCQ progress:', error)
    }
  }

  
  const loadModuleProgress = async (courseId, moduleId) => {
    try {
      const response = await axios.get(
        `/api/users/progress/module/?course_id=${courseId}&module_id=${moduleId}`
      )
      if (response.data) {
        setModuleProgress(response.data)
      }
    } catch (error) {
      console.error('Error loading module progress:', error)
    }
  }

  
  const handleFlashCardFlip = async () => {
    if (flashCardRevealed) return 
    
    const currentCard = flashCards[currentFlashCard]
    if (!currentCard) return
    
    
    const cardId = currentCard.id || currentCard.topic || `card-${currentFlashCard}`
    if (flippedFlashCards.has(cardId)) {
      setFlashCardRevealed(true)
      return
    }
    
    setFlashCardRevealed(true)
    
    
    try {
      const response = await axios.post(
        `/api/users/progress/flashcards/flip/`,
        {
          course_id: courseId,
          module_id: moduleId,
          flashcard_id: cardId
        }
      )
      
      const newFlippedSet = new Set([...flippedFlashCards, cardId])
      setFlippedFlashCards(newFlippedSet)
      
      if (response.data.xp_awarded && response.data.xp_awarded > 0) {
        showToast('+' + response.data.xp_awarded + ' XP earned!', 'success')
      }
      
      // Update module progress count
      setModuleProgress(prev => ({
        ...prev,
        flashcards_flipped: newFlippedSet.size,
        progress_percent: Math.max(prev?.progress_percent || 0, derivedModuleProgressPercent),
      }))
      
      // We pass the updated set to check completion to avoid stale state issues
      checkModuleCompletion(newFlippedSet)
      
      // Refresh full progress from server to keep sync
      await loadModuleProgress(courseId, moduleId)
    } catch (error) {
      console.error('Error recording flashcard flip:', error)
      // Optimistic update even on error to allow UI progress
      const errorFlippedSet = new Set([...flippedFlashCards, cardId])
      setFlippedFlashCards(errorFlippedSet)
      checkModuleCompletion(errorFlippedSet)
    }
  }

  
  const checkModuleCompletion = async (currentFlippedCards = null) => {
    const cardsToUse = currentFlippedCards || flippedFlashCards
    
    const allFlashcardsFlipped = flashCards.length > 0 && 
      flashCards.every(card => {
        const cardId = card.id || card.topic || `card-${flashCards.indexOf(card)}`
        return cardsToUse.has(cardId)
      })
    
    // MCQs use local state which might also be a bit stale, but usually better
    const allMcqsAnswered = mcqs.length > 0 && 
      mcqs.every(mcq => mcqProgress[mcq.id]?.answered && mcqProgress[mcq.id]?.correct)
    
    const hasActivities = (flashCards.length > 0 || mcqs.length > 0)
    const allActivitiesComplete = (flashCards.length === 0 || allFlashcardsFlipped) && (mcqs.length === 0 || allMcqsAnswered)
    
    if (hasActivities && allActivitiesComplete) {
      try {
        const response = await axios.post(
          `/api/users/progress/module/complete/`,
          {
            course_id: courseId,
            module_id: moduleId
          }
        )
        if (response.data.completed) {
          showToast('🎉 Module completed! +' + response.data.xp_awarded + ' XP bonus!', 'success')
          
          await loadModuleProgress(courseId, moduleId)
          
          setModuleProgress(prev => ({
            ...prev,
            status: 'completed',
            progress_percent: 100,
            xp_awarded: response.data.xp_awarded || (prev?.xp_awarded || 0)
          }))
          
          
          window.dispatchEvent(new Event('module-completed'))
        }
      } catch (error) {
        console.error('Error marking module complete:', error)
      }
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!chatInput.trim()) return

    const userMessage = {
      role: 'user',
      text: chatInput,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setChatInput('')

    try {
      const response = await api.sendMessage({
        course_id: courseId,
        module_id: moduleId,
        question: chatInput,
      })

      const aiMessage = {
        role: 'assistant',
        text: response.data.answer || response.data.response || 'I apologize, but I could not generate a response.',
        timestamp: new Date(),
      }

      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        role: 'assistant',
        text: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, errorMessage])
    }
  }

  const handleMCQSubmit = async (mcq, choiceIdx) => {
    
    
    const correctAnswer = mcq.correct_answer || mcq.choices?.[mcq.correct_choice]
    const selectedAnswerText = mcq.choices?.[choiceIdx] || mcq.options?.[choiceIdx]
    const isCorrect = selectedAnswerText === correctAnswer || choiceIdx === parseInt(mcq.correct_choice)
    
    try {
      const response = await axios.post(
        `/api/users/progress/mcqs/answer/`,
        { 
          course_id: courseId,
          module_id: moduleId,
          mcq_id: mcq.id,
          choice: choiceIdx,
          selected_answer: selectedAnswerText,
          correct: isCorrect
        }
      )

      if (response.data.correct || isCorrect) {
        
        if (response.data.xp_awarded && response.data.xp_awarded > 0) {
          showToast('+' + response.data.xp_awarded + ' XP earned!', 'success')
        }
        
        
        setMcqProgress(prev => ({
          ...prev,
          [mcq.id]: {
            answered: true,
            correct: true,
            attempts: (prev[mcq.id]?.attempts || 0) + 1,
            allowRetry: false
          }
        }))
        
        
        const updatedMcqProgress = {
          ...mcqProgress,
          [mcq.id]: {
            answered: true,
            correct: true,
            attempts: (mcqProgress[mcq.id]?.attempts || 0) + 1,
            allowRetry: false
          }
        }
        const correctMcqsCount = Object.values(updatedMcqProgress).filter(m => m.correct).length
        setModuleProgress(prev => ({
          ...prev,
          mcqs_completed: correctMcqsCount,
          progress_percent: Math.max(prev?.progress_percent || 0, derivedModuleProgressPercent),
        }))
        
        
        await loadModuleProgress(courseId, moduleId)
        
        
        checkModuleCompletion()
      } else {
        
        setMcqProgress(prev => ({
          ...prev,
          [mcq.id]: {
            answered: true,
            correct: false,
            attempts: (prev[mcq.id]?.attempts || 0) + 1,
            allowRetry: true
          }
        }))
      }
      
      
      return { ...response.data, isCorrect }
    } catch (error) {
      console.error('Error submitting MCQ:', error)
      
      return { error: true, isCorrect }
    }
  }

  const nextFlashCard = () => {
    if (currentFlashCard < flashCards.length - 1) {
      setCurrentFlashCard(currentFlashCard + 1)
      setFlashCardRevealed(false)
    }
  }

  const prevFlashCard = () => {
    if (currentFlashCard > 0) {
      setCurrentFlashCard(currentFlashCard - 1)
      setFlashCardRevealed(false)
    }
  }

  if (loading || !module) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg">
      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Breadcrumb & Title Section */}
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="flex-1">
            <div className="flex items-center gap-2 text-xs font-bold text-brand-1 mb-3">
              <Link to="/course" className="hover:underline uppercase">ACADEMY</Link>
              <span className="text-brand-1/30">/</span>
              <span className="text-text-muted uppercase line-clamp-1">{course?.title || 'COURSE'}</span>
            </div>
            <h1 className="text-4xl font-bold text-text-main mb-2">{module.title}</h1>
            <p className="text-lg text-text-muted line-clamp-2">{module.summary}</p>
          </div>

          {moduleProgress && (
            <div className="w-full md:w-80 p-5 bg-retro-surface rounded-2xl shadow-glass border border-brand-1/10 backdrop-blur-md">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-brand-1 tracking-wider uppercase">
                  {moduleProgress.status === 'completed' ? 'Module Complete' : 'Your Progress'}
                </span>
                <span className="text-xs font-bold text-text-main">
                  {displayModuleProgress.progress_percent || 0}%
                </span>
              </div>
              <div className="w-full h-2.5 bg-brand-1/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-brand-1 to-brand-2 rounded-full transition-all duration-700 ease-out"
                  style={{ width: `${displayModuleProgress.progress_percent || 0}%` }}
                ></div>
              </div>
              <div className="mt-3 flex items-center justify-between text-[10px] text-text-muted uppercase font-bold tracking-tight">
                <span>{Math.max(displayModuleProgress.flashcards_flipped || 0, flippedCardCount)} / {flashCards.length} CARDS</span>
                <span>{Math.max(displayModuleProgress.mcqs_completed || 0, correctMcqCount)} / {mcqs.length} QUIZZES</span>
              </div>
            </div>
          )}
        </div>
        {/* Lesson Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-retro-surface rounded-3xl p-8 shadow-glass border border-brand-1/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-brand-1/5 rounded-full -mr-16 -mt-16 blur-3xl"></div>
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-brand-1/10 flex items-center justify-center text-brand-1">
                  <FileText className="w-6 h-6" />
                </div>
                <h2 className="text-2xl font-bold text-text-main">Lesson Theory</h2>
              </div>

              <div className="prose prose-slate max-w-none text-text-muted leading-relaxed mb-6 space-y-4">
                {(module.theory_text || module.summary || 'Learn key concepts through interactive content.').split('\n').map((para, i) => (
                  <p key={i}>{para}</p>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-4 mt-8">
                <button
                  onClick={() => setOverviewOpen(!overviewOpen)}
                  className="flex items-center gap-2 px-6 py-3 rounded-2xl border border-brand-1/30 bg-retro-surface text-brand-1 font-bold text-sm hover:bg-brand-1 hover:text-white transition-all active:scale-95 shadow-sm"
                >
                  <Info className="w-4 h-4" />
                  KEY CONCEPTS
                </button>
                <button
                  onClick={() => setExplainOpen(!explainOpen)}
                  className="flex items-center gap-2 px-6 py-3 rounded-2xl border border-brand-1/30 bg-retro-surface text-brand-1 font-bold text-sm hover:bg-brand-1 hover:text-white transition-all active:scale-95 shadow-sm"
                >
                  <Lightbulb className="w-4 h-4" />
                  SIMPLIFIED ANALOGY
                </button>
              </div>

              {/* Overview/Explain Widgets */}
              {(overviewOpen || explainOpen) && (
                <div className="mt-6 p-6 bg-brand-1/5 rounded-2xl border border-brand-1/20 animate-[fadeSlideDown_300ms_ease-out_forwards]">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-extrabold text-brand-1 uppercase tracking-widest">
                      {overviewOpen ? 'Module Overview' : 'Nex Deep-Dive'}
                    </h3>
                    <button onClick={() => { setOverviewOpen(false); setExplainOpen(false); }} className="text-text-muted hover:text-text-main">
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-sm text-text-muted leading-relaxed">
                    {overviewOpen
                      ? module.summary || 'Summary of the core principles discussed here.'
                      : module.theory_text || 'An expanded explanation focused on real-world application.'}
                  </p>
                </div>
              )}
            </div>

            {/* Did You Know Card */}
            <div className="bg-gradient-to-br from-brand-2/10 to-brand-1/10 rounded-3xl p-8 border border-brand-2/20 relative group">
              <div className="absolute -top-4 -left-4 w-12 h-12 bg-white rounded-2xl shadow-lg flex items-center justify-center text-brand-2 group-hover:rotate-12 transition-transform">
                <Star className="w-6 h-6 fill-current" />
              </div>
              <h3 className="text-xl font-extrabold text-text-main mb-3">Wealth Insight</h3>
              <p className="text-text-muted leading-relaxed">
                {module.did_you_know || "The concept of 'Compound Interest' was famously called the eighth wonder of the world. Mastering small, consistent gains is the key to outperforming high-risk speculative trading over the long term."}
              </p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-retro-surface rounded-3xl p-6 shadow-glass border border-brand-1/10">
              <h3 className="text-lg font-bold text-text-main mb-4 flex items-center gap-2">
                <Play className="w-5 h-5 text-brand-1" />
                Study Bench
              </h3>
              <div className="space-y-3">
                {[
                  { name: 'Technical Cheat Sheet', type: 'PDF', icon: 'FileText' },
                  { name: 'Formula Reference', type: 'Sheet', icon: 'TrendingUp' },
                  { name: 'Case Study: Market Crashes', type: 'Case', icon: 'BookOpen' }
                ].map((item, idx) => (
                  <button key={idx} className="w-full p-4 flex items-center justify-between bg-retro-bg rounded-2xl border border-brand-1/5 hover:border-brand-1 transition-all group">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-brand-1/10 flex items-center justify-center text-brand-1 group-hover:scale-110 transition-transform text-xs font-bold uppercase">
                        {item.type}
                      </div>
                      <span className="text-sm font-bold text-text-main">{item.name}</span>
                    </div>
                    <ArrowRight className="w-4 h-4 text-brand-1 opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all" />
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-retro-surface rounded-3xl p-6 shadow-glass border border-brand-1/10">
              <h3 className="text-lg font-bold text-text-main mb-4">Mentor Nex</h3>
              <div className="flex items-center gap-4 p-4 bg-brand-1/5 rounded-2xl border border-brand-1/10">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-1 to-brand-2 flex items-center justify-center text-white font-bold text-xl">
                  N
                </div>
                <div>
                  <p className="text-xs font-extrabold text-brand-1 uppercase tracking-widest">Always Online</p>
                  <p className="text-sm text-text-main font-bold">Ask me anything!</p>
                </div>
              </div>
              <button 
                onClick={() => setChatOpen(true)}
                className="w-full mt-4 py-3 rounded-xl bg-brand-1 text-white font-bold text-sm hover:scale-[1.02] active:scale-95 transition-all shadow-lg shadow-brand-1/20"
              >
                OPEN MENTOR CHAT
              </button>
            </div>
          </div>
        </div>

        {/* Interactive Activities */}
        <div className="bg-retro-surface rounded-xl p-8 shadow-card mb-8 border border-brand-1/20">
          <div className="flex items-center gap-3 mb-6">
            <Lightbulb className="w-6 h-6 text-brand-1" />
            <h2 className="text-2xl font-bold text-text-main">Interactive Activities</h2>
          </div>

          {/* Flash Cards */}
          {flashCards.length > 0 && (
            <div className="mb-12">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-text-main flex items-center gap-2">
                  <Star className="w-5 h-5 text-brand-1" />
                  Key Flashcards
                </h3>
                <span className="px-4 py-1.5 rounded-full bg-brand-1/10 text-brand-1 text-xs font-bold tracking-widest uppercase">
                  {currentFlashCard + 1} of {flashCards.length}
                </span>
              </div>

              <div className="relative group perspective-lg max-w-2xl mx-auto h-80">
                <div 
                  className={`relative w-full h-full cursor-pointer transition-all duration-700 preserve-3d ${flashCardRevealed ? 'rotate-y-180' : ''}`}
                  onClick={handleFlashCardFlip}
                >
                  {/* Front Side */}
                  <div className="absolute inset-0 backface-hidden bg-retro-surface rounded-[40px] p-10 border-2 border-brand-1/20 shadow-glass flex flex-col items-center justify-center text-center">
                    <p className="text-xs font-bold text-brand-1 uppercase tracking-[0.2em] mb-4">
                      {flashCards[currentFlashCard].theory_title || flashCards[currentFlashCard].topic || 'QUESTION'}
                    </p>
                    <h4 className="text-2xl font-bold text-text-main leading-tight">
                      {flashCards[currentFlashCard].topic || flashCards[currentFlashCard].question}
                    </h4>
                    <div className="mt-8 flex items-center gap-2 text-text-muted text-sm font-semibold opacity-60">
                      <span>Click to flip</span>
                      <Play className="w-3 h-3 fill-current" />
                    </div>
                  </div>

                  {/* Back Side */}
                  <div className="absolute inset-0 backface-hidden rotate-y-180 bg-gradient-to-br from-brand-1 to-brand-2 rounded-[40px] p-10 shadow-glass flex flex-col items-center justify-center text-center text-white">
                    <h4 className="text-sm font-bold opacity-80 uppercase tracking-widest mb-6 border-b border-white/20 pb-2">
                      Expert Answer
                    </h4>
                    <p className="text-lg font-medium leading-relaxed">
                      {flashCards[currentFlashCard].theory_content || flashCards[currentFlashCard].answer}
                    </p>
                    <div className="mt-8 px-4 py-2 rounded-full bg-white/20 backdrop-blur-sm text-xs font-bold flex items-center gap-2">
                      <Sparkles className="w-4 h-4" />
                      +{flashCards[currentFlashCard]?.reward?.xp || 25} XP EARNED
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-center gap-4 mt-8">
                <button
                  onClick={prevFlashCard}
                  disabled={currentFlashCard === 0}
                  className="w-12 h-12 rounded-full bg-retro-surface border border-brand-1/10 flex items-center justify-center text-text-muted hover:border-brand-1 hover:text-brand-1 transition-all disabled:opacity-30 disabled:cursor-not-allowed group"
                >
                  <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
                </button>
                <div className="flex gap-2">
                  {flashCards.map((_, idx) => (
                    <div 
                      key={idx} 
                      className={`w-2 h-2 rounded-full transition-all duration-300 ${idx === currentFlashCard ? 'w-8 bg-brand-1' : 'bg-brand-1/20'}`}
                    />
                  ))}
                </div>
                <button
                  onClick={nextFlashCard}
                  disabled={currentFlashCard === flashCards.length - 1}
                  className="w-12 h-12 rounded-full bg-retro-surface border border-brand-1/10 flex items-center justify-center text-text-muted hover:border-brand-1 hover:text-brand-1 transition-all disabled:opacity-30 disabled:cursor-not-allowed group"
                >
                  <ArrowLeft className="w-5 h-5 rotate-180 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </div>
          )}

          {/* MCQs */}
          {mcqs.length > 0 && (
            <div>
              <h3 className="text-lg font-bold text-text-main mb-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-brand-1" />
                Test Your Knowledge
              </h3>
              {mcqs.map((mcq, idx) => (
                <MCQItem 
                  key={mcq.id || idx} 
                  mcq={mcq} 
                  onSubmit={handleMCQSubmit}
                  courseId={courseId}
                  moduleId={moduleId}
                  progress={mcqProgress[mcq.id]}
                  onProgressUpdate={(progress) => {
                    setMcqProgress({ ...mcqProgress, [mcq.id]: progress })
                    checkModuleCompletion()
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Common Questions */}
        {module.fixed_qna && module.fixed_qna.length > 0 && (
          <div className="bg-retro-surface rounded-xl p-8 shadow-card mb-8 border border-brand-1/20">
            <div className="flex items-center gap-3 mb-6">
              <MessageCircle className="w-6 h-6 text-brand-1" />
              <h2 className="text-2xl font-bold text-text-main">Common Questions</h2>
            </div>
            <div className="space-y-4">
              {module.fixed_qna.map((qa, idx) => (
                <FAQItem key={idx} question={qa.q} answer={qa.a} />
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Chat Widget */}
      <ChatWidget
        open={chatOpen}
        onClose={() => setChatOpen(false)}
        messages={messages}
        chatInput={chatInput}
        setChatInput={setChatInput}
        onSend={handleSendMessage}
      />

      {/* Chat Toggle Button */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-brand-2 to-brand-1 text-white shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-180 z-50 flex items-center justify-center"
        aria-label="Open chat"
      >
        <MessageCircle className="w-6 h-6" />
      </button>
    </div>
  )
}

const MCQItem = ({ mcq, onSubmit, courseId, moduleId, progress, onProgressUpdate }) => {
  // Support both 'choices' and 'options' formats
  const choices = mcq.choices || mcq.options || []
  // Determine correct answer - support both formats
  const correctAnswer = mcq.correct_answer
  const correctChoiceIdx = mcq.correct_choice !== undefined 
    ? parseInt(mcq.correct_choice) 
    : (correctAnswer ? choices.findIndex(c => c === correctAnswer) : -1)
  
  // Initialize progress state from props or defaults
  const [selectedAnswer, setSelectedAnswer] = useState(null)
  const [currentProgress, setCurrentProgress] = useState(progress || { answered: false, correct: false, attempts: 0, allowRetry: true })
  const attempts = currentProgress?.attempts || 0
  const showResult = selectedAnswer !== null || (currentProgress?.answered && !currentProgress?.allowRetry)
  
  const handleClick = async (choiceIdx) => {
    if (showResult && !currentProgress?.allowRetry) return
    setSelectedAnswer(choiceIdx)
    const result = await onSubmit(mcq, choiceIdx)
    
    // Update progress
    const isCorrect = result?.isCorrect || (choiceIdx === correctChoiceIdx) || (result?.correct)
    const newProgress = {
      answered: true,
      correct: isCorrect,
      attempts: attempts + 1,
      allowRetry: !isCorrect // Allow retry if incorrect
    }
    setCurrentProgress(newProgress)
    onProgressUpdate?.(newProgress)
  }
  
  const handleRetry = () => {
    setSelectedAnswer(null)
    const newProgress = { ...currentProgress, answered: false, allowRetry: true }
    setCurrentProgress(newProgress)
    onProgressUpdate?.(newProgress)
  }
  
  // Update progress when prop changes
  useEffect(() => {
    if (progress) {
      setCurrentProgress(progress)
      if (progress.answered && progress.correct && correctChoiceIdx >= 0) {
        setSelectedAnswer(correctChoiceIdx) // Show correct answer if already answered correctly
      }
    }
  }, [progress, correctChoiceIdx])

  return (
    <div className="mb-6 bg-retro-surface rounded-xl p-6 border border-brand-1/20 shadow-card">
      <p className="text-lg font-semibold text-text-main mb-4">{mcq.question}</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {choices.map((choice, choiceIdx) => {
          const isSelected = selectedAnswer === choiceIdx
          const isCorrect = choiceIdx === correctChoiceIdx || choice === correctAnswer

          return (
            <button
              key={choiceIdx}
              onClick={() => handleClick(choiceIdx)}
              disabled={showResult}
              className={`p-4 rounded-xl border-2 font-medium text-left transition-all duration-180 ${
                showResult && isCorrect
                  ? 'bg-accent-green/10 border-accent-green text-accent-green'
                  : showResult && isSelected && !isCorrect
                  ? 'bg-accent-red/10 border-accent-red text-accent-red'
                  : isSelected
                  ? 'bg-brand-1/20 border-brand-1 text-text-main'
                  : 'bg-retro-surface border-brand-1/20 text-text-muted hover:border-brand-1/50 hover:text-text-main hover:bg-brand-1/5'
              } ${showResult ? 'cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {choice}
              {showResult && isCorrect && (
                <CheckCircle2 className="w-5 h-5 inline ml-2 text-accent-green" />
              )}
            </button>
          )
        })}
      </div>
      {showResult && (
        <div className="mt-4 p-4 rounded-lg animate-[fadeSlideUp_300ms_ease-out_forwards]">
          {/* Show AI feedback if available */}
          {mcq.ai_feedback && (
              <div className={`p-4 rounded-lg ${
              currentProgress?.correct
                ? 'bg-accent-green/10 border border-accent-green/30'
                : 'bg-accent-red/10 border border-accent-red/30'
            }`}>
              <p className={`text-sm font-medium ${
                currentProgress?.correct
                  ? 'text-accent-green'
                  : 'text-accent-red'
              }`}>
                {currentProgress?.correct
                  ? mcq.ai_feedback.correct || 'Correct! Well done!'
                  : mcq.ai_feedback.incorrect || 'Not quite. Keep learning!'}
              </p>
            </div>
          )}
          {/* Show explanation as fallback */}
          {!mcq.ai_feedback && mcq.explanation && (
            <div className="p-4 bg-retro-surface border border-brand-1/20 rounded-lg">
              <p className="text-sm text-text-main">
                <strong>Explanation:</strong> {mcq.explanation}
              </p>
            </div>
          )}
          {/* Retry button if incorrect */}
          {currentProgress?.allowRetry && !currentProgress?.correct && (
            <button
              onClick={handleRetry}
              className="mt-3 px-4 py-2 bg-brand-1 text-text-main rounded-lg hover:bg-brand-2 transition-colors"
            >
              Try Again (Attempt {currentProgress.attempts + 1})
            </button>
          )}
          {currentProgress?.correct && (
            <div className="mt-2 text-sm text-accent-green font-medium">
              ✓ Completed ({attempts} {attempts === 1 ? 'attempt' : 'attempts'})
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const FAQItem = ({ question, answer }) => {
  const [open, setOpen] = useState(false)

  return (
    <div className="border border-brand-1/30 bg-retro-bg rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-brand-1/5 transition-colors"
      >
        <span className="font-semibold text-text-main">{question}</span>
        {open ? (
          <ChevronUp className="w-5 h-5 text-text-muted flex-shrink-0 ml-4" />
        ) : (
          <ChevronDown className="w-5 h-5 text-text-muted flex-shrink-0 ml-4" />
        )}
      </button>
      {open && (
        <div className="p-4 pt-0 text-text-muted leading-relaxed animate-[fadeSlideUp_300ms_ease-out_forwards]">
          {answer}
        </div>
      )}
    </div>
  )
}

const ChatWidget = ({ open, onClose, messages, chatInput, setChatInput, onSend }) => {
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (open && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, open])

  if (!open) return null

  return (
    <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-retro-surface border border-brand-1/30 rounded-2xl shadow-modal z-50 flex flex-col overflow-hidden animate-[modalEnter_360ms_ease-out_forwards]">
      {/* Header */}
      <div className="bg-retro-bg text-text-main border-b border-brand-1/20 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-brand-1 rounded-full animate-pulse shadow-[0_0_8px_#4a7c59]"></div>
          <span className="font-bold text-text-main">Next</span>
          <span className="text-sm text-text-muted">AI Mentor</span>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full bg-brand-1/10 hover:bg-brand-1/20 transition-colors flex items-center justify-center"
          aria-label="Close chat"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-retro-bg">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-1/20 border border-brand-1/30 text-text-main'
                  : 'bg-retro-surface border border-brand-1/10 text-text-main shadow-sm'
              }`}
            >
              <p className="text-sm leading-relaxed">{msg.text}</p>
              <p className="text-xs opacity-70 mt-1">
                {msg.timestamp?.toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                }) || ''}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={onSend} className="p-4 border-t border-brand-1/20 bg-retro-surface">
        <div className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Type a command..."
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
  )
}

// Helper function for toast notifications
const showToast = (message, type = 'info') => {
  // Simple toast implementation
  const toast = document.createElement('div')
  toast.className = `fixed top-24 right-6 px-6 py-3 rounded-xl shadow-lg z-50 animate-[fadeSlideUp_300ms_ease-out_forwards] ${
    type === 'success' ? 'bg-green-500 text-text-main' : 'bg-retro-surface text-text-main'
  }`
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    toast.remove()
  }, 3000)
}

export default LessonDetail

