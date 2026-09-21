"""
The two views that are not part of any app: the page itself, and the CSRF token.

Serving the page is less trivial than it looks. Django used to render
`templates/react_app.html`, a leftover from `npm create vite` that pointed at
`/src/main.jsx` and titled the tab "WealthPlay - Financial Learning Platform".
That file only resolves through the Vite dev server, so every deployment served
a page whose only script tag was a 404 — and nothing caught it, because in
development the browser talks to Vite directly and Django's copy is never
rendered.

What is served now is the real build output, `static/react/index.html`, with its
hashed asset URLs and its actual metadata.
"""

from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods

SHELL = Path(settings.BASE_DIR) / 'static' / 'react' / 'index.html'

MISSING = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Build missing</title></head>
<body style="font:16px/1.6 system-ui;max-width:42rem;margin:15vh auto;padding:0 1.5rem">
<h1 style="font-size:1.25rem">The frontend has not been built.</h1>
<p>Django serves <code>static/react/index.html</code>, and it is not there yet.</p>
<pre style="background:#f4f4f5;padding:1rem;border-radius:.375rem">npm --prefix frontend run build</pre>
<p>In development, use the Vite dev server on port 3000 instead.</p>
</body></html>"""


@lru_cache(maxsize=1)
def _shell() -> str | None:
    """The built page, read once per process.

    Cached because it never changes while a process is alive: a new build is a
    new deployment. On a serverless host this is read once per cold start.
    """
    try:
        return SHELL.read_text(encoding='utf-8')
    except OSError:
        return None


@require_http_methods(['GET'])
def home(request):
    """The single-page app, for every route the API does not claim.

    The CSRF token is not injected here. The client asks for it on the first
    request that needs one — see `ensureCsrf` in `frontend/src/lib/api.js` —
    which keeps this response cacheable and identical for everybody.
    """
    page = _shell()
    if page is None:
        return HttpResponse(MISSING, status=503, content_type='text/html')

    return HttpResponse(page, content_type='text/html')


@require_http_methods(['GET'])
def get_csrf_token(request):
    """Hand out a CSRF cookie for the client to echo back in a header."""
    token = get_token(request)
    response = JsonResponse({'csrfToken': token})
    response.set_cookie(
        'csrftoken',
        token,
        max_age=86400,
        samesite='Lax',
        # Only over HTTPS in production. Pinning this to False, as it was,
        # meant the cookie travelled in the clear on a deployed site.
        secure=not settings.DEBUG,
    )
    return response
