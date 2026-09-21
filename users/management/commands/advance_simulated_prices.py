"""Move the fictional practice stocks forward one trading session.

Run once a day:

    python manage.py advance_simulated_prices
"""

from django.core.management.base import BaseCommand

from users.portfolio.simulation import advance_all


class Command(BaseCommand):
    help = 'Advance every simulated stock by one session.'

    def handle(self, *args, **options):
        moved = advance_all()
        self.stdout.write(self.style.SUCCESS(f'Advanced {moved} simulated stocks.'))
