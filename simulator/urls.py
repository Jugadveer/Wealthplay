from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # API endpoints for React frontend
    path('api/start/', api_views.start_quiz_api, name='start_quiz_api'),
    path('api/quiz/<int:run_id>/', api_views.get_quiz_question, name='get_quiz_question'),
    path('api/quiz/<int:run_id>/next/', api_views.next_question_api, name='next_question_api'),
    path('api/quiz/<int:run_id>/result/', api_views.get_quiz_result, name='get_quiz_result'),
    path('api/submit-answer/', api_views.submit_answer_api, name='submit_answer_api'),
]