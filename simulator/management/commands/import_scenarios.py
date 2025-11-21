"""
Management command to import scenarios from scenarios.json
Run: python manage.py import_scenarios
"""
from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings
from simulator.models import Scenario, DecisionOption


class Command(BaseCommand):
    help = 'Imports scenarios from scenarios.json file'

    def handle(self, *args, **options):
        self.stdout.write('Importing scenarios from scenarios.json...')
        
        # Get the JSON file path
        json_path = os.path.join(settings.BASE_DIR, 'scenarios.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_path}'))
            return
        
        # Read and parse JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Separate scenarios and decision options
        scenarios_data = [item for item in data if item['model'] == 'simulator.scenario']
        options_data = [item for item in data if item['model'] == 'simulator.decisionoption']
        
        self.stdout.write(f'Found {len(scenarios_data)} scenarios and {len(options_data)} decision options')
        
        # Import scenarios (update or create)
        scenarios_imported = 0
        scenarios_updated = 0
        for scenario_item in scenarios_data:
            pk = scenario_item['pk']
            fields = scenario_item['fields']
            
            scenario, created = Scenario.objects.update_or_create(
                id=pk,
                defaults={
                    'title': fields['title'],
                    'description': fields['description'],
                    'starting_balance': fields['starting_balance']
                }
            )
            
            if created:
                scenarios_imported += 1
            else:
                scenarios_updated += 1
        
        # Import decision options (delete existing for each scenario first, then import)
        options_imported = 0
        options_updated = 0
        
        # Group options by scenario
        options_by_scenario = {}
        for option_item in options_data:
            scenario_id = option_item['fields']['scenario']
            if scenario_id not in options_by_scenario:
                options_by_scenario[scenario_id] = []
            options_by_scenario[scenario_id].append(option_item)
        
        # Import options for each scenario
        for scenario_id, option_items in options_by_scenario.items():
            try:
                scenario = Scenario.objects.get(id=scenario_id)
                # Delete existing options for this scenario
                DecisionOption.objects.filter(scenario=scenario).delete()
                
                # Import new options
                for option_item in option_items:
                    pk = option_item['pk']
                    fields = option_item['fields']
                    
                    # Ensure score is an integer (handle both string and int in JSON)
                    score_value = fields.get('score', 0)
                    if isinstance(score_value, str):
                        try:
                            score_value = int(score_value)
                        except (ValueError, TypeError):
                            score_value = 0
                    try:
                        score_value = int(score_value) if score_value else 0
                    except (TypeError, ValueError):
                        score_value = 0
                    
                    # Use update_or_create to ensure options are properly imported
                    option, created = DecisionOption.objects.update_or_create(
                        id=pk,
                        defaults={
                            'scenario': scenario,
                            'text': fields['text'],
                            'decision_type': fields['decision_type'],
                            'balance_impact': fields['balance_impact'],
                            'confidence_delta': fields.get('confidence_delta', 0),
                            'risk_score_delta': fields.get('risk_score_delta', 0),
                            'future_growth_rate': fields.get('future_growth_rate', 0.0),
                            'score': score_value,
                            'why_it_matters': fields.get('why_it_matters', ''),
                            'mentor_feedback': fields.get('mentor_feedback', '')
                        }
                    )
                    options_imported += 1
                    if score_value > 0:
                        self.stdout.write(f'  Imported option "{fields["text"]}" with score {score_value}')
                    
            except Scenario.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Scenario {scenario_id} not found, skipping options'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nImport Summary:\n'
            f'  Scenarios: {scenarios_imported} imported, {scenarios_updated} updated\n'
            f'  Decision Options: {options_imported} imported\n'
            f'  Total Scenarios in DB: {Scenario.objects.count()}\n'
            f'  Total Options in DB: {DecisionOption.objects.count()}'
        ))

