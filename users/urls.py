from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProgressViewSet, QuizAttemptViewSet, save_onboarding, get_user_profile
from .goals_views import goals_page, create_goal, update_goal, delete_goal, get_goals_api
from .views import award_xp

router = DefaultRouter()
router.register(r'progress', UserProgressViewSet, basename='progress')
router.register(r'quiz-attempts', QuizAttemptViewSet, basename='quiz-attempt')

urlpatterns = [
    path('', include(router.urls)),
    path('onboarding/', save_onboarding, name='save_onboarding'),
    path('profile/', get_user_profile, name='get_user_profile'),
    path('goals/', goals_page, name='goals'),
    path('goals/api/', get_goals_api, name='get_goals_api'),
    path('goals/api/create/', create_goal, name='create_goal'),
    path('goals/api/<int:goal_id>/update/', update_goal, name='update_goal'),
    path('goals/api/<int:goal_id>/delete/', delete_goal, name='delete_goal'),
    path('award-xp/', award_xp, name='award_xp'),
]




