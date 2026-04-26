import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Hexagon, LogOut, Menu, User, X } from 'lucide-react'

const Header = ({ onAuthClick }) => {
  const { user, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const isDashboardRoute = location.pathname === '/dashboard' || location.pathname.startsWith('/dashboard/')

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')

  return (
    <>
      <header className="fixed top-6 left-0 right-0 z-50 flex justify-center px-4">
        <div className="bg-retro-surface/90 border border-brand-1/15 shadow-glass text-text-main backdrop-blur-lg rounded-2xl px-2 py-2 flex items-center gap-1 text-[11px] font-bold tracking-widest uppercase">
          <Link
            to={user ? "/dashboard" : "/"}
            className="flex items-center gap-2 px-4 py-2 hover:bg-brand-1/5 rounded-xl transition-all group"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-1 to-brand-2 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <Hexagon className="w-5 h-5 text-white" />
            </div>
          </Link>

          <div className="hidden md:flex flex-row items-center gap-1">
            {user && (
              <>
                <Link
                  to="/course"
                  className={`px-4 py-2.5 rounded-xl transition-all ${isActive('/course') ? 'bg-brand-1/10 text-brand-1 shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
                >
                  Lessons
                </Link>
                <Link
                  to="/scenario"
                  className={`px-4 py-2.5 rounded-xl transition-all ${isActive('/scenario') ? 'bg-brand-1/10 text-brand-1 shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
                >
                  Simulator
                </Link>
                <Link
                  to="/portfolio"
                  className={`px-4 py-2.5 rounded-xl transition-all ${isActive('/portfolio') ? 'bg-brand-1/10 text-brand-1 shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
                >
                  Portfolio
                </Link>
                <Link
                  to="/achievements"
                  className={`px-4 py-2.5 rounded-xl transition-all ${isActive('/achievements') ? 'bg-brand-1/10 text-brand-1 shadow-sm' : 'text-text-muted hover:text-text-main hover:bg-brand-1/5'}`}
                >
                  Achievements
                </Link>
              </>
            )}
          </div>

          <div className="flex items-center gap-2 ml-2 pl-2 border-l border-brand-1/10 min-h-[32px]">
            {user ? (
              <div className="group relative">
                <button
                  className="flex items-center gap-2 px-3 py-2 hover:bg-brand-1/5 rounded-xl transition-all text-text-main"
                  aria-label="User menu"
                >
                  <div className="w-8 h-8 rounded-full bg-brand-1/10 border border-brand-1/20 flex items-center justify-center">
                    <User className="w-4 h-4 text-brand-1" />
                  </div>
                  <span className="hidden lg:inline-block normal-case tracking-normal">{user.username}</span>
                </button>
                <div className="absolute right-0 top-full mt-3 w-56 rounded-2xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible translate-y-2 group-hover:translate-y-0 transition-all duration-200 bg-retro-surface border border-brand-1/15 backdrop-blur-xl p-2 z-[60]">
                  <div className="px-4 py-3 border-b border-brand-1/10 text-xs text-text-muted mb-1">
                    Logged in as <span className="text-text-main font-bold">{user.username}</span>
                  </div>
                  <button
                    onClick={logout}
                    className="w-full text-left px-4 py-3 text-red-500 hover:bg-red-500/10 transition-all font-bold rounded-xl flex items-center gap-3 overflow-hidden group/logout"
                  >
                    <LogOut className="w-4 h-4 group-hover/logout:-translate-x-1 transition-transform" /> 
                    <span>Log out</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs">
                <button
                  onClick={() => onAuthClick?.('login')}
                  className="px-4 py-2.5 text-text-main hover:text-brand-1 rounded-xl transition-all font-bold"
                >
                  LOGIN
                </button>
                <button
                  onClick={() => onAuthClick?.('signup')}
                  className="bg-brand-1 text-white px-5 py-2.5 rounded-xl hover:bg-brand-2 transition-all shadow-glow font-bold"
                >
                  JOIN
                </button>
              </div>
            )}
            
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden w-10 h-10 flex items-center justify-center hover:bg-brand-1/5 rounded-xl transition-all text-text-main ml-1"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {}
      {mobileMenuOpen && (
        <div className={`fixed inset-0 z-40 flex flex-col items-center justify-center gap-8 uppercase tracking-widest font-bold text-lg animate-fade-in bg-retro-bg/98 text-text-main`}>
          <Link
            to={user ? "/dashboard" : "/"}
            className={`${isActive('/dashboard') ? 'text-brand-1' : 'text-text-muted hover:text-text-main'}`}
            onClick={() => setMobileMenuOpen(false)}
          >
            Home
          </Link>
          {user && (
            <>
              <Link
                to="/course"
                className={`${isActive('/course') ? 'text-brand-1' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Lessons
              </Link>
              <Link
                to="/scenario"
                className={`${isActive('/scenario') ? 'text-brand-1' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Simulator
              </Link>
              <Link
                to="/portfolio"
                className={`${isActive('/portfolio') ? 'text-brand-1' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Portfolio
              </Link>
              <Link
                to="/achievements"
                className={`${isActive('/achievements') ? 'text-brand-1' : 'text-text-muted hover:text-text-main'}`}
                onClick={() => setMobileMenuOpen(false)}
              >
                Achievements
              </Link>
              
              <button
                onClick={() => {
                  setMobileMenuOpen(false)
                  logout()
                }}
                className="text-red-300 hover:text-red-200 mt-8"
              >
                Logout
              </button>
            </>
          )}
        </div>
      )}
    </>
  )
}

export default Header

