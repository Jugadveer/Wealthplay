from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, TopicViewSet, LessonViewSet, MentorPersonaViewSet,
    course_home, course_detail, lesson_detail,
    login_view, signup_view, logout_view,
    get_courses_with_progress, start_lesson, complete_lesson
)
from .course_views import get_courses, get_course_detail, get_module_detail, submit_mcq_answer, get_plaque_card_content, submit_plaque_card_answer, get_all_flash_cards

# API routes (for /api/courses/)
router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'lessons', LessonViewSet, basename='lesson')
router.register(r'mentors', MentorPersonaViewSet, basename='mentor')

urlpatterns = [
    # JSON-based course API routes (MUST come before router to avoid conflicts)
    path('json/', get_courses, name='get_courses_json'),
    path('json/<str:course_id>/', get_course_detail, name='get_course_json'),
    path('json/<str:course_id>/<str:module_id>/', get_module_detail, name='get_module_json'),
    
    # Enriched module content API routes
    path('api/module/<str:module_id>/mcq/<str:mcq_id>/answer/', submit_mcq_answer, name='submit_mcq_answer'),
    path('api/module/<str:module_id>/flash-cards/', get_all_flash_cards, name='get_all_flash_cards'),
    path('api/module/<str:module_id>/plaque-card/', get_plaque_card_content, name='get_plaque_card_content'),
    path('api/module/<str:module_id>/plaque-card/answer/', submit_plaque_card_answer, name='submit_plaque_card_answer'),
    
    # Progress API routes
    path('api/with-progress/', get_courses_with_progress, name='get_courses_with_progress'),
    path('api/<str:course_id>/<str:module_id>/start/', start_lesson, name='start_lesson'),
    path('api/<str:course_id>/<str:module_id>/complete/', complete_lesson, name='complete_lesson'),
    
    # Auth routes
    path('auth/login/', login_view, name='login'),
    path('auth/signup/', signup_view, name='signup'),
    path('auth/logout/', logout_view, name='logout'),
    
    # Page routes (for /course/)
    path('', course_home, name='course_home'),
    path('<str:course_id>/', course_detail, name='course_detail'),
    path('<str:course_id>/<str:module_id>/', lesson_detail, name='lesson_detail'),
    
    # API routes (for /api/courses/) - DRF router (comes last)
    path('', include(router.urls)),
]
