"""
Django management command to import module content from folder structure:
course_modules/{course_id}/{module_id}/
"""
from django.core.management.base import BaseCommand
import json
import os
from pathlib import Path
from django.conf import settings
from courses.models import ModuleContent, ModuleQNA, ModuleMCQ

class Command(BaseCommand):
    help = 'Import module content from course_modules folder structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--course',
            type=str,
            default=None,
            help='Import only a specific course (course_id)'
        )
        parser.add_argument(
            '--module',
            type=str,
            default=None,
            help='Import only a specific module (course_id_module_id)'
        )

    def handle(self, *args, **options):
        base_dir = Path('course_modules')
        
        if not base_dir.exists():
            self.stdout.write(self.style.ERROR('course_modules folder not found!'))
            self.stdout.write(self.style.WARNING('Run: python create_module_folders.py first'))
            return
        
        imported = 0
        updated = 0
        errors = []
        
        # Load base course structure to get module metadata
        try:
            with open('financial_course.json', 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not load financial_course.json: {e}'))
            courses_data = []
        
        # Build course/module lookup
        course_module_lookup = {}
        for course in courses_data:
            course_id = course.get('id')
            for module in course.get('modules', []):
                module_id = module.get('id')
                full_module_id = f"{course_id}_{module_id}"
                course_module_lookup[full_module_id] = {
                    'course_id': course_id,
                    'module': module
                }
        
        # Process each course folder
        for course_dir in base_dir.iterdir():
            if not course_dir.is_dir():
                continue
            
            course_id = course_dir.name
            
            # Filter by course if specified
            if options.get('course') and course_id != options.get('course'):
                continue
            
            # Process each module folder
            for module_dir in course_dir.iterdir():
                if not module_dir.is_dir():
                    continue
                
                module_id = module_dir.name
                full_module_id = f"{course_id}_{module_id}"
                
                # Filter by module if specified
                if options.get('module') and full_module_id != options.get('module'):
                    continue
                
                try:
                    # Get module metadata from lookup
                    module_info = course_module_lookup.get(full_module_id, {})
                    module_meta = module_info.get('module', {})
                    
                    # Load MCQs
                    mcqs_file = module_dir / 'mcqs.json'
                    mcqs = []
                    if mcqs_file.exists():
                        with open(mcqs_file, 'r', encoding='utf-8') as f:
                            mcqs = json.load(f)
                    
                    # Load flash cards (optional, for future use)
                    flash_cards_file = module_dir / 'flash_cards.json'
                    flash_cards = []
                    if flash_cards_file.exists():
                        with open(flash_cards_file, 'r', encoding='utf-8') as f:
                            flash_cards = json.load(f)
                    
                    # Load Q&A
                    qna_file = module_dir / 'qna.json'
                    qna_data = []
                    if qna_file.exists():
                        with open(qna_file, 'r', encoding='utf-8') as f:
                            qna_data = json.load(f)
                    
                    # Get or create ModuleContent
                    module_content, created = ModuleContent.objects.update_or_create(
                        module_id=full_module_id,
                        defaults={
                            'course_id': course_id,
                            'title': module_meta.get('title', module_id),
                            'summary': module_meta.get('summary', ''),
                            'theory_text': module_meta.get('theory_text', ''),
                            'duration_min': module_meta.get('duration_min', 0),
                            'xp_reward': module_meta.get('xp_reward', 0),
                            'plaque_card': module_meta.get('plaque_card', {'type': 'flash-card'}),
                            'metadata': module_meta.get('metadata', {})
                        }
                    )
                    
                    if created:
                        imported += 1
                    else:
                        updated += 1
                    
                    # Import Q&A
                    ModuleQNA.objects.filter(module_content=module_content).delete()
                    for idx, qa in enumerate(qna_data):
                        ModuleQNA.objects.create(
                            module_content=module_content,
                            question=qa.get('question', ''),
                            answer=qa.get('answer', ''),
                            order=idx
                        )
                    
                    # Import MCQs
                    ModuleMCQ.objects.filter(module_content=module_content).delete()
                    for idx, mcq in enumerate(mcqs):
                        ModuleMCQ.objects.create(
                            module_content=module_content,
                            mcq_id=mcq.get('id', f'mcq-{idx+1}'),
                            question=mcq.get('question', ''),
                            choices=mcq.get('choices', []),
                            correct_choice=mcq.get('correct_choice', ''),
                            explanation=mcq.get('explanation', ''),
                            order=idx
                        )
                    
                    self.stdout.write(f'  {full_module_id}: {len(mcqs)} MCQs, {len(qna_data)} Q&A')
                    
                except Exception as e:
                    errors.append(f'{full_module_id}: {str(e)}')
                    self.stdout.write(self.style.ERROR(f'  Error in {full_module_id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n[SUCCESS] Import complete!\n'
            f'   Imported: {imported}\n'
            f'   Updated: {updated}\n'
            f'   Errors: {len(errors)}'
        ))
        
        if errors:
            self.stdout.write(self.style.WARNING('\nErrors:'))
            for error in errors[:10]:
                self.stdout.write(self.style.WARNING(f'  - {error}'))

