from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import Http404
from .views import home, get_csrf_token

urlpatterns = [
    path('admin', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', admin.site.urls),
    path('api/csrf-token/', get_csrf_token, name='get_csrf_token'),
    path('api/auth/', include('users.auth_urls')),
    path('api/courses/', include('courses.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/market/', include('market_data.urls')),
    path('api/users/', include('users.urls')),
    path('api/scenario/', include('simulator.urls')),
    path('api/daily/', include('daily.urls')),
    path('api/ai/', include('ai.urls')),
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    # Every route the API does not claim renders the built single-page app,
    # so a deep link like /markets/analysis survives a refresh.
    re_path(r'^(?!admin|static|media).*$', home, name='react_app'),
]
