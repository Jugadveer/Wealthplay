"""
The mentor, Nex.

One endpoint serves both the in-lesson mentor and the floating assistant; the
only difference is whether a module id is supplied. There used to be two
endpoints with two prompts, two histories, and two greetings — one of which
called the mentor "Next".

Questions are grounded in the module the learner is reading, resolved through
:mod:`courses.content`. Previously the mentor searched an unrelated JSON file
that never contained the real course ids, so every question answered
"Course 'investing-basics' not found."
"""

from __future__ import annotations

import logging

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ai import tutor
from courses import content

from .models import TopicChatMessage

logger = logging.getLogger(__name__)

HISTORY_TURNS = 8
MAX_QUESTION_LENGTH = 500

UNAVAILABLE = (
    "I can't reach my language model right now. The lesson notes and the "
    'common questions below still have you covered.'
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_mentor(request):
    """Answer a question, grounded in the current module when there is one."""
    question = (request.data.get('question') or '').strip()[:MAX_QUESTION_LENGTH]
    course_id = (request.data.get('course_id') or '').strip()
    module_id = (request.data.get('module_id') or '').strip()

    if not question:
        return Response({'error': 'Ask me something first.'}, status=400)

    module = content.get_module(course_id, module_id) if course_id and module_id else None

    # A question the module already answers gets the authored answer, which is
    # faster and more accurate than regenerating it.
    if module:
        authored = _authored_answer(question, module['qna'])
        if authored:
            _record(request.user, course_id, module_id, question, authored)
            return Response({'reply': authored, 'source': 'lesson', 'available': True})

    reply = tutor.answer_lesson_question(
        question,
        module_title=module['title'] if module else 'general finance',
        theory=module['theory'] if module else '',
        history=_recent_turns(request.user, course_id, module_id),
    )

    if reply is None:
        return Response({'reply': UNAVAILABLE, 'source': 'unavailable', 'available': False})

    _record(request.user, course_id, module_id, question, reply)
    return Response({'reply': reply, 'source': 'model', 'available': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mentor_history(request, course_id, module_id=''):
    """Past turns for a module, so the conversation survives a page reload."""
    messages = TopicChatMessage.objects.filter(
        user=request.user, course_id=course_id, module_id=module_id
    ).order_by('created_at')[:60]

    return Response(
        {
            'messages': [
                {
                    'role': 'user' if message.sender == 'user' else 'assistant',
                    'text': message.text,
                    'at': message.created_at.isoformat(),
                }
                for message in messages
            ]
        }
    )


def _authored_answer(question: str, qna: list[dict]) -> str | None:
    """Match a question against the module's authored Q&A.

    Deliberately conservative: it requires a real overlap of meaningful words,
    because a wrong match is worse than no match.
    """
    asked = _keywords(question)
    if len(asked) < 2:
        return None

    best_score, best_answer = 0.0, None
    for pair in qna:
        candidate = _keywords(pair['question'])
        if not candidate:
            continue
        overlap = len(asked & candidate) / len(asked | candidate)
        if overlap > best_score:
            best_score, best_answer = overlap, pair['answer']

    return best_answer if best_score >= 0.5 else None


_STOPWORDS = frozenset(
    'a an the is are was were do does did what why how when which that this '
    'of to in on for with and or it its my your i you can should would'.split()
)


def _keywords(text: str) -> set[str]:
    return {
        word.strip('?.,!').lower()
        for word in text.split()
        if len(word) > 2 and word.strip('?.,!').lower() not in _STOPWORDS
    }


def _recent_turns(user, course_id: str, module_id: str) -> list[tuple[str, str]]:
    """The last few turns, oldest first, so follow-up questions resolve."""
    recent = TopicChatMessage.objects.filter(
        user=user, course_id=course_id, module_id=module_id
    ).order_by('-created_at')[:HISTORY_TURNS]

    return [('user' if m.sender == 'user' else 'assistant', m.text) for m in reversed(recent)]


def _record(user, course_id: str, module_id: str, question: str, answer: str) -> None:
    """Persist both sides of the exchange."""
    stamp = timezone.now().strftime('%H:%M')
    TopicChatMessage.objects.bulk_create(
        [
            TopicChatMessage(
                user=user, course_id=course_id, module_id=module_id,
                sender='user', text=question, time_display=stamp,
            ),
            TopicChatMessage(
                user=user, course_id=course_id, module_id=module_id,
                sender='nex', text=answer, time_display=stamp,
            ),
        ]
    )
