"""
Course views for serving courses from course_modules folders
"""
import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

# Import the new folder-based loader
from .load_from_folders import load_courses_from_folders, get_module_from_folder


def transform_topic_to_course(topic):
    """Transform a topic (from topics structure) to course format"""
    lessons = topic.get('lessons', [])
    
    # Transform lessons to modules
    modules = []
    for lesson in lessons:
        # Extract Q&A from messages if available
        fixed_qna = []
        messages = lesson.get('messages', [])
        
        # Try to extract Q&A pairs from messages
        # Look for patterns like "Q:" and "A:" or question-answer pairs
        for i, msg in enumerate(messages):
            text = msg.get('text', '')
            sender = msg.get('sender', '')
            
            # If message contains Q&A pattern
            if 'Q:' in text or '?' in text:
                # Try to find answer in next message
                if i + 1 < len(messages):
                    answer_text = messages[i + 1].get('text', '')
                    if answer_text:
                        fixed_qna.append({
                            'q': text.replace('Q:', '').strip(),
                            'a': answer_text.replace('A:', '').strip()
                        })
        
        module = {
            'id': lesson.get('id', ''),
            'title': lesson.get('title', ''),
            'summary': lesson.get('title', ''),  # Use title as summary if no summary field
            'fixed_qna': fixed_qna if isinstance(fixed_qna, list) and len(fixed_qna) > 0 else []
        }
        modules.append(module)
    
    # Calculate duration estimate (5 mins per lesson)
    duration_mins = len(lessons) * 5
    
    course = {
        'id': topic.get('id', ''),
        'title': topic.get('title', ''),
        'overview': topic.get('summary', topic.get('title', '')),
        'duration_mins': duration_mins,
        'source': '',  # Will be extracted from lessons if available
        'modules': modules
    }
    
    return course


def load_courses_data():
    """Load courses from course_modules folders"""
    courses = load_courses_from_folders()
    if courses:
        print(f"Loaded {len(courses)} courses from course_modules folders")
    else:
        print("No courses found in course_modules folders")
    return courses


@api_view(['GET'])
@permission_classes([AllowAny])
def get_courses(request):
    """Get all courses from JSON, filtered by user level"""
    from users.models import UserProfile, UserProgress
    
    # Use folder-based loading first
    courses = load_courses_from_folders()
    if not courses or not isinstance(courses, list):
        courses = load_courses_data()
    
    # Ensure we return an array
    if not isinstance(courses, list):
        courses = []
    
    # If user is authenticated, filter courses based on level
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            user_level = profile.level
            user_xp = profile.xp
            
            # Filter courses based on level and XP
            filtered_courses = []
            for course in courses:
                # Get course level and normalize to lowercase
                course_level_raw = course.get('level', 'beginner')
                course_level = course_level_raw.lower() if isinstance(course_level_raw, str) else 'beginner'
                xp_required = course.get('xp_to_unlock', 0)
                
                # First check if user has enough XP
                has_enough_xp = (xp_required <= user_xp)
                
                # Then check level access
                if user_level == 'beginner':
                    # Beginner users can only access beginner courses (must meet XP requirement)
                    can_access = (course_level == 'beginner' and has_enough_xp)
                elif user_level == 'intermediate':
                    # Intermediate users can access beginner and intermediate courses (must meet XP requirement)
                    can_access = (course_level in ['beginner', 'intermediate'] and has_enough_xp)
                elif user_level == 'advanced':
                    # Advanced users can access all courses (must meet XP requirement)
                    can_access = has_enough_xp
                else:
                    # Default: no access
                    can_access = False
                
                # Calculate course progress
                # Get modules from course - they should already be loaded from load_courses_from_folders
                modules = course.get('modules', [])
                # If no modules in course dict, try to load from folder structure
                if not modules:
                    course_id = course.get('id')
                    if course_id:
                        # Count modules by checking folder structure
                        from pathlib import Path
                        from django.conf import settings
                        course_modules_dir = Path(settings.BASE_DIR) / 'course_modules' / course_id
                        if course_modules_dir.exists():
                            module_folders = [d for d in course_modules_dir.iterdir() if d.is_dir() and d.name.startswith('m')]
                            modules = [{'id': mf.name} for mf in sorted(module_folders)]
                
                completed_count = 0
                total_modules_count = len(modules) if modules else 0
                
                # Count completed modules
                for mod in modules:
                    module_id = mod.get('id') if isinstance(mod, dict) else str(mod)
                    progress = UserProgress.objects.filter(
                        user=request.user,
                        course_id=course.get('id'),
                        module_id=module_id,
                        status='completed'
                    ).first()
                    if progress:
                        completed_count += 1
                
                # Mark course as locked/unlocked
                course['locked'] = not can_access
                course['user_can_access'] = can_access
                course['user_level'] = user_level
                course['user_xp'] = user_xp
                course['completed_modules'] = completed_count
                total_modules_count = len(modules) if modules else 0
                course['total_modules'] = total_modules_count
                course['progress_percent'] = (completed_count / total_modules_count * 100) if total_modules_count > 0 else 0
                
                filtered_courses.append(course)
            
            return Response(filtered_courses)
        except UserProfile.DoesNotExist:
            # No profile yet, show only beginner courses
            filtered_courses = [c for c in courses if c.get('level', 'beginner') == 'beginner' and c.get('xp_to_unlock', 0) == 0]
            for course in filtered_courses:
                course['locked'] = False
                course['user_can_access'] = True
                course['user_level'] = 'beginner'
                course['user_xp'] = 0
            return Response(filtered_courses)
    else:
        # Non-authenticated users see no courses
        return Response([])


