import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Hexagon, LogOut, Menu, Home, BookOpen, Target, User, TrendingUp, X } from 'lucide-react'

const Header = ({ onAuthClick }) => {
  const { user, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <>
      <header className="sticky top-0 z-50 bg-gradient-to-r from-brand-1 to-brand-2 text-white shadow-lg">
        <div className="max-w-container mx-auto px-6 lg:px-10">
          <div className="flex items-center justify-between h-[70px]">
            {/* Logo */}
            <Link
              to={user ? "/dashboard" : "/"}
              className="flex items-center gap-2 text-xl font-bold hover:scale-105 transition-transform group"
            >
              <div className="relative">
                <Hexagon className="w-8 h-8 group-hover:rotate-180 transition-transform duration-500" />
              </div>
              <span>WealthPlay</span>
            </Link>

            {/* Navigation Links - Only for authenticated users */}
            {user && (
              <nav className="hidden md:flex items-center gap-1">
                <Link
                  to="/dashboard"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    isActive('/dashboard') 
                      ? 'bg-white/20 text-white shadow-md' 
                      : 'text-white/90 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Home className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                <Link
                  to="/course"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    isActive('/course') 
                      ? 'bg-white/20 text-white shadow-md' 
                      : 'text-white/90 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Courses</span>
                </Link>
                <Link
                  to="/scenario"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    isActive('/scenario') 
                      ? 'bg-white/20 text-white shadow-md' 
                      : 'text-white/90 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Target className="w-4 h-4" />
                  <span>Scenarios</span>
                </Link>
                <Link
                  to="/portfolio"
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    isActive('/portfolio') 
                      ? 'bg-white/20 text-white shadow-md' 
                      : 'text-white/90 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <TrendingUp className="w-4 h-4" />
                  <span>Portfolio</span>
                </Link>
              </nav>
            )}

            {/* Auth Buttons */}
            <div className="flex items-center gap-3">
              {user ? (
                <div className="flex items-center gap-3">
                  <Link
                    to="/dashboard"
                    className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 transition-all duration-200"
                  >
                    <User className="w-4 h-4" />
                    <span className="font-medium">{user.username}</span>
                  </Link>
                  <button
                    onClick={logout}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/20 border border-white/30 hover:bg-white/30 transition-all duration-200 active:scale-95"
                    aria-label="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="hidden sm:inline">Logout</span>
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => onAuthClick?.('login')}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white text-brand-1 font-semibold hover:bg-gray-100 transition-all duration-200 active:scale-95 shadow-sm"
                  >
                    <User className="w-4 h-4" />
                    <span>Login</span>
                  </button>
                  <button
                    onClick={() => onAuthClick?.('signup')}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-transparent border-2 border-white text-white font-semibold hover:bg-white/10 transition-all duration-200 active:scale-95"
                  >
                    Sign Up
                  </button>
                </div>
              )}
              {/* Mobile menu button */}
              {user && (
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 hover:bg-white/20 rounded-lg transition-all"
                  aria-label="Toggle menu"
                >
                  {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                </button>
              )}
            </div>
          </div>
        </div>
        {/* Gradient line */}
        <div className="h-0.5 bg-gradient-to-r from-transparent via-white/50 to-transparent"></div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && user && (
        <div className="md:hidden bg-white border-b shadow-lg animate-slideDown">
          <nav className="max-w-container mx-auto px-6 py-4 flex flex-col gap-2">
            <Link
              to="/dashboard"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                isActive('/dashboard')
                  ? 'bg-brand-1/10 text-brand-1'
                  : 'text-text-main hover:bg-muted-1'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <Home className="w-5 h-5" />
              <span>Dashboard</span>
            </Link>
            <Link
              to="/course"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                isActive('/course')
                  ? 'bg-brand-1/10 text-brand-1'
                  : 'text-text-main hover:bg-muted-1'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <BookOpen className="w-5 h-5" />
              <span>Courses</span>
            </Link>
            <Link
              to="/scenario"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                isActive('/scenario')
                  ? 'bg-brand-1/10 text-brand-1'
                  : 'text-text-main hover:bg-muted-1'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <Target className="w-5 h-5" />
              <span>Scenarios</span>
            </Link>
            <Link
              to="/portfolio"
              className={`flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-colors ${
                isActive('/portfolio')
                  ? 'bg-brand-1/10 text-brand-1'
                  : 'text-text-main hover:bg-muted-1'
              }`}
              onClick={() => setMobileMenuOpen(false)}
            >
              <TrendingUp className="w-5 h-5" />
              <span>Portfolio</span>
            </Link>
            <div className="border-t border-muted-2 mt-2 pt-2">
              <Link
                to="/dashboard"
                className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-muted hover:bg-muted-1"
                onClick={() => setMobileMenuOpen(false)}
              >
                <User className="w-5 h-5" />
                <span>{user.username}</span>
              </Link>
              <button
                onClick={() => {
                  setMobileMenuOpen(false)
                  logout()
                }}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 font-medium"
              >
                <LogOut className="w-5 h-5" />
                <span>Logout</span>
              </button>
            </div>
          </nav>
        </div>
      )}
    </>
  )
}

export default Header

