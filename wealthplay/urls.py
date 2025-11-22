from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .views import home, get_csrf_token
# Old Django dashboard removed - using React dashboard instead
# from .views import dashboard
from users.goals_views import goals_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/csrf-token/', get_csrf_token, name='get_csrf_token'),  # CSRF token endpoint for React
    path('api/courses/', include('courses.urls')),  # API endpoints
    path('api/chat/', include('chat.urls')),
    path('api/users/', include('users.urls')),
    path('api/uploads/', include('uploads.urls')),
    path('api/cursor/', include('cursor.urls')),
    # Django-specific routes that should be served by Django templates
    path('goals/', goals_page, name='goals'),  # Goals page (Django template)
    path('onboarding/', TemplateView.as_view(template_name='onboarding.html'), name='onboarding'),  # Old Django onboarding (deprecated)
    # Landing page route - serve React app
    path('', home, name='home'),
    # Catch-all route: serve React app for all other routes (dashboard, course, scenario, etc.)
    # This must be last so all other routes are matched first
    # Using re_path with .* pattern to match all remaining paths
    path('<path:path>', TemplateView.as_view(template_name='react_app.html'), name='react_app'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
