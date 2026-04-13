from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from django.http import Http404
from .views import home, get_csrf_token
from users.goals_views import goals_page

def react_app_view(request):
    return TemplateView.as_view(template_name='react_app.html')(request)

urlpatterns = [
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', admin.site.urls),
    path('api/csrf-token/', get_csrf_token, name='get_csrf_token'),
    path('api/courses/', include('courses.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/market/', include('market_data.urls')),
    path('api/users/', include('users.urls')),
    path('api/uploads/', include('uploads.urls')),
    path('api/cursor/', include('cursor.urls')),
    path('api/scenario/', include('simulator.urls')),
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    re_path(r'^(?!admin|static|media).*$', react_app_view, name='react_app'),
]
