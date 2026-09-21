"""Load the scenario bank into the database.

Idempotent: scenarios are keyed on title, so re-running updates the text and
the options in place rather than creating duplicates.

    python manage.py seed_scenarios
    python manage.py seed_scenarios --prune   # also delete scenarios not in the bank
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from simulator.models import DecisionOption, Scenario
from simulator.scenario_bank import BANK


class Command(BaseCommand):
    help = 'Create or update every scenario in simulator/scenario_bank.py.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--prune',
            action='store_true',
            help='Delete scenarios whose titles are no longer in the bank.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created = updated = 0

        for case in BANK:
            scenario, was_created = Scenario.objects.update_or_create(
                title=case.title,
                defaults={'description': case.description, 'starting_balance': case.balance},
            )
            created += was_created
            updated += not was_created

            # Options are replaced wholesale. Matching them individually would
            # need a stable key the bank does not have, and rewriting three rows
            # is cheaper than inventing one.
            scenario.options.all().delete()
            DecisionOption.objects.bulk_create(
                DecisionOption(
                    scenario=scenario,
                    text=choice.text,
                    decision_type=choice.kind,
                    balance_impact=choice.impact,
                    future_growth_rate=choice.growth,
                    confidence_delta=choice.confidence,
                    risk_score_delta=choice.risk,
                    score=choice.score,
                    why_it_matters=choice.why,
                    mentor_feedback=choice.mentor,
                )
                for choice in case.options
            )

        removed = 0
        if options['prune']:
            titles = {case.title for case in BANK}
            removed, _ = Scenario.objects.exclude(title__in=titles).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'{created} created, {updated} updated, {removed} removed. '
                f'{Scenario.objects.count()} scenarios in total.'
            )
        )
