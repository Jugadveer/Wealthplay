from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='scenario_home'),
    path('start/', views.start_quiz, name='start_quiz'),
    path('quiz/<int:run_id>/', views.play_quiz_question, name='play_quiz_question'),
    path('quiz/<int:run_id>/next/', views.next_question, name='next_question'),
    path('quiz/<int:run_id>/result/', views.quiz_result, name='quiz_result'),
    path('api/submit-answer/', views.submit_quiz_answer, name='submit_answer'),
]