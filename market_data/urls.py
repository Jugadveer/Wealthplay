from django.urls import path

from . import cron, views

urlpatterns = [
    path('news/', views.market_news, name='market_news'),
    path('quotes/', views.market_quotes, name='market_quotes'),
    path('history/<str:symbol>/', views.market_history, name='market_history'),
    # Called by the platform scheduler where there is no Celery worker.
    path('cron/warm/', cron.warm, name='cron_warm'),
]
