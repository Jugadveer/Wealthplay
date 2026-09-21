from django.urls import path

from . import challenge_views
from .achievement_views import check_achievements, get_achievements, mark_achievement_notified
from .goals import views as goals
from .portfolio import analysis_views, instrument_views, social_views
from .portfolio import views as portfolio
from .simulation_views import get_sim_data, list_crises, start_session
from .views import award_xp, get_user_profile, save_onboarding

urlpatterns = [
    # Account
    path('onboarding/', save_onboarding, name='save_onboarding'),
    path('profile/', get_user_profile, name='get_user_profile'),
    path('award-xp/', award_xp, name='award_xp'),

    # Goals
    path('goals/', goals.list_goals, name='list_goals'),
    path('goals/assess/', goals.assess_goal, name='assess_goal'),
    path('goals/plan/', goals.preview_plan, name='preview_goal_plan'),
    path('goals/create/', goals.create_goal, name='create_goal'),
    path('goals/<int:goal_id>/update/', goals.update_goal, name='update_goal'),
    path('goals/<int:goal_id>/delete/', goals.delete_goal, name='delete_goal'),
    path('goals/<int:goal_id>/link/', goals.link_goal, name='link_goal'),
    path('goals/contribution/', goals.set_contribution, name='set_contribution'),
    path('goals/contribution/pay/', goals.pay_contribution, name='pay_contribution'),

    # Portfolio
    path('portfolio/', portfolio.get_portfolio, name='get_portfolio'),
    path('portfolio/analysis/', analysis_views.get_portfolio_analysis, name='get_portfolio_analysis'),
    path('portfolio/history/', portfolio.get_portfolio_history, name='get_portfolio_history'),
    path('portfolio/tickers-info/', portfolio.get_tickers_info, name='get_tickers_info'),
    path('portfolio/stocks/', portfolio.get_stocks, name='get_stocks'),
    path('portfolio/stocks/<str:symbol>/', portfolio.get_stock_detail, name='get_stock_detail'),
    path('portfolio/instruments/', instrument_views.list_instruments, name='list_instruments'),
    path('portfolio/deposits/open/', instrument_views.open_deposit, name='open_deposit'),
    path('portfolio/deposits/<int:deposit_id>/close/', instrument_views.close_deposit, name='close_deposit'),
    path('portfolio/sips/start/', instrument_views.start_sip, name='start_sip'),
    path('portfolio/sips/<int:sip_id>/stop/', instrument_views.stop_sip, name='stop_sip'),
    path('portfolio/sips/run/', instrument_views.run_sips, name='run_sips'),
    path('portfolio/buy/', portfolio.buy_stock, name='buy_stock'),
    path('portfolio/sell/', portfolio.sell_stock, name='sell_stock'),
    path('portfolio/critique/', analysis_views.critique_trade_idea, name='critique_trade_idea'),
    path('portfolio/hindsight/', analysis_views.get_hindsight_replay, name='get_hindsight_replay'),
    path('portfolio/copy-trading/', social_views.get_copy_trading_hub, name='get_copy_trading_hub'),
    path('portfolio/copy-trading/follow/', social_views.follow_copy_trader, name='follow_copy_trader'),
    path('portfolio/copy-trading/post/', social_views.post_trade_rationale, name='post_trade_rationale'),

    # Challenges
    path('challenges/leaderboard/', challenge_views.get_leaderboard, name='get_leaderboard'),
    path('challenges/stats/', challenge_views.get_user_challenge_stats, name='get_user_challenge_stats'),
    path('challenges/calibration/', challenge_views.get_calibration, name='get_calibration'),
    path('challenges/question/', challenge_views.get_random_stock_question, name='get_random_stock_question'),
    path('challenges/hint/', challenge_views.get_prediction_hint, name='get_prediction_hint'),
    path('challenges/predict/', challenge_views.submit_stock_prediction, name='submit_stock_prediction'),

    # Achievements
    path('achievements/', get_achievements, name='get_achievements'),
    path('achievements/check/', check_achievements, name='check_achievements'),
    path('achievements/notify/', mark_achievement_notified, name='mark_achievement_notified'),

    # Time capsule
    path('time-capsule/crises/', list_crises, name='list_crises'),
    path('time-capsule/start/<int:crisis_id>/', start_session, name='start_session'),
    path('time-capsule/sim-data/<int:session_id>/', get_sim_data, name='get_sim_data'),

]
