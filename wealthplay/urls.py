from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.http import Http404
from .views import home, get_csrf_token
# Old Django dashboard removed - using React dashboard instead
# from .views import dashboard
from users.goals_views import goals_page

def react_app_view(request):
    """Serve React app for all routes except admin, static, and media"""
    # The regex pattern already excludes admin, static, and media paths
    return TemplateView.as_view(template_name='react_app.html')(request)

urlpatterns = [
    # Redirect /admin to /admin/ (with trailing slash) - must come before catch-all
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', admin.site.urls),
    path('api/csrf-token/', get_csrf_token, name='get_csrf_token'),  # CSRF token endpoint for React
    path('api/courses/', include('courses.urls')),  # API endpoints
    path('api/chat/', include('chat.urls')),
    path('api/users/', include('users.urls')),
    path('api/uploads/', include('uploads.urls')),
    path('api/cursor/', include('cursor.urls')),
    path('api/scenario/', include('simulator.urls')),  # Scenario API endpoints
    # Landing page route - serve React app
    path('', home, name='home'),
]

# Add static and media file serving BEFORE the catch-all route
# This ensures admin static files are served correctly
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Catch-all route: serve React app for all other routes (dashboard, course, scenario, etc.)
# Exclude admin, static, and media paths using regex negative lookahead
# This must be last so all other routes (including static files) are matched first
urlpatterns += [
    re_path(r'^(?!admin|static|media).*$', react_app_view, name='react_app'),
]
