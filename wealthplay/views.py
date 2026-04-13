from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token


@require_http_methods(["GET"])
def home(request):
    return render(request, 'react_app.html')


@require_http_methods(["GET"])
def get_csrf_token(request):
    token = get_token(request)
    response = JsonResponse({'csrfToken': token})
    response.set_cookie('csrftoken', token, max_age=86400, samesite='Lax', secure=False)
    return response
