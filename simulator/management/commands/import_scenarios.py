"""
Management command to import scenarios from simulator_data.json
Run: python manage.py import_scenarios
"""
from django.core.management.base import BaseCommand
from django.db import transaction
import json
import os
from pathlib import Path
from django.conf import settings
from simulator.models import Scenario, DecisionOption


class Command(BaseCommand):
    help = 'Imports scenarios from simulator_data.json file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to JSON file (default: simulator_data.json in project root)',
        )

    def handle(self, *args, **options):
        # Clean up old scenario JSON files
        self.stdout.write('Cleaning up old scenario JSON files...')
        base_dir = Path(settings.BASE_DIR)
        old_files = [
            base_dir / 'scenarios.json',
            base_dir / 'simulator' / 'scenarios.json',
            base_dir / 'mentor_content' / 'scenarios.json',
        ]
        for old_file in old_files:
            if old_file.exists():
                try:
                    old_file.unlink()
                    self.stdout.write(self.style.SUCCESS(f'  Deleted: {old_file}'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Could not delete {old_file}: {e}'))
        
        # Get the JSON file path
        if options.get('file'):
            json_path = Path(options['file'])
        else:
            json_path = Path(settings.BASE_DIR) / 'simulator_data.json'
        
        if not json_path.exists():
            self.stdout.write(self.style.ERROR(f'File not found: {json_path}'))
            self.stdout.write(f'Looking for file at: {json_path.absolute()}')
            return
        
        self.stdout.write(f'Importing scenarios from {json_path}...')
        
        # Read and parse JSON
        try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {e}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return
        
        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR('JSON file must contain a list of scenarios'))
            return
        
        # Check if it's Django dump format or direct format
        # Direct format has 'id' and 'options' fields at top level
        # Django format has 'model' and 'pk' fields
        is_django_format = len(data) > 0 and isinstance(data[0], dict) and 'model' in data[0] and 'pk' in data[0] and 'id' not in data[0]
        
        if is_django_format:
            # Handle Django dump format
            scenarios_data = [item for item in data if item.get('model') == 'simulator.scenario']
            options_data = [item for item in data if item.get('model') == 'simulator.decisionoption']
            self.stdout.write(f'Found {len(scenarios_data)} scenarios and {len(options_data)} options in Django format')
        else:
            # Handle direct format (with 'id' and 'options' fields)
            scenarios_data = data
            options_data = []
            self.stdout.write(f'Found {len(scenarios_data)} scenarios in direct format')
        
        # Use atomic transaction to ensure all-or-nothing import
        try:
            with transaction.atomic():
                # Delete all existing scenarios and options first
                self.stdout.write('Deleting existing scenarios and options...')
                deleted_options = DecisionOption.objects.all().delete()[0]
                deleted_scenarios = Scenario.objects.all().delete()[0]
                self.stdout.write(self.style.SUCCESS(f'  Deleted {deleted_scenarios} scenarios and {deleted_options} options'))
                
        scenarios_imported = 0
        scenarios_updated = 0
                options_imported = 0
                
                if is_django_format:
                    # Process Django format
                    for item in scenarios_data:
                        scenario_id = item.get('pk')
                        fields = item.get('fields', {})
            
            scenario, created = Scenario.objects.update_or_create(
                            id=scenario_id,
                defaults={
                                'title': fields.get('title', ''),
                                'description': fields.get('description', ''),
                                'starting_balance': float(fields.get('starting_balance', 50000.00))
                }
            )
            
            if created:
                scenarios_imported += 1
            else:
                scenarios_updated += 1
        
                        # Delete existing options
                        DecisionOption.objects.filter(scenario=scenario).delete()
        
                    # Process options
        options_by_scenario = {}
                    for item in options_data:
                        scenario_id = item.get('fields', {}).get('scenario')
                        if scenario_id:
            if scenario_id not in options_by_scenario:
                options_by_scenario[scenario_id] = []
                            options_by_scenario[scenario_id].append(item)
        
        for scenario_id, option_items in options_by_scenario.items():
            try:
                scenario = Scenario.objects.get(id=scenario_id)
                            for item in option_items:
                                fields = item.get('fields', {})
                                DecisionOption.objects.create(
                                    scenario=scenario,
                                    text=fields.get('text', ''),
                                    decision_type=fields.get('decision_type', 'SAVE'),
                                    balance_impact=float(fields.get('balance_impact', 0.00)),
                                    confidence_delta=fields.get('confidence_delta', 0),
                                    risk_score_delta=fields.get('risk_score_delta', 0),
                                    future_growth_rate=float(fields.get('future_growth_rate', 0.0)),
                                    score=fields.get('score', 0),
                                    why_it_matters=fields.get('why_it_matters', ''),
                                    mentor_feedback=fields.get('mentor_feedback', '')
                                )
                                options_imported += 1
                        except Scenario.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f'Scenario {scenario_id} not found'))
                else:
                    # Process direct format (with 'id' field)
                    for scenario_data in data:
                        scenario_id = scenario_data.get('id')
                        if not scenario_id:
                            self.stdout.write(self.style.WARNING('Skipping scenario without id'))
                            continue
                        
                        # Create or update scenario
                        scenario, created = Scenario.objects.update_or_create(
                            id=scenario_id,
                        defaults={
                                'title': scenario_data.get('title', ''),
                                'description': scenario_data.get('description', ''),
                                'starting_balance': scenario_data.get('starting_balance', 50000.00)
                            }
                        )
                        
                        if created:
                            scenarios_imported += 1
                            self.stdout.write(f'  Created scenario #{scenario_id}: {scenario.title}')
                        else:
                            scenarios_updated += 1
                            self.stdout.write(f'  Updated scenario #{scenario_id}: {scenario.title}')
                        
                        # Delete existing options for this scenario to avoid duplicates
                        DecisionOption.objects.filter(scenario=scenario).delete()
                        
                        # Import options
                        options = scenario_data.get('options', [])
                        for option_data in options:
                            DecisionOption.objects.create(
                                scenario=scenario,
                                text=option_data.get('text', ''),
                                decision_type=option_data.get('decision_type', 'SAVE'),
                                balance_impact=option_data.get('balance_impact', 0.00),
                                confidence_delta=option_data.get('confidence_delta', 0),
                                risk_score_delta=option_data.get('risk_score_delta', 0),
                                future_growth_rate=option_data.get('future_growth_rate', 0.0),
                                score=option_data.get('score', 0),
                                why_it_matters=option_data.get('why_it_matters', ''),
                                mentor_feedback=option_data.get('mentor_feedback', '')
                    )
                    options_imported += 1
                    
                        self.stdout.write(f'    Imported {len(options)} options for scenario #{scenario_id}')
        
        self.stdout.write(self.style.SUCCESS(
                    f'\n✅ Import Complete!\n'
                    f'  Scenarios: {scenarios_imported} created, {scenarios_updated} updated\n'
            f'  Decision Options: {options_imported} imported\n'
            f'  Total Scenarios in DB: {Scenario.objects.count()}\n'
            f'  Total Options in DB: {DecisionOption.objects.count()}'
        ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {e}'))
            import traceback
            traceback.print_exc()
            raise
