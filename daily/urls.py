from django.urls import path

from . import views

urlpatterns = [
    path('today/', views.today, name='daily_today'),
    path('ticker/', views.ticker_board, name='ticker_board'),
    path('ticker/search/', views.ticker_search, name='ticker_search'),
    path('ticker/guess/', views.ticker_guess, name='ticker_guess'),
    path('ledger/', views.ledger_board, name='ledger_board'),
    path('ledger/guess/', views.ledger_guess, name='ledger_guess'),
    path('call/', views.market_call, name='market_call'),
    path('rank/', views.rank_board, name='rank_board'),
    path('estimate/', views.number_sense, name='number_sense'),
    path('drill/', views.drill, name='daily_drill'),
    path('drill/answer/', views.drill_answer, name='daily_drill_answer'),
    path('streak/', views.streak, name='daily_streak'),
    path('recap/', views.recap, name='weekly_recap'),
]
