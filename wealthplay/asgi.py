"""
ASGI entry point.

Served by Daphne. There are no WebSocket routes: the app had two consumers for a
live chat and a market feed, neither of which the client ever connected to. The
mentor is a plain request/response endpoint and quotes come from a cached REST
call, so nothing needs a socket.

Channels stays configured because the deployment target runs ASGI, and adding a
socket later should not mean changing the server.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')

application = get_asgi_application()
