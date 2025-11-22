import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../utils/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const response = await api.getProfile()
      if (response.status === 200 && response.data) {
        setUser(response.data)
      } else {
        setUser(null)
      }
    } catch (error) {
      // 401 or 403 is expected for non-authenticated users, don't log it
      if (error.response?.status !== 401 && error.response?.status !== 403) {
        console.error('Auth check error:', error)
      }
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      console.log('Login attempt with:', { username, password: '***' })
      
      // Validate inputs
      if (!username || !username.trim()) {
        return { success: false, error: 'Username is required' }
      }
      if (!password) {
        return { success: false, error: 'Password is required' }
      }

      const { axios } = await import('../utils/api')
      
      // Get CSRF token first
      const csrfToken = await getCsrfToken()
      console.log('CSRF token:', csrfToken ? 'found' : 'missing')
      
      // Create FormData
      const formDataObj = new FormData()
      formDataObj.append('username', username.trim())
      formDataObj.append('password', password)
      
      const response = await axios.post('/api/courses/auth/login/', formDataObj, {
        headers: {
          'X-CSRFToken': csrfToken || '',
          // Don't set Content-Type - let axios set it with boundary for FormData
        },
        withCredentials: true,
      })
      
      console.log('Login response:', response.data)

      if (response.data && response.data.success) {
        await checkAuth()
        // Login users always go to dashboard - onboarding is only for signups
        return { 
          success: true,
          needsOnboarding: false
        }
      } else {
        return {
          success: false,
          error: response.data?.error || 'Login failed. Please check your credentials.',
        }
      }
    } catch (error) {
      console.error('Login error:', error)
      const errorMessage =
        error.response?.data?.error ||
        error.response?.data?.message ||
        error.message ||
        'Login failed. Please check your credentials.'
      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  const signup = async (username, email, password, password2) => {
    try {
      console.log('Signup attempt with:', { username, email, password: '***', password2: '***' })
      
      // Validate inputs
      if (!username || !username.trim()) {
        return { success: false, error: 'Username is required' }
      }
      if (username.trim().length < 3) {
        return { success: false, error: 'Username must be at least 3 characters' }
      }
      if (!email || !email.trim()) {
        return { success: false, error: 'Email is required' }
      }
      if (!password) {
        return { success: false, error: 'Password is required' }
      }
      if (password.length < 6) {
        return { success: false, error: 'Password must be at least 6 characters' }
      }
      if (password !== password2) {
        return { success: false, error: 'Passwords do not match.' }
      }

      const { axios } = await import('../utils/api')
      
      // Get CSRF token first
      const csrfToken = await getCsrfToken()
      console.log('CSRF token:', csrfToken ? 'found' : 'missing')
      
      // Create FormData
      const formDataObj = new FormData()
      formDataObj.append('username', username.trim())
      formDataObj.append('email', email.trim())
      formDataObj.append('password', password)
      formDataObj.append('password2', password2)
      
      // Log FormData contents for debugging
      for (let [key, value] of formDataObj.entries()) {
        console.log(`FormData ${key}:`, key === 'password' || key === 'password2' ? '***' : value)
      }
      
      const response = await axios.post('/api/courses/auth/signup/', formDataObj, {
        headers: {
          'X-CSRFToken': csrfToken || '',
          // Don't set Content-Type - let axios set it with boundary for FormData
        },
        withCredentials: true,
      })
      
      console.log('Signup response:', response.data)

      if (response.data && response.data.success) {
        // Check if onboarding is needed
        if (response.data.needs_onboarding) {
          // Signal that onboarding should be shown (can be handled by parent component)
          console.log('User needs onboarding')
        }
        await checkAuth()
        return { success: true, needsOnboarding: response.data.needs_onboarding }
      } else {
        return {
          success: false,
          error: response.data?.error || 'Signup failed. Please try again.',
        }
      }
    } catch (error) {
      console.error('Signup error:', error)
      const errorMessage =
        error.response?.data?.error ||
        error.response?.data?.message ||
        error.message ||
        'Signup failed. Please try again.'
      return {
        success: false,
        error: errorMessage,
      }
    }
  }

  const logout = async () => {
    try {
      const { axios } = await import('../utils/api')
      const csrfToken = await getCsrfToken()
      
      await axios.post(
        '/api/courses/auth/logout/',
        {},
        {
          headers: {
            'X-CSRFToken': csrfToken,
          },
          withCredentials: true,
        }
      )
    } catch (error) {
      console.error('Logout error:', error)
      // Continue with logout even if request fails
    }
    
    // Clear user state after API call
    setUser(null)
    
    // Force a full page reload to clear all React state and session
    // Use replace with timestamp to prevent redirect loops
    window.location.replace('/?' + Date.now())
  }

  const getCsrfToken = async () => {
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
      const { axios } = await import('../utils/api')
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

  const value = {
    user,
    loading,
    login,
    signup,
    logout,
    checkAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

