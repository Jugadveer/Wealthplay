"""
Scheduled work, as an HTTP endpoint.

The same job `users.tasks.warm_market_cache` runs under Celery. A serverless
deployment has no worker to run it, so the platform's scheduler calls this
instead — see `crons` in `vercel.json`. One job, two triggers, no second copy of
the logic: both call `services.warm`.

It matters because a cold market cache means the first visitor of the day waits
on eight provider round trips. Warming it overnight moves that cost off a real
person.

Authentication is a shared secret rather than a session, because a scheduler has
no user. Vercel signs its own cron requests with `Authorization: Bearer
$CRON_SECRET`; anything else must send the same header. With no secret
configured the endpoint refuses in production and allows in development, so it
cannot be left accidentally open.
"""

from __future__ import annotations

import hmac
import logging
import os

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import services

logger = logging.getLogger(__name__)


def _authorised(request) -> bool:
    secret = os.environ.get('CRON_SECRET', '').strip()
    if not secret:
        # Never open on a deployed site just because nobody set the variable.
        return settings.DEBUG

    presented = request.headers.get('Authorization', '')
    expected = f'Bearer {secret}'
    # Constant-time: a plain `==` leaks the secret one character at a time.
    return hmac.compare_digest(presented, expected)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def warm(request):
    """Pre-populate the quote cache for every tracked symbol."""
    if not _authorised(request):
        return Response({'error': 'Not authorised.'}, status=401)

    warmed = services.warm()
    total = len(services.TRACKED_SYMBOLS)
    logger.info('cron warm: %s/%s symbols', warmed, total)

    return Response({'warmed': warmed, 'symbols': total})
