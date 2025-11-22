import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api, { axios } from '../utils/api'
import {
  ArrowLeft,
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
  const [flippedFlashCards, setFlippedFlashCards] = useState(new Set()) // Track flipped cards
  const [mcqs, setMcqs] = useState([])
  const [mcqProgress, setMcqProgress] = useState({}) // Track MCQ answers: {mcqId: {answered: true, correct: bool, attempts: number}}
  const [moduleProgress, setModuleProgress] = useState(null) // Overall module progress

  useEffect(() => {
    loadModule()
  }, [courseId, moduleId])

  const loadModule = async () => {
    try {
      setLoading(true)
      // Load course detail first
      const courseResponse = await api.getCourse(courseId)
      setCourse(courseResponse.data)

      // Load module detail
      const moduleResponse = await api.getModule(courseId, moduleId)
      const moduleData = moduleResponse.data.module || moduleResponse.data

      setModule(moduleData)
      // Set MCQs from module data - support both formats
      const mcqsData = moduleData.mcqs || []
      setMcqs(mcqsData)
      
      // Load flash cards if available
      if (moduleData.flash_cards && moduleData.flash_cards.length > 0) {
        // Transform flash cards to expected format
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
        
        // Load user progress for flashcards
        loadFlashCardProgress(courseId, moduleId)
      } else {
        // Try to load from flash-cards endpoint
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
      
      // Load module progress
      loadModuleProgress(courseId, moduleId)
      // Load MCQ progress
      loadMCQProgress(courseId, moduleId)
    } catch (error) {
      console.error('Error loading module:', error)
    } finally {
      setLoading(false)
    }
  }

  // Load flashcard progress from API
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

  // Load MCQ progress from API
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

  // Load overall module progress
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

  // Handle flashcard flip and award XP
  const handleFlashCardFlip = async () => {
    if (flashCardRevealed) return // Already flipped
    
    const currentCard = flashCards[currentFlashCard]
    if (!currentCard) return
    
    // Check if already flipped to prevent duplicate XP
    const cardId = currentCard.id || currentCard.topic || `card-${currentFlashCard}`
    if (flippedFlashCards.has(cardId)) {
      setFlashCardRevealed(true)
      return
    }
    
    setFlashCardRevealed(true)
    
    // Award XP for flipping
    try {
      const response = await axios.post(
        `/api/users/progress/flashcards/flip/`,
        {
          course_id: courseId,
          module_id: moduleId,
          flashcard_id: cardId
        }
      )
      
      if (response.data.xp_awarded && response.data.xp_awarded > 0) {
        showToast('+' + response.data.xp_awarded + ' XP earned!', 'success')
        setFlippedFlashCards(new Set([...flippedFlashCards, cardId]))
        
        // Update module progress immediately
        setModuleProgress(prev => ({
          ...prev,
          flashcards_flipped: (prev?.flashcards_flipped || 0) + 1
        }))
        
        // Reload module progress from API to get accurate count
        await loadModuleProgress(courseId, moduleId)
        
        // Check if module is complete
        checkModuleCompletion()
      }
    } catch (error) {
      console.error('Error recording flashcard flip:', error)
      // Still mark as flipped locally
      setFlippedFlashCards(new Set([...flippedFlashCards, cardId]))
      // Update local progress even on error
      setModuleProgress(prev => ({
        ...prev,
        flashcards_flipped: (prev?.flashcards_flipped || 0) + 1
      }))
    }
  }

  // Check and update module completion status
  const checkModuleCompletion = async () => {
    const allFlashcardsFlipped = flashCards.length > 0 && 
      flashCards.every(card => {
        const cardId = card.id || card.topic || `card-${flashCards.indexOf(card)}`
        return flippedFlashCards.has(cardId)
      })
    
    const allMcqsAnswered = mcqs.length > 0 && 
      mcqs.every(mcq => mcqProgress[mcq.id]?.answered && mcqProgress[mcq.id]?.correct)
    
    // Only mark complete if there are activities and all are done
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
          // Reload page progress to update display with latest data
          await loadModuleProgress(courseId, moduleId)
          // Also update local state immediately
          setModuleProgress(prev => ({
            ...prev,
            status: 'completed',
            progress_percent: 100,
            xp_awarded: response.data.xp_awarded || (prev?.xp_awarded || 0)
          }))
          
          // Trigger a storage event to notify CourseHome to reload
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
    
    // Check if answer is correct
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
        // Show XP notification only (feedback is already shown in MCQItem component)
        if (response.data.xp_awarded && response.data.xp_awarded > 0) {
          showToast('+' + response.data.xp_awarded + ' XP earned!', 'success')
        }
        
        // Update MCQ progress
        setMcqProgress(prev => ({
          ...prev,
          [mcq.id]: {
            answered: true,
            correct: true,
            attempts: (prev[mcq.id]?.attempts || 0) + 1,
            allowRetry: false
          }
        }))
        
        // Update module progress immediately - count correct MCQs
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
          mcqs_completed: correctMcqsCount
        }))
        
        // Reload module progress from API to get accurate count
        await loadModuleProgress(courseId, moduleId)
        
        // Check if module is complete
        checkModuleCompletion()
      } else {
        // Update progress even for incorrect answers
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
      
      // Return response for MCQItem to use
      return { ...response.data, isCorrect }
    } catch (error) {
      console.error('Error submitting MCQ:', error)
      // Return error for MCQItem to handle
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
    <div className="min-h-screen bg-muted-1">
      {/* Header */}
      <header className="bg-gradient-to-r from-brand-1 to-brand-2 text-white shadow-lg px-6 py-8 lg:px-10">
        <div className="max-w-container mx-auto">
          <button
            onClick={() => navigate('/course')}
            className="mb-4 bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-4xl font-bold mb-2">{module.title}</h1>
          <p className="text-lg text-white/90">{module.summary}</p>
          {/* Module Progress Indicator */}
          {moduleProgress && (
            <div className="mt-4 bg-white/20 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-white">
                  {moduleProgress.status === 'completed' ? '✓ Module Completed' : 'Module Progress'}
                </span>
                <span className="text-sm text-white/90">
                  {Math.max(moduleProgress.flashcards_flipped || 0, flippedFlashCards.size)} / {flashCards.length} flashcards • {Math.max(moduleProgress.mcqs_completed || 0, Object.values(mcqProgress).filter(m => m.correct).length)} / {mcqs.length} MCQs
                </span>
              </div>
              <div className="w-full h-2 bg-white/30 rounded-full overflow-hidden">
                <div
                  className="h-full bg-white rounded-full transition-all duration-500"
                  style={{ width: `${moduleProgress.progress_percent || 0}%` }}
                ></div>
              </div>
              {moduleProgress.status === 'completed' && (
                <p className="text-sm text-white/90 mt-2">
                  🎉 You've completed this module! +{moduleProgress.xp_awarded || 0} XP earned
                </p>
              )}
            </div>
          )}
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Lesson Content */}
        <div className="bg-white rounded-xl p-8 shadow-card mb-8">
          <div className="flex items-center gap-3 mb-6">
            <FileText className="w-6 h-6 text-brand-1" />
            <h2 className="text-2xl font-bold text-text-main">Lesson Content</h2>
          </div>

          <p className="text-text-muted leading-relaxed mb-6">
            {module.theory_text || module.summary || 'Learn key concepts through interactive content.'}
          </p>

          {/* Action Buttons */}
          <div className="flex gap-4 mb-8">
            <button
              onClick={() => setOverviewOpen(!overviewOpen)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl border-2 border-brand-1 bg-white text-brand-1 font-semibold hover:bg-brand-1 hover:text-white transition-all duration-180 active:scale-95"
            >
              <Info className="w-5 h-5" />
              Overview
            </button>
            <button
              onClick={() => setExplainOpen(!explainOpen)}
              className="flex items-center gap-2 px-6 py-3 rounded-xl border-2 border-brand-1 bg-white text-brand-1 font-semibold hover:bg-brand-1 hover:text-white transition-all duration-180 active:scale-95"
            >
              <FileText className="w-5 h-5" />
              Explain
            </button>
          </div>

          {/* Overview/Explain Widgets */}
          {(overviewOpen || explainOpen) && (
            <div className="mb-8 p-6 bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl border-2 border-brand-1/20 animate-[modalEnter_360ms_ease-out_forwards]">
              <button
                onClick={() => {
                  setOverviewOpen(false)
                  setExplainOpen(false)
                }}
                className="float-right text-text-muted hover:text-text-main"
              >
                <X className="w-5 h-5" />
              </button>
              <h3 className="text-lg font-bold text-text-main mb-3">
                {overviewOpen ? 'Overview' : 'Explanation'}
              </h3>
              <p className="text-text-muted leading-relaxed">
                {overviewOpen
                  ? module.summary || 'Overview of key concepts in this module.'
                  : module.theory_text || module.summary || 'Detailed explanation of the concepts.'}
              </p>
            </div>
          )}
        </div>

        {/* Interactive Activities */}
        <div className="bg-white rounded-xl p-8 shadow-card mb-8">
          <div className="flex items-center gap-3 mb-6">
            <Lightbulb className="w-6 h-6 text-brand-1" />
            <h2 className="text-2xl font-bold text-text-main">Interactive Activities</h2>
          </div>

          {/* Flash Cards */}
          {flashCards.length > 0 && (
            <div className="mb-8">
              <div className="bg-gradient-to-br from-brand-1/10 to-brand-2/10 rounded-xl p-6 border-2 border-brand-1/20">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-text-main flex items-center gap-2">
                    <Star className="w-5 h-5 text-brand-1" />
                    Flash Cards
                    <span className="text-sm font-normal text-text-muted">
                      ({currentFlashCard + 1} / {flashCards.length})
                    </span>
                  </h3>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-brand-1">
                      +{flashCards[currentFlashCard]?.reward?.xp || 25} XP
                    </span>
                  </div>
                </div>

                {flashCards[currentFlashCard] && (
                  <div className="relative min-h-[200px]">
                    <div
                      className={`bg-white rounded-xl p-8 shadow-lg cursor-pointer transform transition-all duration-360 ${
                        flashCardRevealed ? 'rotateY-180' : ''
                      }`}
                      onClick={handleFlashCardFlip}
                      style={{ transformStyle: 'preserve-3d' }}
                    >
                      {!flashCardRevealed ? (
                        <div className="text-center">
                          <p className="text-sm text-text-muted mb-2">{flashCards[currentFlashCard].theory_title || flashCards[currentFlashCard].topic || 'Topic'}</p>
                          <p className="text-xl font-bold text-text-main mb-4">
                            {flashCards[currentFlashCard].topic || flashCards[currentFlashCard].question || 'Tap to reveal answer'}
                          </p>
                          <p className="text-sm text-text-muted">Click to flip</p>
                        </div>
                      ) : (
                        <div className="text-center">
                          <p className="text-lg font-semibold text-text-main mb-4">
                            {flashCards[currentFlashCard].theory_title || flashCards[currentFlashCard].topic}
                          </p>
                          <p className="text-base text-text-muted leading-relaxed">
                            {flashCards[currentFlashCard].theory_content || flashCards[currentFlashCard].answer}
                          </p>
                          {flashCards[currentFlashCard] && flippedFlashCards.has(flashCards[currentFlashCard].id) && (
                            <p className="text-sm text-green-600 mt-4">✓ Earned +{flashCards[currentFlashCard]?.reward?.xp || 25} XP</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between mt-6">
                  <button
                    onClick={prevFlashCard}
                    disabled={currentFlashCard === 0}
                    className="px-4 py-2 rounded-lg bg-white border-2 border-muted-3 text-text-main font-semibold hover:border-brand-1 hover:text-brand-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={nextFlashCard}
                    disabled={currentFlashCard === flashCards.length - 1}
                    className="px-4 py-2 rounded-lg bg-brand-1 text-white font-semibold hover:bg-brand-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
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
          <div className="bg-white rounded-xl p-8 shadow-card mb-8">
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
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-accent-green to-teal-600 text-white shadow-lg hover:shadow-xl hover:scale-110 transition-all duration-180 z-50 flex items-center justify-center"
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
    <div className="mb-6 bg-muted-1 rounded-xl p-6">
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
                  ? 'bg-green-100 border-green-500 text-green-700'
                  : showResult && isSelected && !isCorrect
                  ? 'bg-red-100 border-red-500 text-red-700'
                  : isSelected
                  ? 'bg-brand-1/10 border-brand-1 text-brand-1'
                  : 'bg-white border-muted-3 text-text-main hover:border-brand-1/50'
              } ${showResult ? 'cursor-not-allowed' : 'cursor-pointer'}`}
            >
              {choice}
              {showResult && isCorrect && (
                <CheckCircle2 className="w-5 h-5 inline ml-2 text-green-600" />
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
                ? 'bg-green-50 border border-green-200'
                : 'bg-red-50 border border-red-200'
            }`}>
              <p className={`text-sm font-medium ${
                currentProgress?.correct
                  ? 'text-green-800'
                  : 'text-red-800'
              }`}>
                {currentProgress?.correct
                  ? mcq.ai_feedback.correct || 'Correct! Well done!'
                  : mcq.ai_feedback.incorrect || 'Not quite. Keep learning!'}
              </p>
            </div>
          )}
          {/* Show explanation as fallback */}
          {!mcq.ai_feedback && mcq.explanation && (
            <div className="p-4 bg-brand-1/10 rounded-lg">
              <p className="text-sm text-text-muted">
                <strong>Explanation:</strong> {mcq.explanation}
              </p>
            </div>
          )}
          {/* Retry button if incorrect */}
          {currentProgress?.allowRetry && !currentProgress?.correct && (
            <button
              onClick={handleRetry}
              className="mt-3 px-4 py-2 bg-brand-1 text-white rounded-lg hover:bg-brand-2 transition-colors"
            >
              Try Again (Attempt {currentProgress.attempts + 1})
            </button>
          )}
          {currentProgress?.correct && (
            <div className="mt-2 text-sm text-green-600 font-medium">
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
    <div className="border-l-4 border-brand-1 bg-muted-1 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-muted-2 transition-colors"
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
    <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-modal z-50 flex flex-col overflow-hidden animate-[modalEnter_360ms_ease-out_forwards]">
      {/* Header */}
      <div className="bg-gradient-to-r from-accent-green to-teal-600 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
          <span className="font-bold">Nex</span>
          <span className="text-sm opacity-90">Your AI mentor</span>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full bg-white/20 hover:bg-white/30 transition-colors flex items-center justify-center"
          aria-label="Close chat"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-muted-1">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-brand-1 text-white'
                  : 'bg-white text-text-main shadow-sm'
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
      <form onSubmit={onSend} className="p-4 border-t border-muted-2 bg-white">
        <div className="flex gap-2">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Type a question..."
            className="flex-1 px-4 py-3 rounded-xl border-2 border-muted-3 focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all"
          />
          <button
            type="submit"
            className="px-4 py-3 rounded-xl bg-brand-1 text-white hover:bg-brand-2 transition-all active:scale-95"
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
    type === 'success' ? 'bg-green-500 text-white' : 'bg-white text-text-main'
  }`
  toast.textContent = message
  document.body.appendChild(toast)
  setTimeout(() => {
    toast.remove()
  }, 3000)
}

export default LessonDetail