@api_view(['GET'])
@permission_classes([AllowAny])
def get_course_detail(request, course_id):
    """Get a specific course by ID from course_modules folders"""
    # Use folder-based loading first
    courses = load_courses_from_folders()
    if not courses:
        courses = load_courses_data()
    
    # Ensure courses is a list
    if not isinstance(courses, list):
        return Response({"error": "Courses data is not in the expected format"}, status=500)
    
    if not courses:
        return Response({"error": "No courses available"}, status=404)
    
    # Find course by ID (case-insensitive match)
    course = None
    for c in courses:
        if isinstance(c, dict):
            course_id_val = c.get("id", "")
            # Try exact match first
            if course_id_val == course_id:
                course = c
                break
            # Try case-insensitive match
            if course_id_val.lower() == course_id.lower():
                course = c
                break
    
    if not course:
        # Return first course as fallback
        print(f"Course '{course_id}' not found, returning first course")
        course = courses[0] if isinstance(courses[0], dict) else None
        if not course:
            return Response({"error": f"Course '{course_id}' not found"}, status=404)
    
    return Response(course)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_module_detail(request, course_id, module_id):
    """Get a specific module from course_modules folder"""
    # Load from folder structure
    result = get_module_from_folder(course_id, module_id)
    
    if not result:
        return Response({"error": "Module not found"}, status=404)
    
    module, course = result
    
    return Response({
        "course": {
            "id": course.get("id"),
            "title": course.get("title"),
            "source": "course_modules"
        },
        "module": module
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_mcq_answer(request, module_id, mcq_id):
    """Submit MCQ answer and award XP"""
    from users.models import UserProfile
    import json
    
    # Parse module_id (format: course_id_module_id)
    if '_' in module_id:
        course_id, module_id_only = module_id.rsplit('_', 1)
    else:
        # Try to find course by searching modules
        courses = load_courses_data()
        course_id = None
        module_id_only = module_id
        for course in courses:
            for mod in course.get('modules', []):
                if mod.get('id') == module_id:
                    course_id = course.get('id')
                    break
            if course_id:
                break
        
        if not course_id:
            return Response({"error": "Module not found"}, status=404)
    
    # Load module from folder
    result = get_module_from_folder(course_id, module_id_only)
    if not result:
        return Response({"error": "Module not found"}, status=404)
    
    module, course = result
    mcqs = module.get('mcqs', [])
    
    # Find the specific MCQ
    mcq = None
    for m in mcqs:
        if str(m.get('id')) == str(mcq_id):
            mcq = m
            break
    
    if not mcq:
        return Response({"error": "MCQ not found"}, status=404)
    
    # Get selected choice
    choice_idx = request.data.get('choice')
    selected_answer = request.data.get('selected_answer', '')
    
    # Determine correct answer
    correct_answer = mcq.get('correct_answer')
    choices = mcq.get('choices') or mcq.get('options', [])
    correct_choice_idx = mcq.get('correct_choice')
    
    # Check if answer is correct
    if choice_idx is not None:
        is_correct = (choice_idx == correct_choice_idx) or (choices[choice_idx] == correct_answer if choice_idx < len(choices) else False)
    else:
        is_correct = (selected_answer == correct_answer)
    
    # Award XP if correct (only once per MCQ)
    from users.models import UserProgress
    progress, _ = UserProgress.objects.get_or_create(
        user=request.user,
        course_id=course_id,
        module_id=module_id_only,
        defaults={'status': 'in_progress'}
    )
    
    # Check if this MCQ was already answered correctly
    mcqs_progress = progress.mcqs_progress or {}
    mcq_progress_data = mcqs_progress.get(str(mcq_id), {})
    already_correct = mcq_progress_data.get('correct', False)
    
    xp_awarded = 0
    if is_correct and not already_correct:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        xp_per_mcq = 15  # Default XP per MCQ
        profile.xp += xp_per_mcq
        profile.save()
        xp_awarded = xp_per_mcq
        progress.xp_awarded += xp_per_mcq
    
    # Update MCQ progress
    mcqs_progress[str(mcq_id)] = {
        'answered': True,
        'correct': is_correct,
        'attempts': mcq_progress_data.get('attempts', 0) + 1,
        'allow_retry': not is_correct  # Allow retry if incorrect
    }
    progress.mcqs_progress = mcqs_progress
    progress.save()
    
    # Get AI feedback
    ai_feedback = mcq.get('ai_feedback', {})
    feedback_message = ai_feedback.get('correct' if is_correct else 'incorrect', '')
    
    return Response({
        'correct': is_correct,
        'correct_answer': correct_answer,
        'correct_choice': correct_choice_idx,
        'explanation': feedback_message or mcq.get('explanation', ''),
        'xp_awarded': xp_awarded,
        'user_xp': UserProfile.objects.get(user=request.user).xp,
        'isCorrect': is_correct,  # For frontend compatibility
        'mcq_progress': mcqs_progress.get(str(mcq_id), {})
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_flash_cards(request, module_id):
    """Get all flash cards for a module from course_modules folder"""
    # Parse module_id (format: course_id_module_id)
    if '_' in module_id:
        course_id, module_id_only = module_id.rsplit('_', 1)
    else:
        # Try to find course by searching modules
        courses = load_courses_data()
        course_id = None
        module_id_only = module_id
        for course in courses:
            for mod in course.get('modules', []):
                if mod.get('id') == module_id:
                    course_id = course.get('id')
                    break
            if course_id:
                break
        
        if not course_id:
            return Response({"error": "Module not found"}, status=404)
    
    # Load module from folder
    result = get_module_from_folder(course_id, module_id_only)
    if not result:
        return Response({"error": "Module not found"}, status=404)
    
    module, course = result
    flash_cards = module.get('flash_cards', [])
    
    # Transform flash cards to expected format
    transformed_cards = []
    for i, card in enumerate(flash_cards[:4]):  # Max 4 cards
        transformed_cards.append({
            'id': card.get('id', f'flashcard-{i+1}'),
            'topic': card.get('topic', ''),
            'theory_title': card.get('theory_title', ''),
            'theory_content': card.get('theory_content', ''),
            'question': card.get('question', card.get('topic', '')),
            'answer': card.get('answer', card.get('theory_content', '')),
            'reward': {'xp': 25}  # Default XP per flash card
        })
    
    return Response({
        'flash_cards': transformed_cards,
        'total': len(transformed_cards)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_plaque_card_content(request, module_id):
    """Get plaque card content (flash card, scenario, etc.)"""
    from courses.models import ModuleContent
    
    try:
        module_content = ModuleContent.objects.get(module_id=module_id)
        plaque_card = module_content.plaque_card or {}
        card_type = plaque_card.get('type', 'flash-card')
        
        # Generate flash card content based on module
        if card_type == 'flash-card':
            # Create flash card from module content
            theory_text = module_content.theory_text or ''
            if theory_text:
                theory_key_points = theory_text.split('.')[:3]  # First 3 sentences
                key_concept = '. '.join([p.strip() for p in theory_key_points if p.strip()]) + '.'
            else:
                key_concept = module_content.summary or f"Key concepts from {module_content.title}"
            
            # Generate a question from the fixed Q&A or theory
            fixed_qna = list(module_content.qna_pairs.all())
            if fixed_qna:
                # Use first Q&A as flash card question
                flash_question = fixed_qna[0].question
                flash_answer = fixed_qna[0].answer
            else:
                # Generate question from module title
                flash_question = f"What is the main concept of {module_content.title}?"
                flash_answer = module_content.summary or (theory_text[:200] if theory_text else "Please review the module content.")
            
            return Response({
                'type': 'flash-card',
                'content': {
                    'key_concept': key_concept,
                    'question': flash_question,
                    'answer': flash_answer,
                    'reward': plaque_card.get('reward_on_complete', {})
                }
            })
        elif card_type == 'quiz-card':
            # For quiz cards, use first MCQ
            mcqs = list(module_content.mcqs.all()[:1])
            if mcqs:
                mcq = mcqs[0]
                return Response({
                    'type': 'quiz-card',
                    'content': {
                        'question': mcq.question,
                        'choices': mcq.choices,
                        'correct_choice': mcq.correct_choice,
                        'explanation': mcq.explanation,
                        'reward': plaque_card.get('reward_on_complete', {})
                    }
                })
            else:
                # Fallback: create a flash card if no MCQ available
                theory_text = module_content.theory_text or ''
                if theory_text:
                    theory_key_points = theory_text.split('.')[:3]
                    key_concept = '. '.join([p.strip() for p in theory_key_points if p.strip()]) + '.'
                else:
                    key_concept = module_content.summary or f"Key concepts from {module_content.title}"
                
                fixed_qna = list(module_content.qna_pairs.all())
                if fixed_qna:
                    flash_question = fixed_qna[0].question
                    flash_answer = fixed_qna[0].answer
                else:
                    flash_question = f"What is the main concept of {module_content.title}?"
                    flash_answer = module_content.summary or (theory_text[:200] if theory_text else "Please review the module content.")
                
                return Response({
                    'type': 'flash-card',
                    'content': {
                        'key_concept': key_concept,
                        'question': flash_question,
                        'answer': flash_answer,
                        'reward': plaque_card.get('reward_on_complete', {})
                    }
                })
        
        return Response({'error': f'Unsupported card type: {card_type}'}, status=400)
        
    except ModuleContent.DoesNotExist:
        # Try to get module from JSON as fallback
        try:
            courses = load_courses_data()
            course_id, module_id_only = module_id.rsplit('_', 1) if '_' in module_id else (None, module_id)
            
            module = None
            for course in courses:
                if course.get('id') == course_id:
                    for mod in course.get('modules', []):
                        if mod.get('id') == module_id_only:
                            module = mod
                            break
                    break
            
            if module:
                # Create basic flash card from module data
                theory_text = module.get('theory_text', '')
                key_concept = (theory_text[:300] if theory_text else module.get('summary', 'No content available'))
                fixed_qna = module.get('fixed_qna', [])
                
                if fixed_qna and len(fixed_qna) > 0:
                    flash_question = fixed_qna[0].get('q', 'What is the main concept?')
                    flash_answer = fixed_qna[0].get('a', 'Please review the module content.')
                else:
                    flash_question = f"What is the main concept of {module.get('title', 'this module')}?"
                    flash_answer = module.get('summary', 'Please review the module content above.')
                
                plaque_card = module.get('plaque_card', {})
                return Response({
                    'type': 'flash-card',
                    'content': {
                        'key_concept': key_concept,
                        'question': flash_question,
                        'answer': flash_answer,
                        'reward': plaque_card.get('reward_on_complete', {'xp': 25})
                    }
                })
        except Exception as e:
            pass
        
        return Response({"error": f"Module '{module_id}' not found in database or JSON"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_plaque_card_answer(request, module_id):
    """Submit plaque card answer and award XP only if correct"""
    from courses.models import ModuleContent, UserPlaqueCardCompletion
    from users.models import UserProfile
    
    try:
        module_content = ModuleContent.objects.get(module_id=module_id)
        plaque_card = module_content.plaque_card or {}
        card_type = plaque_card.get('type', '')
        user_answer = request.data.get('answer', '').strip()
        selected_choice = request.data.get('selected_choice', '').upper()
        
        reward = plaque_card.get('reward_on_complete', {})
        # Ensure flash cards give enough XP - default to 20% of module XP per flash card
        default_flash_xp = max(10, (module_content.xp_reward * 20) // 100)
        xp_to_award = reward.get('xp', default_flash_xp)
        
        is_correct = False
        correct_answer = None
        
        if card_type == 'flash-card':
            # For flash cards, check if answer matches (fuzzy match)
            # Get expected answer from request if provided (for multi-card support)
            expected_answer = request.data.get('expected_answer', '').strip()
            card_index = request.data.get('card_index', 0)
            
            fixed_qna = list(module_content.qna_pairs.all())
            
            # Use expected answer from request if provided, otherwise use first Q&A
            if expected_answer:
                correct_answer = expected_answer.lower()
            elif fixed_qna and card_index < len(fixed_qna):
                correct_answer = fixed_qna[card_index].answer.lower()
            elif fixed_qna:
                correct_answer = fixed_qna[0].answer.lower()
            else:
                correct_answer = ''
            
            if correct_answer:
                user_answer_lower = user_answer.lower()
                
                # Simple keyword matching (check if user answer contains key words from correct answer)
                correct_words = set([w for w in correct_answer.split()[:8] if len(w) > 3])  # First 8 words, ignore short words
                user_words = set([w for w in user_answer_lower.split() if len(w) > 3])
                overlap = len(correct_words.intersection(user_words))
                
                # More lenient matching: if at least 30% of key words match, consider it correct
                min_overlap = max(2, len(correct_words) // 3)
                is_correct = overlap >= min_overlap or user_answer_lower in correct_answer or correct_answer in user_answer_lower
            else:
                is_correct = False
                correct_answer = None
                
        elif card_type == 'quiz-card':
            # For quiz cards, check selected choice
            mcqs = list(module_content.mcqs.all()[:1])
            if mcqs:
                mcq = mcqs[0]
                correct_answer = mcq.correct_choice
                is_correct = (selected_choice == mcq.correct_choice.upper())
        
        # Only award XP if correct and not already completed
        xp_awarded = 0
        if is_correct:
            completion, created = UserPlaqueCardCompletion.objects.get_or_create(
                user=request.user,
                module_content=module_content,
                card_type=card_type,
                defaults={
                    'xp_awarded': xp_to_award,
                    'badge_earned': reward.get('badge')
                }
            )
            
            if created:
                # Award XP and update profile
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.xp += xp_to_award
                profile.save()
                xp_awarded = xp_to_award
        
        return Response({
            'success': True,
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'xp_awarded': xp_awarded,
            'user_xp': UserProfile.objects.get(user=request.user).xp if request.user.is_authenticated else 0
        })
        
    except ModuleContent.DoesNotExist:
        return Response({"error": "Module not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

