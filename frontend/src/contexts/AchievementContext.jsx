import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import api from '../utils/api'
import AchievementPopup from '../components/AchievementPopup'
import { useAuth } from './AuthContext'

const AchievementContext = createContext()

export const useAchievements = () => {
  const context = useContext(AchievementContext)
  if (!context) {
    throw new Error('useAchievements must be used within AchievementProvider')
  }
  return context
}

export const AchievementProvider = ({ children }) => {
  const { user } = useAuth()
  const [currentAchievement, setCurrentAchievement] = useState(null)
  const [notifiedAchievements, setNotifiedAchievements] = useState(new Set())

  const checkAchievements = useCallback(async () => {
    if (!user) return
    try {
      const response = await api.checkAchievements()
      if (response.data && response.data.newly_unlocked && response.data.newly_unlocked.length > 0) {
        
        const achievement = response.data.newly_unlocked[0]
        if (!notifiedAchievements.has(achievement.id)) {
          setCurrentAchievement(achievement)
        }
      }
    } catch (error) {
      console.error('Error checking achievements:', error)
    }
  }, [notifiedAchievements, user])

  useEffect(() => {
    if (!user) return

    checkAchievements()

    
    const interval = setInterval(checkAchievements, 15000)

    
    const handleImmediateCheck = () => checkAchievements()
    window.addEventListener('achievement-check', handleImmediateCheck)

    return () => {
      clearInterval(interval)
      window.removeEventListener('achievement-check', handleImmediateCheck)
    }
  }, [checkAchievements, user])

  const handleAchievementNotified = useCallback((achievementId) => {
    setNotifiedAchievements(prev => new Set([...prev, achievementId]))
    setCurrentAchievement(null)
  }, [])

  const closeAchievement = useCallback(() => {
    setCurrentAchievement(null)
  }, [])

  return (
    <AchievementContext.Provider value={{ checkAchievements }}>
      {children}
      {currentAchievement && (
        <AchievementPopup
          achievement={currentAchievement}
          onClose={closeAchievement}
          onNotified={handleAchievementNotified}
        />
      )}
    </AchievementContext.Provider>
  )
}

