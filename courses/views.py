from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.utils import timezone
from .models import Course, Topic, Lesson, MentorPersona
from .serializers import CourseSerializer, TopicSerializer, LessonSerializer, MentorPersonaSerializer
from .course_views import load_courses_data, get_course_detail, get_module_detail
from users.models import UserProgress, UserProfile
import json


# API Viewsets
class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        course = self.get_object()
        topics = Topic.objects.filter(course=course)
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class MentorPersonaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MentorPersona.objects.all()
    serializer_class = MentorPersonaSerializer


# Page Views - Course listing page
@login_required(login_url='/')
def course_home(request):
    """Course listing page with progress tracking"""
    return render(request, 'courses/course_listing.html', {
        'user': request.user
    })


@login_required(login_url='/')
def course_detail(request, course_id=None):
    """Course detail page - serves JSON-based course detail"""
    if not course_id:
        courses = load_courses_data()
        if courses and len(courses) > 0:
            course_id = courses[0]["id"]
            return redirect(f'/course/{course_id}/')
    
    return render(request, 'courses/course_detail.html', {
        'course_id': course_id,
        'user': request.user
    })


@login_required(login_url='/')
def lesson_detail(request, course_id, module_id):
    """Lesson detail page - shows lesson content with Q&A and mentor chat"""
    return render(request, 'courses/lesson_detail.html', {
        'course_id': course_id,
        'module_id': module_id,
        'user': request.user
    })


# API endpoints for course/lesson management
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_courses_with_progress(request):
    """Get all courses with user progress and unlock states"""
    courses = load_courses_data()
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        user_level = profile.level
        user_xp = profile.xp
    except UserProgress.DoesNotExist:
        user_level = 'beginner'
        user_xp = 0
    
    # Get all user progress
    user_progress = {}
    progress_records = UserProgress.objects.filter(user=request.user)
    for p in progress_records:
        if p.course_id and p.module_id:
            key = f"{p.course_id}_{p.module_id}"
            user_progress[key] = {
                'status': p.status,
                'xp_awarded': p.xp_awarded,
                'completed_at': p.completed_at.isoformat() if p.completed_at else None
            }
    
    # Add progress and unlock status to courses
    for course in courses:
        course['unlocked'] = course.get('xp_to_unlock', 0) <= user_xp
        if course.get('modules'):
            for module in course['modules']:
                key = f"{course['id']}_{module['id']}"
                progress = user_progress.get(key)
                
                if progress:
                    module['status'] = progress['status']
                    module['xp_awarded'] = progress.get('xp_awarded', 0)
                else:
                    # Determine unlock status
                    module['status'] = 'locked'
                    if module.get('lock_rule') == 'sequential' and module.get('order', 1) > 1:
                        # Check if previous module is completed
                        prev_module = next((m for m in course['modules'] if m.get('order') == module.get('order') - 1), None)
                        if prev_module:
                            prev_key = f"{course['id']}_{prev_module['id']}"
                            prev_progress = user_progress.get(prev_key)
                            if prev_progress and prev_progress['status'] == 'completed':
                                module['status'] = 'unlocked'
                    elif module.get('order', 1) == 1 and course['unlocked']:
                        module['status'] = 'unlocked'
    
    return Response(courses)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_lesson(request, course_id, module_id):
    """Mark lesson as started and return lesson content"""
    courses = load_courses_data()
    course = next((c for c in courses if c.get('id') == course_id), None)
    
    if not course:
        return Response({'error': 'Course not found'}, status=404)
    
    module = next((m for m in course.get('modules', []) if m.get('id') == module_id), None)
    if not module:
        return Response({'error': 'Module not found'}, status=404)
    
    # Create or update progress
    progress, created = UserProgress.objects.update_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id,
        defaults={
            'status': 'in_progress',
            'started_at': timezone.now() if created else None
        }
    )
    
    # Return lesson content
    return Response({
        'course': {
            'id': course.get('id'),
            'title': course.get('title'),
            'source': course.get('source')
        },
        'module': module,
        'progress': {
            'status': progress.status,
            'started_at': progress.started_at.isoformat() if progress.started_at else None
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_lesson(request, course_id, module_id):
    """Mark lesson as completed, award XP, and unlock next lessons"""
    courses = load_courses_data()
    course = next((c for c in courses if c.get('id') == course_id), None)
    
    if not course:
        return Response({'error': 'Course not found'}, status=404)
    
    module = next((m for m in course.get('modules', []) if m.get('id') == module_id), None)
    if not module:
        return Response({'error': 'Module not found'}, status=404)
    
    # Get or create progress
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id
    )
    
    # Update progress
    progress.status = 'completed'
    progress.completed_at = timezone.now()
    progress.progress_percent = 100.0
    
    # Award XP
    xp_reward = module.get('xp_reward', 0)
    progress.xp_awarded = xp_reward
    
    try:
        profile = UserProfile.objects.get(user=request.user)
        profile.xp += xp_reward
        profile.save()
    except UserProfile.DoesNotExist:
        pass
    
    progress.save()
    
    # Unlock next module
    next_module = None
    if module.get('lock_rule') == 'sequential':
        next_module = next((m for m in course.get('modules', []) if m.get('order') == module.get('order', 0) + 1), None)
        if next_module:
            UserProgress.objects.update_or_create(
                user=request.user,
                course_id=course_id,
                module_id=next_module['id'],
                defaults={'status': 'unlocked'}
            )
    
    return Response({
        'status': 'completed',
        'xp_awarded': xp_reward,
        'next_module': next_module,
        'profile': {
            'xp': profile.xp if 'profile' in locals() else 0,
            'level': profile.level if 'profile' in locals() else 'beginner'
        }
    })


# Auth views
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    from django.contrib.auth import authenticate, login
    from django.http import JsonResponse
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            return JsonResponse({'success': False, 'error': 'Username and password are required'}, status=400)
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return JsonResponse({'success': True, 'redirect': '/'})
        return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@csrf_exempt
def signup_view(request):
    from django.contrib.auth.models import User
    from django.contrib.auth import login, authenticate
    from django.http import JsonResponse
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')
        
        if not username or len(username) < 3:
            return JsonResponse({'success': False, 'error': 'Username must be at least 3 characters'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists'}, status=400)
        
        if not email:
            return JsonResponse({'success': False, 'error': 'Email is required'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already registered'}, status=400)
        
        if password != password2:
            return JsonResponse({'success': False, 'error': 'Passwords do not match'}, status=400)
        
        if not password or len(password) < 6:
            return JsonResponse({'success': False, 'error': 'Password must be at least 6 characters'}, status=400)
        
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            
            # Create user profile
            from users.models import UserProfile
            UserProfile.objects.create(
                user=user,
                level='beginner',
                xp=0,
                onboarding_completed=False
            )
            
            login(request, user)
            return JsonResponse({
                'success': True, 
                'redirect': '/',
                'needs_onboarding': True  # Signal that onboarding should be shown
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


def logout_view(request):
    from django.contrib.auth import logout
    if request.method == 'POST':
        logout(request)
        return redirect('/')
    return redirect('/')
