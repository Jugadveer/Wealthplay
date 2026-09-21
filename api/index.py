"""
Serverless entry point.

Vercel treats every file under `api/` as a function and calls the module-level
`app`. One function serves the whole site: the API, the admin, and the React
shell that the catch-all route in `wealthplay/urls.py` renders. WhiteNoise, which
is already in the middleware stack, serves the built assets from inside the same
bundle, so there is no second origin and no CORS between the page and its API.

WSGI rather than ASGI on purpose. There are no WebSocket routes — see
`wealthplay/asgi.py` — and a serverless function cannot hold a socket open
anyway, so the ASGI stack would be 80 MB of dependencies against a 250 MB
function limit in exchange for nothing.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wealthplay.settings')

app = get_wsgi_application()

# Vercel's Python runtime looks for `app`; some versions look for `handler`.
handler = app
