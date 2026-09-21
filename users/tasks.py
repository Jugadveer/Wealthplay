"""
Scheduled background work.

Both tasks are also management commands, so they can be run by cron, Task
Scheduler or Celery Beat without requiring a broker to be available.
"""

import logging

from celery import shared_task

from market_data import services
from users.portfolio.simulation import advance_all

logger = logging.getLogger(__name__)


@shared_task
def warm_market_cache():
    """Refresh quotes for every tracked symbol.

    Without this the first request of the day pays the provider round trip for
    every symbol on the page.
    """
    warmed = services.warm()
    logger.info('warmed %s market symbols', warmed)
    return {'warmed': warmed}


@shared_task
def advance_simulated_prices():
    """Move the fictional practice stocks forward one session."""
    moved = advance_all()
    logger.info('advanced %s simulated stocks', moved)
    return {'moved': moved}
