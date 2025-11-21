"""
Django management command to import enriched module content from JSON
"""
from django.core.management.base import BaseCommand
import json
import os
from django.conf import settings
from courses.models import ModuleContent, ModuleQNA, ModuleMCQ, ModuleMentorPrompt

class Command(BaseCommand):
    help = 'Import enriched module content from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='data/output/modules_bundle.json',
            help='Path to the module content bundle JSON file'
        )
        parser.add_argument(
            '--full-content',
            type=str,
            default='financial_course_full_content.json',
            help='Path to the full content JSON file'
        )

    def handle(self, *args, **options):
        file_path = options.get('file')
        full_content_path = options.get('full_content')
        
        # Try full content file first
        if os.path.exists(full_content_path):
            self.stdout.write(f'Loading from: {full_content_path}')
            with open(full_content_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'modules' in data:
                modules = data['modules']
            elif isinstance(data, list):
                modules = data
            else:
                self.stdout.write(self.style.ERROR('Invalid JSON structure'))
                return
        elif os.path.exists(file_path):
            self.stdout.write(f'Loading from: {file_path}')
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and 'results' in data:
                modules = data['results']
            else:
                modules = data if isinstance(data, list) else []
        else:
            self.stdout.write(self.style.ERROR(f'File not found: {full_content_path} or {file_path}'))
            return
        
        imported = 0
        updated = 0
        errors = []
        
        for module_data in modules:
            try:
                module_id = module_data.get('module_id', '')
                course_id = module_data.get('topic_id', '')
                
                if not module_id or not course_id:
                    errors.append(f'Missing module_id or topic_id: {module_data}')
                    continue
                
                # Get or create ModuleContent
                module_content, created = ModuleContent.objects.update_or_create(
                    module_id=module_id,
                    defaults={
                        'course_id': course_id,
                        'title': module_data.get('title', ''),
                        'summary': module_data.get('summary', ''),
                        'theory_text': module_data.get('theory_text', ''),
                        'duration_min': module_data.get('duration_min', 0),
                        'xp_reward': module_data.get('xp_reward', 0),
                        'plaque_card': module_data.get('plaque_card', {}),
                        'metadata': module_data.get('metadata', {})
                    }
                )
                
                if created:
                    imported += 1
                else:
                    updated += 1
                
                # Import Q&A
                ModuleQNA.objects.filter(module_content=module_content).delete()
                for idx, qna in enumerate(module_data.get('fixed_qna', [])):
                    ModuleQNA.objects.create(
                        module_content=module_content,
                        question=qna.get('q', ''),
                        answer=qna.get('a', ''),
                        order=idx
                    )
                
                # Import MCQs
                ModuleMCQ.objects.filter(module_content=module_content).delete()
                for idx, mcq_data in enumerate(module_data.get('mcqs', [])):
                    ModuleMCQ.objects.create(
                        module_content=module_content,
                        mcq_id=mcq_data.get('id', f'mcq-{idx+1}'),
                        question=mcq_data.get('question', ''),
                        choices=mcq_data.get('choices', []),
                        correct_choice=mcq_data.get('correct_choice', ''),
                        explanation=mcq_data.get('explanation', ''),
                        order=idx
                    )
                
                # Import Mentor Prompts
                ModuleMentorPrompt.objects.filter(module_content=module_content).delete()
                for idx, prompt_data in enumerate(module_data.get('mentor_prompts', [])):
                    ModuleMentorPrompt.objects.create(
                        module_content=module_content,
                        user_question=prompt_data.get('user_q', ''),
                        mentor_answer_seed=prompt_data.get('mentor_a', ''),
                        order=idx
                    )
                
            except Exception as e:
                errors.append(f'Error processing {module_data.get("module_id", "unknown")}: {str(e)}')
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n[SUCCESS] Import complete!\n'
            f'   Imported: {imported}\n'
            f'   Updated: {updated}\n'
            f'   Errors: {len(errors)}'
        ))
        
        if errors:
            self.stdout.write(self.style.WARNING('\nErrors:'))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(self.style.WARNING(f'  - {error}'))

