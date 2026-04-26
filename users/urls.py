from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserProgressViewSet, QuizAttemptViewSet, save_onboarding, get_user_profile
from .goals_views import goals_page, create_goal, update_goal, delete_goal, get_goals_api
from .views import award_xp
from .progress_views import flashcard_flip, get_flashcard_progress, get_mcq_progress, get_module_progress, complete_module, mcq_answer
from .portfolio_views import (
    get_portfolio, get_stocks, get_stock_detail, buy_stock, sell_stock,
    get_portfolio_history, get_ai_recommendation, get_proactive_mentor_nudge,
    get_portfolio_esg, get_hindsight_replay, get_copy_trading_hub,
    follow_copy_trader, post_trade_rationale, get_tickers_info
)
from .challenge_views import get_leaderboard, get_user_challenge_stats, submit_stock_prediction, get_random_stock_question
from .achievement_views import get_achievements, check_achievements, mark_achievement_notified
from .simulation_views import list_crises, start_session, get_sim_data

router = DefaultRouter()
# Note: progress endpoints are handled manually below, not via router
router.register(r'quiz-attempts', QuizAttemptViewSet, basename='quiz-attempt')

urlpatterns = [
    # Progress tracking endpoints - MUST come before router to avoid conflicts
    path('progress/flashcards/flip/', flashcard_flip, name='flashcard_flip'),
    path('progress/flashcards/', get_flashcard_progress, name='get_flashcard_progress'),
    path('progress/mcqs/answer/', mcq_answer, name='mcq_answer'),
    path('progress/mcqs/', get_mcq_progress, name='get_mcq_progress'),
    path('progress/module/complete/', complete_module, name='complete_module'),
    path('progress/module/', get_module_progress, name='get_module_progress'),
    # Other endpoints
    path('onboarding/', save_onboarding, name='save_onboarding'),
    path('profile/', get_user_profile, name='get_user_profile'),
    path('goals/', goals_page, name='goals'),
    path('goals/api/', get_goals_api, name='get_goals_api'),
    path('goals/api/create/', create_goal, name='create_goal'),
    path('goals/api/<int:goal_id>/update/', update_goal, name='update_goal'),
    path('goals/api/<int:goal_id>/delete/', delete_goal, name='delete_goal'),
    path('award-xp/', award_xp, name='award_xp'),
    # Portfolio endpoints
    path('portfolio/', get_portfolio, name='get_portfolio'),
    path('portfolio/tickers-info/', get_tickers_info, name='get_tickers_info'),
    path('portfolio/history/', get_portfolio_history, name='get_portfolio_history'),
    path('portfolio/stocks/', get_stocks, name='get_stocks'),
    path('portfolio/stocks/<str:symbol>/', get_stock_detail, name='get_stock_detail'),
    path('portfolio/buy/', buy_stock, name='buy_stock'),
    path('portfolio/sell/', sell_stock, name='sell_stock'),
    path('portfolio/ai-recommendation/', get_ai_recommendation, name='get_ai_recommendation'),
    path('portfolio/proactive-mentor/', get_proactive_mentor_nudge, name='get_proactive_mentor_nudge'),
    path('portfolio/esg/', get_portfolio_esg, name='get_portfolio_esg'),
    path('portfolio/hindsight-replay/', get_hindsight_replay, name='get_hindsight_replay'),
    path('portfolio/copy-trading/', get_copy_trading_hub, name='get_copy_trading_hub'),
    path('portfolio/copy-trading/follow/', follow_copy_trader, name='follow_copy_trader'),
    path('portfolio/copy-trading/post/', post_trade_rationale, name='post_trade_rationale'),
    # Challenge endpoints
    path('challenges/leaderboard/', get_leaderboard, name='get_leaderboard'),
    path('challenges/stats/', get_user_challenge_stats, name='get_user_challenge_stats'),
    path('challenges/question/', get_random_stock_question, name='get_random_stock_question'),
    path('challenges/predict/', submit_stock_prediction, name='submit_stock_prediction'),
    # Achievement endpoints
    path('achievements/', get_achievements, name='get_achievements'),
    path('achievements/check/', check_achievements, name='check_achievements'),
    path('achievements/notify/', mark_achievement_notified, name='mark_achievement_notified'),
    # Time Capsule endpoints
    path('time-capsule/crises/', list_crises, name='list_crises'),
    path('time-capsule/start/<int:crisis_id>/', start_session, name='start_session'),
    path('time-capsule/sim-data/<int:session_id>/', get_sim_data, name='get_sim_data'),
    # Router URLs (must come last)
    path('', include(router.urls)),
]




