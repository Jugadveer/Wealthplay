"""Project package.

Celery is imported here so its app is registered before any task module is
loaded, but only when Celery is actually installed. A serverless deployment has
no worker to run the two scheduled jobs against — warming the market cache and
advancing the simulated prices — and shipping Celery, Kombu, billiard, amqp and
Redis to a host that cannot use them is weight for nothing.

Where there is no worker, those jobs run as scheduled HTTP requests instead; see
`vercel.json`. Where there is one, install `requirements-asgi.txt` and this
behaves exactly as before.
"""

try:
    from .celery import app as celery_app
except ModuleNotFoundError:  # Celery not installed — no worker on this host.
    celery_app = None

__all__ = ('celery_app',)
