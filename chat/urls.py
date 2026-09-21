from django.urls import path

from . import views

urlpatterns = [
    path('mentor/ask/', views.ask_mentor, name='ask_mentor'),
    path('mentor/history/<str:course_id>/', views.mentor_history, name='mentor_history'),
    path('mentor/history/<str:course_id>/<str:module_id>/', views.mentor_history, name='mentor_history_module'),
]
