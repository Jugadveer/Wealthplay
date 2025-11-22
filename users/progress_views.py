"""
Progress tracking views for flashcards, MCQs, and module completion
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import UserProgress, UserProfile
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flashcard_flip(request):
    """Record flashcard flip and award XP"""
    course_id = request.data.get('course_id')
    module_id = request.data.get('module_id')
    flashcard_id = request.data.get('flashcard_id')
    
    if not all([course_id, module_id, flashcard_id]):
        return Response({"error": "Missing required fields"}, status=400)
    
    # Get or create progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id,
        defaults={'status': 'in_progress', 'started_at': timezone.now()}
    )
    
    # Check if already flipped - handle both list and dict formats
    flipped_cards = progress.flashcards_flipped
    if isinstance(flipped_cards, dict):
        # Convert dict to list
        flipped_cards = [k for k, v in flipped_cards.items() if v]
    elif not isinstance(flipped_cards, list):
        flipped_cards = []
    
    # Convert flashcard_id to string for consistency
    flashcard_id_str = str(flashcard_id)
    
    if flashcard_id_str in flipped_cards:
        return Response({
            "xp_awarded": 0,
            "message": "Flashcard already flipped",
            "flipped_cards": flipped_cards
        })
    
    # Award XP for flashcard flip
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    xp_per_flashcard = 25
    profile.xp += xp_per_flashcard
    profile.save()
    
    # Update progress - store as list
    flipped_cards.append(flashcard_id_str)
    progress.flashcards_flipped = flipped_cards
    progress.xp_awarded += xp_per_flashcard
    progress.save()
    
    return Response({
        "xp_awarded": xp_per_flashcard,
        "user_xp": profile.xp,
        "flipped_cards": flipped_cards
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_flashcard_progress(request):
    """Get flashcard progress for a module"""
    course_id = request.query_params.get('course_id')
    module_id = request.query_params.get('module_id')
    
    if not all([course_id, module_id]):
        return Response({"error": "Missing course_id or module_id"}, status=400)
    
    try:
        progress = UserProgress.objects.get(
            user=request.user,
            course_id=course_id,
            module_id=module_id
        )
        flipped_cards = progress.flashcards_flipped
        # Handle both list and dict formats
        if isinstance(flipped_cards, dict):
            flipped_cards = [k for k, v in flipped_cards.items() if v]
        elif not isinstance(flipped_cards, list):
            flipped_cards = []
        return Response({
            "flipped_cards": flipped_cards
        })
    except UserProgress.DoesNotExist:
        return Response({
            "flipped_cards": []
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mcq_progress(request):
    """Get MCQ progress for a module"""
    course_id = request.query_params.get('course_id')
    module_id = request.query_params.get('module_id')
    
    if not all([course_id, module_id]):
        return Response({"error": "Missing course_id or module_id"}, status=400)
    
    try:
        progress = UserProgress.objects.get(
            user=request.user,
            course_id=course_id,
            module_id=module_id
        )
        return Response({
            "mcq_progress": progress.mcqs_progress or {}
        })
    except UserProgress.DoesNotExist:
        return Response({
            "mcq_progress": {}
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_module_progress(request):
    """Get overall module progress"""
    course_id = request.query_params.get('course_id')
    module_id = request.query_params.get('module_id')
    
    if not all([course_id, module_id]):
        return Response({"error": "Missing course_id or module_id"}, status=400)
    
    try:
        progress = UserProgress.objects.get(
            user=request.user,
            course_id=course_id,
            module_id=module_id
        )
        # Calculate progress counts
        flipped_cards = progress.flashcards_flipped
        if isinstance(flipped_cards, dict):
            flipped_cards = [k for k, v in flipped_cards.items() if v]
        elif not isinstance(flipped_cards, list):
            flipped_cards = []
        
        mcqs_progress = progress.mcqs_progress or {}
        mcqs_completed = sum(1 for mcq in mcqs_progress.values() if mcq.get('answered') and mcq.get('correct'))
        
        return Response({
            "status": progress.status,
            "progress_percent": progress.progress_percent,
            "xp_awarded": progress.xp_awarded,
            "flashcards_flipped": len(flipped_cards),
            "mcqs_completed": mcqs_completed,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None
        })
    except UserProgress.DoesNotExist:
        return Response({
            "status": "locked",
            "progress_percent": 0,
            "xp_awarded": 0,
            "flashcards_flipped": 0,
            "mcqs_completed": 0,
            "completed_at": None
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mcq_answer(request):
    """Record MCQ answer and award XP if correct"""
    course_id = request.data.get('course_id')
    module_id = request.data.get('module_id')
    mcq_id = request.data.get('mcq_id') or request.data.get('id')
    choice = request.data.get('choice')
    selected_answer = request.data.get('selected_answer')
    is_correct = request.data.get('correct', False)
    
    if not all([course_id, module_id, mcq_id is not None]):
        return Response({"error": "Missing required fields"}, status=400)
    
    # Get or create progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id,
        defaults={'status': 'in_progress', 'started_at': timezone.now()}
    )
    
    # Get MCQ progress
    mcqs_progress = progress.mcqs_progress or {}
    mcq_key = str(mcq_id)
    
    # Check if already answered correctly
    if mcq_key in mcqs_progress and mcqs_progress[mcq_key].get('correct'):
        return Response({
            "correct": True,
            "xp_awarded": 0,
            "message": "MCQ already answered correctly",
            "user_xp": UserProfile.objects.get(user=request.user).xp
        })
    
    # Award XP only if correct and not already answered
    xp_awarded = 0
    if is_correct:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        xp_per_mcq = 15
        profile.xp += xp_per_mcq
        profile.save()
        xp_awarded = xp_per_mcq
        progress.xp_awarded += xp_per_mcq
    
    # Update progress
    mcqs_progress[mcq_key] = {
        'answered': True,
        'correct': is_correct,
        'selected_choice': choice,
        'selected_answer': selected_answer,
        'attempts': mcqs_progress.get(mcq_key, {}).get('attempts', 0) + 1
    }
    progress.mcqs_progress = mcqs_progress
    progress.save()
    
    return Response({
        "correct": is_correct,
        "xp_awarded": xp_awarded,
        "user_xp": UserProfile.objects.get(user=request.user).xp,
        "mcq_progress": mcqs_progress[mcq_key]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_module(request):
    """Mark module as completed when all flashcards and MCQs are done"""
    course_id = request.data.get('course_id')
    module_id = request.data.get('module_id')
    
    if not all([course_id, module_id]):
        return Response({"error": "Missing course_id or module_id"}, status=400)
    
    # Get progress
    try:
        progress = UserProgress.objects.get(
            user=request.user,
            course_id=course_id,
            module_id=module_id
        )
    except UserProgress.DoesNotExist:
        return Response({"error": "Progress not found"}, status=404)
    
    # Award bonus XP for completion if not already completed
    xp_bonus = 0
    if progress.status != 'completed':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        xp_bonus = 50  # Bonus XP for completing a module
        profile.xp += xp_bonus
        profile.save()
        
        # Update progress
        progress.status = 'completed'
        progress.progress_percent = 100.0
        progress.xp_awarded += xp_bonus
        progress.completed_at = timezone.now()
        progress.save()
    
    return Response({
        "completed": True,
        "xp_awarded": xp_bonus,
        "user_xp": UserProfile.objects.get(user=request.user).xp
    })

