import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')

# Initialize Django first so model imports in routing/consumers are safe.
django_asgi_app = get_asgi_application()

import chat.routing
import market_data.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns + 
            market_data.routing.websocket_urlpatterns
        )
    ),
})
