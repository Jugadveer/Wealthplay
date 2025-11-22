from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.utils import timezone
from datetime import timedelta
from users.models import UserProfile, UserProgress


@require_http_methods(["GET"])
def home(request):
    """Home page - serve React app for all routes"""
    # Always serve React app - React Router will handle routing and auth checks
    # The React app will check authentication status client-side
    return render(request, 'react_app.html')


# Old Django dashboard removed - using React dashboard instead
# @login_required
# def dashboard(request):
#     """Dashboard for authenticated users - REMOVED: Using React dashboard"""
#     pass


@require_http_methods(["GET"])
def get_csrf_token(request):
    """API endpoint to get CSRF token for React frontend"""
    token = get_token(request)
    response = JsonResponse({'csrfToken': token})
    response.set_cookie('csrftoken', token, max_age=86400, samesite='Lax', secure=False)
    return response
