"""Move the fictional practice stocks forward.

Prices also catch up lazily whenever a quote is read, so this is a convenience
rather than a requirement — every session's return is seeded on
``(symbol, date)``, so both paths produce the same series.

    python manage.py advance_simulated_prices
    python manage.py advance_simulated_prices --rebuild   # redraw all history
"""

from django.core.management.base import BaseCommand

from users.models import CustomStock
from users.portfolio.simulation import advance, advance_all


class Command(BaseCommand):
    help = 'Advance every simulated stock to today.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Discard existing bars and redraw every history from the current model.',
        )

    def handle(self, *args, **options):
        if options['rebuild']:
            for stock in CustomStock.objects.all():
                stock.price_history = []
                advance(stock)
            self.stdout.write(self.style.SUCCESS(f'Rebuilt {CustomStock.objects.count()} histories.'))
            return

        moved = advance_all()
        self.stdout.write(self.style.SUCCESS(f'Advanced {moved} simulated stocks.'))
