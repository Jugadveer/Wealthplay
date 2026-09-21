from django.urls import path

from . import views

urlpatterns = [
    path('news/', views.market_news, name='market_news'),
    path('quotes/', views.market_quotes, name='market_quotes'),
    path('history/<str:symbol>/', views.market_history, name='market_history'),
]
