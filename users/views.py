from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProgress, QuizAttempt, UserProfile, DemoPortfolio
from .serializers import UserProgressSerializer, QuizAttemptSerializer
from courses.models import Course, Lesson
import json


class UserProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def course_progress(self, request):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'error': 'course_id required'}, status=status.HTTP_400_BAD_REQUEST)

        progress = UserProgress.objects.filter(user=request.user, course_id=course_id)
        serializer = self.get_serializer(progress, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_progress(self, request):
        lesson_id = request.data.get('lesson_id')
        status_value = request.data.get('status', 'in_progress')
        progress_percent = request.data.get('progress_percent', 0.0)

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        progress, created = UserProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            course=lesson.topic.course,
            topic=lesson.topic,
            defaults={
                'status': status_value,
                'progress_percent': progress_percent,
                'last_accessed': timezone.now()
            }
        )

        if created:
            progress.started_at = timezone.now()
            progress.save()

        if status_value == 'completed':
            progress.completed_at = timezone.now()
            progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        lesson_id = request.data.get('lesson_id')
        quiz_data = request.data.get('quiz_data', {})

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        # Calculate score (simplified - should match answers from lesson metadata)
        score = 0.0
        max_score = len(quiz_data.get('answers', []))

        attempt = QuizAttempt.objects.create(
            user=request.user,
            lesson=lesson,
            quiz_data=quiz_data,
            score=score,
            max_score=max_score
        )

        serializer = self.get_serializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

@csrf_exempt
@require_http_methods(["POST"])
def save_onboarding(request):
    """Save onboarding quiz answers and create/update user profile"""
    
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Authentication required'
        }, status=401)
    
    try:
        # Get data from FormData (POST request)
        # Try request.POST first (FormData), then request.data (JSON)
        financial_goal = request.POST.get('financial_goal', '') or (hasattr(request, 'data') and request.data.get('financial_goal', '') or '')
        investment_experience = request.POST.get('investment_experience', '') or (hasattr(request, 'data') and request.data.get('investment_experience', '') or '')
        risk_comfort = request.POST.get('risk_comfort', '') or (hasattr(request, 'data') and request.data.get('risk_comfort', '') or '')
        initial_investment = request.POST.get('initial_investment', '') or (hasattr(request, 'data') and request.data.get('initial_investment', '') or '')
        investment_timeline = request.POST.get('investment_timeline', '') or (hasattr(request, 'data') and request.data.get('investment_timeline', '') or '')
        
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'xp': 0,
                'level': 'beginner',  # Will be recalculated below
                'confidence_score': 0.0,
                'onboarding_completed': False
            }
        )
        
        # Update onboarding answers
        profile.financial_goal = financial_goal
        profile.investment_experience = investment_experience
        profile.risk_comfort = risk_comfort
        profile.initial_investment = initial_investment
        profile.investment_timeline = investment_timeline
        profile.onboarding_completed = True
        
        # Calculate initial level based on comprehensive assessment
        # Scoring system that considers multiple factors
        level_score = 0
        experience = profile.investment_experience
        risk_comfort = profile.risk_comfort
        initial_investment = profile.initial_investment
        financial_goal = profile.financial_goal
        
        # Investment experience scoring (primary factor - 0-3 points)
        if experience == 'very_experienced':
            level_score += 3
        elif experience == 'experienced':
            level_score += 2
        elif experience == 'basics':
            level_score += 1
        else:  # beginner
            level_score += 0
        
        # Risk comfort scoring (0-2 points)
        if risk_comfort == 'aggressive':
            level_score += 2
        elif risk_comfort == 'balanced':
            level_score += 1
        else:  # safe
            level_score += 0
        
        # Initial investment scoring (0-1 points) - indicates commitment
        if initial_investment in ['50k_2l', 'over_2l']:
            level_score += 1
        
        # Financial goal scoring (0-1 points)
        if financial_goal in ['long_term_wealth', 'extra_income']:
            level_score += 1
        
        # Determine level based on total score (0-7 points)
        # Advanced: 5-7 points, Intermediate: 3-4 points, Beginner: 0-2 points
        if level_score >= 5:
            profile.level = 'advanced'
            profile.xp = 1200  # Start with enough XP for advanced courses
        elif level_score >= 3:
            profile.level = 'intermediate'
            profile.xp = 750  # Start with enough XP for intermediate courses
        else:
            profile.level = 'beginner'
            profile.xp = 50  # Give some starting XP
        
        profile.save()
        
        # Create demo portfolio if doesn't exist
        DemoPortfolio.objects.get_or_create(
            user=request.user,
            defaults={
                'holdings': {},
                'total_value': 50000.00
            }
        )
        
        # Return level info for frontend display
        level_display = {
            'beginner': 'Beginner',
            'intermediate': 'Intermediate',
            'advanced': 'Advanced'
        }
        
        return JsonResponse({
            'status': 'success',
            'level': profile.level,
            'level_display': level_display.get(profile.level, 'Beginner'),
            'xp': profile.xp,
            'level_score': level_score,
            'message': 'Onboarding completed successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)


def calculate_level_from_answers(answers):
    """Calculate user level from onboarding answers"""
    experience = answers.get('investment_experience', '')
    if experience in ['experienced', 'very_experienced']:
        return 'intermediate'
    elif experience == 'basics':
        return 'beginner'
    return 'beginner'


@api_view(['GET'])
def get_user_profile(request):
    """Get user profile with level, XP, and onboarding data"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        return JsonResponse({
            'level': profile.level,
            'xp': profile.xp,
            'confidence_score': profile.confidence_score,
            'financial_goal': profile.financial_goal,
            'investment_experience': profile.investment_experience,
            'risk_comfort': profile.risk_comfort,
            'initial_investment': profile.initial_investment,
            'investment_timeline': profile.investment_timeline,
            'onboarding_completed': profile.onboarding_completed,
            'demo_balance': float(profile.demo_balance)
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'level': 'beginner',
            'xp': 0,
            'confidence_score': 0.0,
            'onboarding_completed': False,
            'demo_balance': 50000.00
        })


@csrf_exempt
@login_required
@api_view(['POST'])
def award_xp(request):
    """API endpoint to award XP to user"""
    try:
        profile = UserProfile.objects.get(user=request.user)
        amount = int(request.data.get('amount', 0))
        source = request.data.get('source', 'unknown')
        
        if amount > 0:
            profile.xp += amount
            profile.save()
            
            # Check if level up
            old_level = profile.level
            new_level = profile.calculate_level_from_xp()
            
            return JsonResponse({
                'success': True,
                'amount_awarded': amount,
                'new_total': profile.xp,
                'old_total': profile.xp - amount,
                'leveled_up': old_level != new_level,
                'new_level': new_level
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid amount'}, status=400)
            
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
