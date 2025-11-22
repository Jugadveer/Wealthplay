import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
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
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, beginner, intermediate, advanced

  useEffect(() => {
    loadCourses()
  }, [])

  // Reload courses when component comes into focus or when module is completed
  useEffect(() => {
    const handleFocus = () => {
      loadCourses()
    }
    const handleModuleCompleted = () => {
      loadCourses()
    }
    window.addEventListener('focus', handleFocus)
    window.addEventListener('module-completed', handleModuleCompleted)
    return () => {
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('module-completed', handleModuleCompleted)
    }
  }, [])

  const loadCourses = async () => {
    try {
      const response = await api.getCourses()
      // Handle different response formats
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
      beginner: 'bg-green-100 text-green-700',
      intermediate: 'bg-blue-100 text-blue-700',
      advanced: 'bg-purple-100 text-purple-700',
    }
    return levelMap[level?.toLowerCase()] || 'bg-gray-100 text-gray-700'
  }

  if (loading) {
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
          <div className="flex items-center gap-5 mb-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white/20 hover:bg-white/30 text-white px-5 py-2.5 rounded-full text-sm font-semibold shadow-md hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <ArrowRight className="w-4 h-4 rotate-180" />
              Back
            </button>
          </div>
          <h1 className="text-4xl font-bold mb-2">Financial Courses</h1>
          <p className="text-lg text-white/90">Learn at your own pace with interactive lessons</p>
        </div>
      </header>

      <main className="max-w-container mx-auto px-6 py-10 lg:px-10">
        {/* Filter Tabs */}
        <div className="mb-8 flex flex-wrap gap-4">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'all'
                ? 'bg-brand-1 text-white shadow-lg'
                : 'bg-white text-text-main border-2 border-muted-3 hover:border-brand-1'
            }`}
          >
            <Filter className="w-4 h-4 inline mr-2" />
            All Courses
          </button>
          <button
            onClick={() => setFilter('beginner')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'beginner'
                ? 'bg-green-600 text-white shadow-lg'
                : 'bg-white text-text-main border-2 border-muted-3 hover:border-green-600'
            }`}
          >
            Beginner
          </button>
          <button
            onClick={() => setFilter('intermediate')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'intermediate'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-text-main border-2 border-muted-3 hover:border-blue-600'
            }`}
          >
            Intermediate
          </button>
          <button
            onClick={() => setFilter('advanced')}
            className={`px-6 py-2.5 rounded-full font-semibold transition-all duration-180 ${
              filter === 'advanced'
                ? 'bg-purple-600 text-white shadow-lg'
                : 'bg-white text-text-main border-2 border-muted-3 hover:border-purple-600'
            }`}
          >
            Advanced
          </button>
        </div>

        {/* Courses Grid */}
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
                  className={`group bg-white rounded-xl p-6 shadow-card transition-all duration-360 border ${
                    isLocked || !canAccess
                      ? 'opacity-60 cursor-not-allowed border-muted-3'
                      : 'hover:shadow-card-hover hover:-translate-y-2 border-transparent hover:border-brand-1/20 cursor-pointer'
                  }`}
                  onClick={() => {
                    if (!isLocked && canAccess) {
                      navigate(`/course/${course.id}/m1`)
                    }
                  }}
                >
                  {/* Course Header */}
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
                          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-700 flex items-center gap-1">
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

                  {/* Course Stats */}
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

                  {/* Progress Bar */}
                  {totalModules > 0 && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-xs text-text-muted mb-1">
                        <span>Progress</span>
                        <span>
                          {completedModules} / {totalModules}
                        </span>
                      </div>
                      <div className="w-full h-2 bg-muted-2 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-brand-1 to-brand-2 rounded-full transition-all duration-500"
                          style={{ width: `${(completedModules / totalModules) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  )}

                  {/* CTA */}
                  <div className="flex items-center justify-between pt-4 border-t border-muted-2">
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


