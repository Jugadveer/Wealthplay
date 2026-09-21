from django.urls import path

from . import views

urlpatterns = [
    path('status/', views.ai_status, name='ai_status'),
    path('explain/', views.explain, name='ai_explain'),
    path('explain-number/', views.explain_number, name='ai_explain_number'),
    path('page-help/', views.page_help, name='ai_page_help'),
    path('search/', views.search_content, name='ai_search'),
]
