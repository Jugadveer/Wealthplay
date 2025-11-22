import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import Header from './Header'
import AuthModal from './AuthModal'

const Layout = ({ children, showNav = true }) => {
  const { user } = useAuth()
  const [authModal, setAuthModal] = useState(null) // 'login' or 'signup'

  // Listen for custom events to open modals from anywhere
  useEffect(() => {
    const handleOpenAuthModal = (event) => {
      const mode = event.detail || 'signup' // Default to signup
      console.log('Opening auth modal:', mode)
      setAuthModal(mode)
    }

    window.addEventListener('openAuthModal', handleOpenAuthModal)
    return () => window.removeEventListener('openAuthModal', handleOpenAuthModal)
  }, [])

  // Debug: Log when modal state changes
  useEffect(() => {
    if (authModal) {
      console.log('Auth modal is now:', authModal)
    }
  }, [authModal])

  // Ensure CSRF token is available on mount
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

  return (
    <div className="min-h-screen bg-muted-1">
      {showNav && <Header onAuthClick={setAuthModal} />}
      
      <main>{children}</main>

      {/* Auth Modals */}
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

