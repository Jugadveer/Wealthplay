import json
import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from courses.models import Course, Topic, Lesson, MentorPersona
from chat.models import ChatMessage, Attachment
from datetime import datetime


class Command(BaseCommand):
    help = 'Import course data from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file')

    def handle(self, *args, **options):
        json_file = options['json_file']
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Import mentors
        self.stdout.write('Importing mentors...')
        for mentor_id, mentor_data in data.get('mentors', {}).items():
            MentorPersona.objects.update_or_create(
                mentor_id=mentor_id,
                defaults={
                    'name': mentor_data['name'],
                    'role': mentor_data['role'],
                    'system_prompt': mentor_data['system_prompt'],
                }
            )
        self.stdout.write(self.style.SUCCESS(f'Imported {len(data.get("mentors", {}))} mentors'))

        # Import course
        meta = data.get('meta', {})
        course, created = Course.objects.update_or_create(
            course_id=meta.get('course_id', 'finlit_001'),
            defaults={
                'title': meta.get('title', 'Financial Literacy Course'),
                'language': meta.get('language', 'en-IN'),
                'currency': meta.get('currency', 'INR'),
                'version': meta.get('version', '1.0'),
            }
        )
        self.stdout.write(self.style.SUCCESS(f'Imported course: {course.title}'))

        # Import topics and lessons
        topics_count = 0
        lessons_count = 0
        messages_count = 0
        attachments_count = 0

        for topic_data in data.get('topics', []):
            topic, _ = Topic.objects.update_or_create(
                course=course,
                topic_id=topic_data['id'],
                defaults={
                    'title': topic_data['title'],
                    'order': topic_data.get('order', 0),
                    'summary': topic_data.get('summary', ''),
                }
            )
            topics_count += 1

            for lesson_data in topic_data.get('lessons', []):
                lesson, _ = Lesson.objects.update_or_create(
                    topic=topic,
                    lesson_id=lesson_data['id'],
                    defaults={
                        'title': lesson_data['title'],
                        'order': lesson_data.get('order', 0),
                        'content_type': lesson_data.get('content_type', 'chat'),
                        'metadata': {
                            'quiz': lesson_data.get('quiz', []),
                            'sources': lesson_data.get('sources', []),
                        }
                    }
                )
                lessons_count += 1

                # Import messages
                for msg_data in lesson_data.get('messages', []):
                    ChatMessage.objects.get_or_create(
                        lesson=lesson,
                        sender=msg_data['sender'],
                        text=msg_data['text'],
                        defaults={
                            'time_display': msg_data.get('time', ''),
                        }
                    )
                    messages_count += 1

                    # Handle attachments in messages
                    if 'attachment' in msg_data:
                        att_data = msg_data['attachment']
                        Attachment.objects.get_or_create(
                            attachment_id=att_data.get('id', ''),
                            defaults={
                                'title': att_data.get('title', ''),
                                'filename': att_data.get('filename', ''),
                                'size_bytes': att_data.get('size_bytes', 0),
                                'mime_type': att_data.get('mime_type', 'application/pdf'),
                                'short_summary': att_data.get('short_summary', ''),
                                'tags': att_data.get('tags', []),
                            }
                        )
                        attachments_count += 1

                # Import standalone attachments
                for att_data in lesson_data.get('attachments', []):
                    Attachment.objects.get_or_create(
                        attachment_id=att_data.get('id', ''),
                        defaults={
                            'title': att_data.get('title', ''),
                            'filename': att_data.get('filename', ''),
                            'size_bytes': att_data.get('size_bytes', 0),
                            'mime_type': att_data.get('mime_type', 'application/pdf'),
                            'short_summary': att_data.get('short_summary', ''),
                            'tags': att_data.get('tags', []),
                        }
                    )
                    attachments_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nImport complete:\n'
            f'  - Topics: {topics_count}\n'
            f'  - Lessons: {lessons_count}\n'
            f'  - Messages: {messages_count}\n'
            f'  - Attachments: {attachments_count}'
        ))





