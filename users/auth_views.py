"""
Session authentication.

These were previously ``@csrf_exempt``, read credentials from POST-or-JSON-or-
whichever-worked, and printed the attempted username to the server log on every
request. CSRF protection is on here now; the SPA sends the token with every
unsafe request.
"""

from __future__ import annotations

import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import ValidationError, validate_password
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import UserProfile

logger = logging.getLogger(__name__)

MIN_USERNAME_LENGTH = 3


def _field(request, name: str) -> str:
    """Read a field from JSON or form data, whichever the client sent."""
    value = request.data.get(name)
    return value.strip() if isinstance(value, str) else ''


def _session_payload(user) -> dict:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return {
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'xp': profile.xp,
            'level': profile.level,
            'streak': profile.streak,
            'needs_onboarding': not (profile.financial_goal and profile.risk_tolerance),
        },
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Start a session."""
    username = _field(request, 'username')
    password = request.data.get('password') or ''

    if not username or not password:
        return Response({'success': False, 'error': 'Enter your username and password.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        # Deliberately vague: saying which half was wrong helps enumerate accounts.
        return Response({'success': False, 'error': 'That username and password do not match.'}, status=401)

    login(request, user)
    return Response(_session_payload(user))


@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    """Create an account and start a session."""
    username = _field(request, 'username')
    email = _field(request, 'email')
    password = request.data.get('password') or ''

    if len(username) < MIN_USERNAME_LENGTH:
        return Response(
            {'success': False, 'error': f'Usernames need at least {MIN_USERNAME_LENGTH} characters.'},
            status=400,
        )
    if not email:
        return Response({'success': False, 'error': 'An email address is required.'}, status=400)

    try:
        # Django's own validators: length, common passwords, all-numeric, and
        # similarity to the username.
        validate_password(password, User(username=username, email=email))
    except ValidationError as exc:
        return Response({'success': False, 'error': exc.messages[0]}, status=400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password)
            UserProfile.objects.create(user=user, level='beginner', xp=0)
    except IntegrityError:
        # The unique constraint is the authority; checking first would race.
        return Response({'success': False, 'error': 'That username is already taken.'}, status=400)

    login(request, user)
    return Response(_session_payload(user), status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    """End the session."""
    logout(request)
    return Response({'success': True})
