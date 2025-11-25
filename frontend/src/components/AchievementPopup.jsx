import { useEffect, useState } from 'react'
import { X, Trophy, Sparkles, Flame, TrendingUp, Target, BarChart3, Award, Briefcase, Zap, Shield, BookOpen, CheckCircle2, Sun } from 'lucide-react'
import api from '../utils/api'

const iconMap = {
  trophy: Trophy,
  sparkles: Sparkles,
  flame: Flame,
  'trending-up': TrendingUp,
  target: Target,
  'bar-chart-3': BarChart3,
  award: Award,
  briefcase: Briefcase,
  zap: Zap,
  shield: Shield,
  'book-open': BookOpen,
  'check-circle-2': CheckCircle2,
  sun: Sun,
}

const AchievementPopup = ({ achievement, onClose, onNotified }) => {
  const [show, setShow] = useState(true)

  useEffect(() => {
    // Auto-close after 5 seconds
    const timer = setTimeout(() => {
      handleClose()
    }, 5000)

    return () => clearTimeout(timer)
  }, [])

  const handleClose = async () => {
    setShow(false)
    // Mark as notified
    if (achievement.id && onNotified) {
      try {
        await api.markAchievementNotified(achievement.id)
        onNotified(achievement.id)
      } catch (error) {
        console.error('Error marking achievement as notified:', error)
      }
    }
    setTimeout(() => {
      onClose()
    }, 300)
  }

  const Icon = iconMap[achievement.icon_name] || Trophy

  if (!show) return null

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
      <div className="bg-white rounded-xl shadow-2xl border-2 border-orange-200 p-6 max-w-sm animate-bounce-in">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-400 to-orange-600 flex items-center justify-center flex-shrink-0">
            <Icon className="w-8 h-8 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-bold text-text-main">Achievement Unlocked!</h3>
              <button
                onClick={handleClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xl font-semibold text-brand-1 mb-1">{achievement.name}</p>
            <p className="text-sm text-text-muted mb-3">{achievement.description}</p>
            {achievement.xp_reward > 0 && (
              <div className="flex items-center gap-2 text-accent-green">
                <Sparkles className="w-4 h-4" />
                <span className="text-sm font-semibold">+{achievement.xp_reward} XP</span>
              </div>
            )}
          </div>
        </div>
      </div>
      <style jsx>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes bounce-in {
          0% {
            transform: scale(0.8);
            opacity: 0;
          }
          50% {
            transform: scale(1.05);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
        .animate-bounce-in {
          animation: bounce-in 0.5s ease-out;
        }
      `}</style>
    </div>
  )
}

export default AchievementPopup

