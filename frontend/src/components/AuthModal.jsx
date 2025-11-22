import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { X, User, Mail, Lock, LogIn, UserPlus } from 'lucide-react'

const AuthModal = ({ mode, onClose, onSwitch }) => {
  const { login, signup } = useAuth()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
  })
  const firstInputRef = useRef(null)

  // Debug: Log when modal opens
  useEffect(() => {
    if (mode) {
      console.log('AuthModal rendered with mode:', mode)
    }
  }, [mode])

  useEffect(() => {
    if (firstInputRef.current && mode) {
      setTimeout(() => firstInputRef.current?.focus(), 100)
    }
  }, [mode])

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [onClose])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    // Debug: Log form data
    console.log('Form submit - mode:', mode)
    console.log('Form data:', {
      username: formData.username,
      email: formData.email,
      password: formData.password ? '***' : 'empty',
      password2: formData.password2 ? '***' : 'empty',
    })

    try {
      let result
      if (mode === 'login') {
        if (!formData.username || !formData.password) {
          setError('Please fill in all fields')
          setLoading(false)
          return
        }
        result = await login(formData.username, formData.password)
      } else {
        if (!formData.username || !formData.email || !formData.password || !formData.password2) {
          setError('Please fill in all fields')
          setLoading(false)
          return
        }
        result = await signup(
          formData.username,
          formData.email,
          formData.password,
          formData.password2
        )
      }

      if (result.success) {
        onClose()
        
        // Wait a moment for auth state to update, then navigate
        setTimeout(() => {
          if (result.needsOnboarding) {
            window.location.href = '/onboarding'
          } else {
            window.location.href = result.redirect || '/dashboard'
          }
        }, 300)
      } else {
        setError(result.error || 'An error occurred')
      }
    } catch (err) {
      console.error('Auth error:', err)
      setError(
        err.response?.data?.error ||
        err.message ||
        'An unexpected error occurred. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => {
      const newData = {
        ...prev,
        [name]: value,
      }
      // Debug: Log form data changes
      if (name === 'username' || name === 'email') {
        console.log(`Form field changed - ${name}:`, value)
      }
      return newData
    })
    setError('')
  }

  // Ensure modal is visible when component renders
  if (!mode) return null

  return (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/35 backdrop-blur-sm"
      style={{ 
        opacity: 1, 
        pointerEvents: 'auto',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby={mode === 'login' ? 'login-title' : 'signup-title'}
    >
      <div
        className="relative w-full max-w-md bg-white rounded-xl shadow-modal"
        style={{
          transform: 'scale(1)',
          opacity: 1,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-full bg-muted-2 text-text-muted hover:bg-muted-3 hover:text-brand-1 transition-all duration-180 hover:rotate-90"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="px-8 pt-8 pb-6">
          <h2
            id={mode === 'login' ? 'login-title' : 'signup-title'}
            className="text-2xl font-bold text-brand-1"
          >
            {mode === 'login' ? 'Login to WealthPlay' : 'Create Your Account'}
          </h2>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-8 pb-8">
          {/* Username */}
          <div className="mb-5">
            <label htmlFor="username" className="block text-sm font-medium text-text-main mb-1.5">
              Username
            </label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              <input
                ref={firstInputRef}
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                required
                autoComplete="username"
                className="w-full pl-10 pr-4 py-3 border-2 border-muted-3 rounded-lg focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all duration-180"
                aria-required="true"
              />
            </div>
          </div>

          {/* Email (Signup only) */}
          {mode === 'signup' && (
            <div className="mb-5">
              <label htmlFor="email" className="block text-sm font-medium text-text-main mb-1.5">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-3 border-2 border-muted-3 rounded-lg focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all duration-180"
                  aria-required="true"
                />
              </div>
            </div>
          )}

          {/* Password */}
          <div className="mb-5">
            <label htmlFor="password" className="block text-sm font-medium text-text-main mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                minLength={mode === 'signup' ? 6 : undefined}
                className="w-full pl-10 pr-4 py-3 border-2 border-muted-3 rounded-lg focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all duration-180"
                aria-required="true"
              />
            </div>
          </div>

          {/* Confirm Password (Signup only) */}
          {mode === 'signup' && (
            <div className="mb-5">
              <label
                htmlFor="password2"
                className="block text-sm font-medium text-text-main mb-1.5"
              >
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  type="password"
                  id="password2"
                  name="password2"
                  value={formData.password2}
                  onChange={handleChange}
                  required
                  autoComplete="new-password"
                  className="w-full pl-10 pr-4 py-3 border-2 border-muted-3 rounded-lg focus:border-brand-1 focus:ring-4 focus:ring-brand-1/10 outline-none transition-all duration-180"
                  aria-required="true"
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div
              className="mb-5 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600"
              role="alert"
              aria-live="polite"
            >
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-6 rounded-full bg-gradient-to-r from-brand-1 to-brand-2 text-white font-semibold hover:shadow-lg hover:shadow-brand-1/30 hover:-translate-y-0.5 active:scale-95 transition-all duration-180 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : mode === 'login' ? (
              <>
                <LogIn className="w-5 h-5" />
                Login
              </>
            ) : (
              <>
                <UserPlus className="w-5 h-5" />
                Sign Up
              </>
            )}
          </button>

          {/* Switch Mode */}
          <p className="mt-6 text-center text-sm text-text-muted">
            {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
            <button
              type="button"
              onClick={onSwitch}
              className="text-brand-1 font-semibold hover:text-brand-2 transition-colors"
            >
              {mode === 'login' ? 'Sign Up' : 'Login'}
            </button>
          </p>
        </form>
      </div>
    </div>
  )
}

export default AuthModal

