"""
Course API.

Serves the catalogue from :mod:`courses.content` and tracks progress in
``UserCourseProgress``. There is one content store now; the parallel
``financial_course.json`` store that the mentor used to read has been removed.
"""

from __future__ import annotations

import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import UserProfile

from . import content
from .models import UserCourseProgress

logger = logging.getLogger(__name__)


def _progress_for(user, course_id: str | None = None) -> dict[str, str]:
    """Module id -> status for one user, optionally narrowed to a course."""
    if not user.is_authenticated:
        return {}

    rows = UserCourseProgress.objects.filter(user=user).exclude(module_id='')
    if course_id:
        rows = rows.filter(course_id=course_id)

    return {f'{row.course_id}:{row.module_id}': row.status for row in rows}


@api_view(['GET'])
@permission_classes([AllowAny])
def list_courses(request):
    """Every course, with the caller's completion counts."""
    progress = _progress_for(request.user)

    courses = []
    for course in content.catalogue():
        completed = sum(
            1
            for module in course['modules']
            if progress.get(f'{course["id"]}:{module["id"]}') == 'completed'
        )
        courses.append(
            {
                'id': course['id'],
                'title': course['title'],
                'level': course['level'],
                'summary': course['summary'],
                'xp_to_unlock': course['xp_to_unlock'],
                'module_count': course['module_count'],
                'estimated_minutes': course['estimated_minutes'],
                'completed_modules': completed,
            }
        )

    return Response({'courses': courses})


@api_view(['GET'])
@permission_classes([AllowAny])
def course_detail(request, course_id):
    """One course and its module list."""
    course = content.get_course(course_id)
    if not course:
        return Response({'error': 'No such course.'}, status=404)

    progress = _progress_for(request.user, course_id)

    return Response(
        {
            'id': course['id'],
            'title': course['title'],
            'level': course['level'],
            'summary': course['summary'],
            'estimated_minutes': course['estimated_minutes'],
            'modules': [
                {
                    'id': module['id'],
                    'title': module['title'],
                    'summary': module['summary'],
                    'order': module['order'],
                    'estimated_minutes': module['estimated_minutes'],
                    'xp_reward': module['xp_reward'],
                    'card_count': len(module['cards']),
                    'question_count': len(module['mcqs']),
                    'status': progress.get(f'{course_id}:{module["id"]}', 'not_started'),
                }
                for module in course['modules']
            ],
        }
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def module_detail(request, course_id, module_id):
    """One module, ready to render.

    Correct answers are withheld: grading happens server-side so the answer key
    is never in the page source.
    """
    module = content.get_module(course_id, module_id)
    if not module:
        return Response({'error': 'No such module.'}, status=404)

    course = content.get_course(course_id)
    answered = _answered_questions(request.user, course_id, module_id)

    return Response(
        {
            'course': {'id': course['id'], 'title': course['title']},
            'id': module['id'],
            'title': module['title'],
            'theory': module['theory'],
            'estimated_minutes': module['estimated_minutes'],
            'xp_reward': module['xp_reward'],
            'cards': module['cards'],
            'questions': [
                {
                    'id': question['id'],
                    'question': question['question'],
                    'options': question['options'],
                    'answered': question['id'] in answered,
                }
                for question in module['mcqs']
            ],
            'qna': module['qna'],
            'next': content.next_module(course_id, module_id),
            'status': _module_status(request.user, course_id, module_id),
        }
    )


def _answered_questions(user, course_id: str, module_id: str) -> set[str]:
    row = UserCourseProgress.objects.filter(
        user=user, course_id=course_id, module_id=module_id
    ).first()
    return set(getattr(row, 'answered_questions', None) or [])


def _module_status(user, course_id: str, module_id: str) -> str:
    row = UserCourseProgress.objects.filter(
        user=user, course_id=course_id, module_id=module_id
    ).first()
    return row.status if row else 'not_started'


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def answer_question(request):
    """Grade one question and award XP the first time it is answered correctly."""
    course_id = request.data.get('course_id', '')
    module_id = request.data.get('module_id', '')
    question_id = str(request.data.get('question_id', ''))

    module = content.get_module(course_id, module_id)
    if not module:
        return Response({'error': 'No such module.'}, status=404)

    question = next((q for q in module['mcqs'] if str(q['id']) == question_id), None)
    if not question:
        return Response({'error': 'No such question.'}, status=404)

    try:
        chosen = int(request.data.get('choice'))
    except (TypeError, ValueError):
        return Response({'error': 'Choose an option.'}, status=400)

    correct = chosen == question['correct_index']

    row, _ = UserCourseProgress.objects.get_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id,
        defaults={'status': 'in_progress'},
    )

    answered = set(row.answered_questions or [])
    first_time = question_id not in answered

    if correct and first_time:
        answered.add(question_id)
        row.answered_questions = sorted(answered)
        row.status = 'in_progress' if row.status == 'not_started' else row.status
        row.save(update_fields=['answered_questions', 'status', 'last_accessed'])

    xp = 15 if (correct and first_time) else 0
    if xp:
        _award_xp(request.user, xp)

    explanation = question['explanation'] if correct else question['hint']
    if not correct and not explanation:
        from ai import tutor

        explanation = (
            tutor.explain_wrong_answer(
                question['question'],
                chosen=question['options'][chosen] if 0 <= chosen < len(question['options']) else '',
                correct=question['options'][question['correct_index']],
                module_title=module['title'],
            )
            or ''
        )

    return Response(
        {
            'correct': correct,
            'correct_index': question['correct_index'],
            'explanation': explanation,
            'xp_awarded': xp,
        }
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_module(request):
    """Mark a module finished, award its XP, and enrol its questions for review."""
    course_id = request.data.get('course_id', '')
    module_id = request.data.get('module_id', '')

    module = content.get_module(course_id, module_id)
    if not module:
        return Response({'error': 'No such module.'}, status=404)

    row, _ = UserCourseProgress.objects.get_or_create(
        user=request.user, course_id=course_id, module_id=module_id
    )

    already_done = row.status == 'completed'
    if not already_done:
        from django.utils import timezone

        row.status = 'completed'
        row.progress_percent = 100.0
        row.completed_at = timezone.now()
        row.save()
        _award_xp(request.user, module['xp_reward'])

        # The module's questions now enter the spaced-repetition queue.
        from daily.review import sync_cards

        sync_cards(request.user)

    from users.achievement_views import check_and_unlock_achievements

    unlocked = check_and_unlock_achievements(request.user)

    return Response(
        {
            'success': True,
            'already_completed': already_done,
            'xp_awarded': 0 if already_done else module['xp_reward'],
            'next': content.next_module(course_id, module_id),
            'newly_unlocked_achievements': [
                {'id': a.id, 'name': a.name, 'xp_reward': a.xp_reward} for a in unlocked
            ],
        }
    )


def _award_xp(user, amount: int) -> None:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.xp += amount
    profile.save(update_fields=['xp'])
    profile.calculate_level_from_xp()
