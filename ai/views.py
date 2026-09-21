"""
Endpoints for help that is not tied to one feature.

Everything here answers the same shape of question — "what does this mean?",
"what do I do here?" — from wherever the user happens to be. The feature-specific
AI lives with its feature; this is the part that follows them around.

Every response carries ``available``. When the model cannot be reached the UI
shows nothing rather than a template dressed up as an answer.
"""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import client, coach, retrieve

MAX_TERM = 120
MAX_CONTEXT = 400


@api_view(['GET'])
@permission_classes([AllowAny])
def ai_status(request):
    """Where answers are coming from, so the UI can say so.

    Worth surfacing rather than hiding: an answer written by a model running on
    this machine and one sent to a hosted API are different things to a user
    typing in their income.
    """
    return Response(client.status())


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain(request):
    """Explain a highlighted term, from the course content where it exists."""
    term = (request.data.get('term') or '').strip()[:MAX_TERM]
    context = (request.data.get('context') or '').strip()[:MAX_CONTEXT]
    course_id = (request.data.get('course_id') or '').strip()

    if not term:
        return Response({'error': 'Nothing to explain.'}, status=400)

    result = coach.explain(term, context=context, course_id=course_id)
    if result is None:
        return Response({'available': False, 'term': term})

    return Response({'available': True, **result})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def explain_number(request):
    """Explain a figure on screen: what it measures, what would move it."""
    label = (request.data.get('label') or '').strip()[:MAX_TERM]
    value = request.data.get('value')
    context = (request.data.get('context') or '').strip()[:MAX_CONTEXT]

    if not label:
        return Response({'error': 'Which number?'}, status=400)

    text = coach.explain_number(label, value, context=context)
    if text is None:
        return Response({'available': False})

    return Response({'available': True, 'label': label, 'explanation': text})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def page_help(request):
    """Orientation for the section the user is currently in."""
    zone = (request.data.get('zone') or '').strip()
    facts = request.data.get('facts')

    if zone not in coach.ZONES:
        return Response({'error': 'Unknown section.'}, status=400)

    text = coach.page_help(zone, facts=facts if isinstance(facts, dict) else None)
    if text is None:
        return Response({'available': False, 'zone': zone})

    return Response({'available': True, 'zone': zone, 'help': text})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_content(request):
    """Search the course content directly.

    No model involved. It backs the assistant's "where is this taught?" links
    and is useful on its own when somebody knows what they are looking for.
    """
    query = (request.GET.get('q') or '').strip()[:MAX_CONTEXT]
    if not query:
        return Response({'results': []})

    return Response({'results': retrieve.search(query, limit=5)})
