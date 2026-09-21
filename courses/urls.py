from django.urls import path

from . import views

urlpatterns = [
    path('json/', views.list_courses, name='list_courses'),
    path('json/<str:course_id>/', views.course_detail, name='course_detail'),
    path('json/<str:course_id>/<str:module_id>/', views.module_detail, name='module_detail'),
    path('answer/', views.answer_question, name='answer_question'),
    path('complete/', views.complete_module, name='complete_module'),
]
