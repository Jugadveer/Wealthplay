import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useGlobalData } from '../contexts/GlobalDataContext'
import api from '../utils/api'
import {
  BookOpen,
  Clock,
  TrendingUp,
  Lock,
  CheckCircle2,
  PlayCircle,
  ArrowRight,
  Filter,
} from 'lucide-react'

const CourseHome = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { courses: cachedCourses, refreshCourses, loadingCourses } = useGlobalData()
  const [courses, setCourses] = useState(() => cachedCourses || [])
  const [loading, setLoading] = useState(!(cachedCourses && cachedCourses.length > 0))
  const [filter, setFilter] = useState('all') 

  // Sync local state with global cache when cache changes
  useEffect(() => {
    if (cachedCourses && cachedCourses.length > 0) {
      setCourses(cachedCourses)
      setLoading(false)
    }
  }, [cachedCourses])

  // Initial load only if empty
  useEffect(() => {
    if (!cachedCourses || cachedCourses.length === 0) {
      loadCourses(false)
    }
  }, [])

  
  useEffect(() => {
    const handleFocus = () => {
      loadCourses(true)
    }
    const handleModuleCompleted = () => {
      loadCourses(true)
    }
    window.addEventListener('focus', handleFocus)
    window.addEventListener('module-completed', handleModuleCompleted)
    return () => {
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('module-completed', handleModuleCompleted)
    }
  }, [])

  const loadCourses = async (force = true) => {
    try {
      const cached = typeof refreshCourses === 'function'
        ? await refreshCourses(force)
        : null

      if (Array.isArray(cached)) {
        setCourses(cached)
        return
      }

      const response = await api.getCourses()
      const coursesData = Array.isArray(response.data) ? response.data : response.data.courses || []
      setCourses(coursesData)
    } catch (error) {
      console.error('Error loading courses:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredCourses = courses.filter((course) => {
    if (filter === 'all') return true
    return course.level?.toLowerCase() === filter.toLowerCase()
  })

  const getLevelColor = (level) => {
    const levelMap = {
      beginner: 'bg-[#FFEDD5] text-[#FF6B35]',
      intermediate: 'bg-[#E0E7FF] text-[#4338CA]',
      advanced: 'bg-brand-2/15 text-brand-2',
    }
    return levelMap[level?.toLowerCase()] || 'bg-muted-2/40 text-text-muted'
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-retro-bg">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-1"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-retro-bg text-text-main">
      {}
      <header className="bg-retro-surface border-b border-brand-1/20 shadow-lg px-6 py-8 lg:px-10 mt-20">
        <div className="max-w-container mx-auto">
          <div className="flex items-center gap-5 mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-brand-1/10 hover:bg-brand-1/20 border border-brand-1/30 text-brand-1 px-5 py-2.5 rounded-full text-sm font-semibold shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowRight className="w-4 h-4 rotate-180" />
              Back
            </button>
          </div>
          <h1 className="text-4xl font-bold mb-2">Financial Courses</h1>
          <p className="text-lg text-text-muted">Learn at your own pace with interactive lessons</p>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {}
        <div className="mb-8 flex flex-wrap gap-4">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'all'
                ? 'bg-retro-surface text-brand-1 border border-brand-1/40 shadow-sm'
                : 'bg-retro-surface text-text-muted border border-brand-1/30 hover:border-brand-1'
            }`}
          >
            <Filter className="w-4 h-4 inline mr-2" />
            All Courses
          </button>
          <button
            onClick={() => setFilter('beginner')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'beginner'
                ? 'bg-accent-green/15 text-accent-green border border-accent-green/30 shadow-sm'
                : 'bg-retro-surface text-text-muted border border-brand-1/30 hover:border-accent-green hover:text-accent-green'
            }`}
          >
            Beginner
          </button>
          <button
            onClick={() => setFilter('intermediate')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'intermediate'
                ? 'bg-accent-blue/15 text-accent-blue border border-accent-blue/30 shadow-sm'
                : 'bg-retro-surface text-text-muted border border-brand-1/30 hover:border-accent-blue hover:text-accent-blue'
            }`}
          >
            Intermediate
          </button>
          <button
            onClick={() => setFilter('advanced')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'advanced'
                ? 'bg-brand-2/15 text-brand-2 border border-brand-2/30 shadow-sm'
                : 'bg-retro-surface text-text-muted border border-brand-1/30 hover:border-brand-2 hover:text-brand-2'
            }`}
          >
            Advanced
          </button>
        </div>

        {}
        {filteredCourses.length === 0 ? (
          <div className="text-center py-12">
            <BookOpen className="w-16 h-16 mx-auto mb-4 text-muted-3" />
            <h3 className="text-xl font-semibold text-text-main mb-2">No courses found</h3>
            <p className="text-text-muted">Try selecting a different filter</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course) => {
              const totalModules = course.total_modules || course.modules?.length || 0
              const completedModules = course.completed_modules || 0
              const isLocked = course.locked || false
              const canAccess = course.user_can_access !== false

              return (
                <div
                  key={course.id}
                  className={`group relative bg-retro-surface rounded-xl p-6 shadow-card transition-all duration-360 border ${
                    isLocked || !canAccess
                      ? 'opacity-60 cursor-not-allowed border-brand-1/10'
                      : 'hover:shadow-card-hover hover:-translate-y-2 border-brand-1/20 hover:border-brand-1 cursor-pointer'
                  }`}
                  onClick={() => {
                    if (!isLocked && canAccess) {
                      navigate(`/course/${course.id}/m1`)
                    }
                  }}
                >
                  {(isLocked || !canAccess) && (
                    <div className="absolute inset-0 bg-retro-bg/70 rounded-xl flex items-center justify-center">
                      <div className="w-12 h-12 rounded-full bg-retro-surface border border-muted-2 flex items-center justify-center">
                        <Lock className="w-5 h-5 text-muted-3" />
                      </div>
                    </div>
                  )}
                  {}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold capitalize ${getLevelColor(
                            course.level
                          )}`}
                        >
                          {course.level || 'Beginner'}
                        </span>
                        {isLocked && (
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-accent-red/15 text-accent-red flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            Locked
                          </span>
                        )}
                      </div>
                      <h3 className="text-xl font-bold text-text-main mb-2 group-hover:text-brand-1 transition-colors">
                        {course.title}
                      </h3>
                      <p className="text-sm text-text-muted line-clamp-2">{course.overview}</p>
                    </div>
                  </div>

                  {}
                  <div className="flex items-center gap-4 mb-4 text-sm text-text-muted">
                    <div className="flex items-center gap-1">
                      <BookOpen className="w-4 h-4" />
                      <span>{totalModules} modules</span>
                    </div>
                    {course.duration_min && (
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{course.duration_min} min</span>
                      </div>
                    )}
                  </div>

                  {}
                  {totalModules > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                        <span>Progress</span>
                        <span>
                          {completedModules} / {totalModules}
                        </span>
                      </div>
                      <div className="w-full h-2 bg-retro-board rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full transition-all duration-500"
                          style={{
                            width: `${(completedModules / totalModules) * 100}%`,
                            backgroundColor: completedModules === totalModules ? '#f59e0b' : '#ff6b35',
                          }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {}
                  <div className="flex items-center justify-between pt-4 border-t border-brand-1/10">
                    {isLocked ? (
                      <span className="text-sm font-semibold text-text-muted">
                        Complete prerequisites to unlock
                      </span>
                    ) : (
                      <>
                        <span className="text-sm font-semibold text-brand-1 group-hover:underline">
                          {completedModules > 0 ? 'Continue Learning' : 'Start Learning'}
                        </span>
                        <ArrowRight className="w-5 h-5 text-brand-1 group-hover:translate-x-1 transition-transform" />
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}

export default CourseHome


