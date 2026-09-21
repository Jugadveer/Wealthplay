"""Populate the market cache so the first user of the day is not the one who pays.

Run on deploy and on a schedule:

    python manage.py warm_market_cache
"""

from django.core.management.base import BaseCommand

from market_data import services


class Command(BaseCommand):
    help = 'Fetch and cache quotes for every tracked symbol.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            help='Comma-separated symbols to warm instead of the tracked list.',
        )

    def handle(self, *args, **options):
        symbols = (
            [s.strip().upper() for s in options['symbols'].split(',') if s.strip()]
            if options.get('symbols')
            else services.TRACKED_SYMBOLS
        )

        warmed = services.warm(symbols)
        missed = len(symbols) - warmed

        self.stdout.write(self.style.SUCCESS(f'Cached {warmed}/{len(symbols)} symbols.'))
        if missed:
            self.stdout.write(
                self.style.WARNING(f'{missed} returned no price; they will retry on demand.')
            )
