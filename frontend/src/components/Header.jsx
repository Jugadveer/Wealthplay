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
        <div className={`bg-retro-surface/95 border border-brand-1/15 shadow-card text-text-main backdrop-blur-md rounded-[12px] px-6 py-3 flex items-center gap-8 text-sm font-semibold tracking-widest uppercase`}>
          {}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className={`md:hidden p-2 transition-all text-text-main hover:text-brand-1`}
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {}
          <div className={`hidden md:flex flex-row items-center gap-6 text-text-muted`}>
            <Link
              to={user ? "/dashboard" : "/"}
              className={`${isActive('/dashboard') ? 'text-brand-1 border-b-2 border-brand-1 pb-0.5' : 'text-text-muted hover:text-text-main'} transition-all`}
            >
              Home
            </Link>
            {user && (
              <>
                <Link
                  to="/course"
                  className={`${isActive('/course') ? 'text-brand-1 border-b-2 border-brand-1 pb-0.5' : 'text-text-muted hover:text-text-main'} transition-all`}
                >
                  Lessons
                </Link>
                <Link
                  to="/scenario"
                  className={`${isActive('/scenario') ? 'text-brand-1 border-b-2 border-brand-1 pb-0.5' : 'text-text-muted hover:text-text-main'} transition-all`}
                >
                  Simulator
                </Link>
                <Link
                  to="/portfolio"
                  className={`${isActive('/portfolio') ? 'text-brand-1 border-b-2 border-brand-1 pb-0.5' : 'text-text-muted hover:text-text-main'} transition-all`}
                >
                  Portfolio
                </Link>
                <Link
                  to="/achievements"
                  className={`${isActive('/achievements') ? 'text-brand-1 border-b-2 border-brand-1 pb-0.5' : 'text-text-muted hover:text-text-main'} transition-all`}
                >
                  Achievements
                </Link>
              </>
            )}
          </div>

          <div className={`flex items-center gap-4 pl-6 h-6 border-l border-muted-2`}>
            {user ? (
              <div className="group relative">
                <button
                  className={`flex items-center transition-all text-text-main hover:text-brand-1`}
                  aria-label="User menu"
                >
                  <User className="w-5 h-5" />
                </button>
                <div className={`absolute right-0 top-full mt-4 w-48 rounded-[12px] shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all bg-retro-surface border border-muted-2`}>
                  <div className={`px-4 py-3 border-b text-xs border-muted-2 text-text-muted`}>
                    Logged in as <span className={`text-text-main font-bold`}>{user.username}</span>
                  </div>
                  <button
                    onClick={logout}
                    className={`w-full text-left px-4 py-3 text-red-600 transition-all font-bold rounded-b-[12px] flex items-center gap-2 hover:bg-red-50 hover:text-red-700`}
                  >
                    <LogOut className="w-4 h-4" /> Logout
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-4 text-xs">
                <button
                  onClick={() => onAuthClick?.('login')}
                  className={`transition-all text-text-main hover:text-brand-1`}
                >
                  LOGIN
                </button>
                <button
                  onClick={() => onAuthClick?.('signup')}
                  className="bg-brand-1 text-white px-4 py-1.5 rounded-[12px] hover:bg-brand-2 transition-all shadow-md"
                >
                  SIGN UP
                </button>
              </div>
            )}
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

