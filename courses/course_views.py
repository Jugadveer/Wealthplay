"""
Course views for serving courses from financial_course.json
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


# Try both possible file names
COURSES_JSON_PATH = None
for filename in ['financial_course.json', 'financial_courses.json']:
    path = os.path.join(settings.BASE_DIR, filename)
    if os.path.exists(path):
        COURSES_JSON_PATH = path
        break

if not COURSES_JSON_PATH:
    COURSES_JSON_PATH = os.path.join(settings.BASE_DIR, 'financial_course.json')


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
    """Load courses from JSON file - use as-is, no transformation"""
    if not COURSES_JSON_PATH or not os.path.exists(COURSES_JSON_PATH):
        print(f"Courses JSON file not found at: {COURSES_JSON_PATH}")
        return []
    
    try:
        with open(COURSES_JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct array of courses (expected format)
                print(f"Loaded {len(data)} courses from {COURSES_JSON_PATH}")
                return data
            elif isinstance(data, dict):
                # Object with 'topics' or 'courses' key
                if 'topics' in data and isinstance(data['topics'], list):
                    # Transform topics to courses format
                    topics = data['topics']
                    courses = [transform_topic_to_course(topic) for topic in topics]
                    print(f"Loaded {len(courses)} courses from {COURSES_JSON_PATH} (transformed from topics)")
                    return courses
                elif 'courses' in data and isinstance(data['courses'], list):
                    print(f"Loaded {len(data['courses'])} courses from {COURSES_JSON_PATH}")
                    return data['courses']
                else:
                    print(f"JSON structure not recognized. Keys: {list(data.keys())}")
                    return []
            else:
                print(f"Unexpected JSON structure: {type(data)}")
                return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return []
    except Exception as e:
        print(f"Error loading courses: {e}")
        import traceback
        traceback.print_exc()
        return []


@api_view(['GET'])
@permission_classes([AllowAny])
def get_courses(request):
    """Get all courses from JSON, filtered by user level"""
    from users.models import UserProfile
    
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
                course_level = course.get('level', 'beginner')
                xp_required = course.get('xp_to_unlock', 0)
                
                # Level hierarchy: beginner < intermediate < advanced
                level_hierarchy = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
                user_level_num = level_hierarchy.get(user_level, 0)
                course_level_num = level_hierarchy.get(course_level, 0)
                
                # Unlock logic:
                # 1. User can access courses at their level or below (beginner < intermediate < advanced)
                # 2. User can access courses they have enough XP for
                # 3. If user is intermediate/advanced, they can access beginner courses
                can_access = False
                
                if course_level_num <= user_level_num:
                    # User is at or above course level (e.g., intermediate can access beginner)
                    can_access = (xp_required <= user_xp)  # Still need enough XP
                elif user_level_num > 0 and course_level == 'beginner':
                    # Intermediate/advanced users can access beginner courses if they have XP
                    can_access = (xp_required <= user_xp)
                else:
                    # Course level is higher than user level - check XP
                    can_access = (xp_required <= user_xp)
                
                # Mark course as locked/unlocked
                course['locked'] = not can_access
                course['user_can_access'] = can_access
                course['user_level'] = user_level
                course['user_xp'] = user_xp
                
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
    """Get a specific course by ID"""
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
    """Get a specific module from a course with enriched content"""
    from courses.models import ModuleContent
    
    # Try to get enriched content from database first
    full_module_id = f"{course_id}_{module_id}"
    try:
        module_content = ModuleContent.objects.get(module_id=full_module_id)
        
        # Build enriched response
        response_data = {
            "course": {
                "id": course_id,
                "title": module_content.title,
                "source": ""  # Can be added later
            },
            "module": {
                "id": module_id,
                "title": module_content.title,
                "summary": module_content.summary,
                "theory_text": module_content.theory_text,
                "duration_min": module_content.duration_min,
                "xp_reward": module_content.xp_reward,
                "fixed_qna": [
                    {"q": qna.question, "a": qna.answer}
                    for qna in module_content.qna_pairs.all().order_by('order')
                ],
                "mcqs": [
                    {
                        "id": mcq.mcq_id,
                        "question": mcq.question,
                        "choices": mcq.choices,
                        "correct_choice": mcq.correct_choice,
                        "explanation": mcq.explanation
                    }
                    for mcq in module_content.mcqs.all().order_by('order')
                ],
                "mentor_prompts": [
                    {
                        "user_q": prompt.user_question,
                        "mentor_a": prompt.mentor_answer_seed
                    }
                    for prompt in module_content.mentor_prompts.all().order_by('order')
                ],
                "plaque_card": module_content.plaque_card,
                "metadata": module_content.metadata
            }
        }
        return Response(response_data)
    except ModuleContent.DoesNotExist:
        # Fallback to JSON file if not in database
        courses = load_courses_data()
        course = next((c for c in courses if c.get("id") == course_id), None)
        
        if not course:
            return Response({"error": "Course not found"}, status=404)
        
        module = next((m for m in course.get("modules", []) if m.get("id") == module_id), None)
        
        if not module:
            return Response({"error": "Module not found"}, status=404)
        
        return Response({
            "course": {
                "id": course.get("id"),
                "title": course.get("title"),
                "source": course.get("source")
            },
            "module": module
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_mcq_answer(request, module_id, mcq_id):
    """Submit MCQ answer and award XP"""
    from courses.models import ModuleContent, ModuleMCQ, UserMCQAttempt
    from users.models import UserProfile
    
    try:
        module_content = ModuleContent.objects.get(module_id=module_id)
        mcq = ModuleMCQ.objects.get(module_content=module_content, mcq_id=mcq_id)
        
        selected_choice = request.data.get('selected_choice', '').upper()
        is_correct = (selected_choice == mcq.correct_choice.upper())
        
        # Get or create attempt - allow re-attempts by updating if exists
        attempt, created = UserMCQAttempt.objects.get_or_create(
            user=request.user,
            mcq=mcq,
            defaults={
                'selected_choice': selected_choice,
                'is_correct': is_correct
            }
        )
        
        # Update attempt if re-attempting
        if not created:
            attempt.selected_choice = selected_choice
            attempt.is_correct = is_correct
            attempt.save()
        
        # Award XP if correct and not already awarded
        xp_awarded = 0
        if is_correct:
            # Award XP on first correct attempt only
            if created:
                # Award portion of module XP - ensure at least 15 XP per MCQ for progression
                # Total module XP should be split: 40% MCQs (3 MCQs = ~13% each), 40% flash cards, 20% completion
                total_mcqs = module_content.mcqs.count()
                if total_mcqs > 0:
                    xp_per_mcq = max(15, (module_content.xp_reward * 40) // (100 * total_mcqs))
                else:
                    xp_per_mcq = max(15, module_content.xp_reward // 3)
                
                # Update user profile
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.xp += xp_per_mcq
                profile.save()
                
                attempt.xp_awarded = xp_per_mcq
                attempt.save()
                xp_awarded = xp_per_mcq
            else:
                # Already attempted - return previously awarded XP
                xp_awarded = attempt.xp_awarded or 0
        
        return Response({
            'is_correct': is_correct,
            'correct_choice': mcq.correct_choice,
            'explanation': mcq.explanation,
            'xp_awarded': xp_awarded,
            'user_xp': UserProfile.objects.get(user=request.user).xp
        })
        
    except ModuleContent.DoesNotExist:
        return Response({"error": "Module not found"}, status=404)
    except ModuleMCQ.DoesNotExist:
        return Response({"error": "MCQ not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_flash_cards(request, module_id):
    """Get all flash cards (3-4) for a module"""
    from courses.models import ModuleContent
    
    try:
        module_content = ModuleContent.objects.get(module_id=module_id)
        
        # Generate 3-4 flash cards from module content
        fixed_qna = list(module_content.qna_pairs.all())
        theory_text = module_content.theory_text or ''
        
        flash_cards = []
        
        # Create flash cards from fixed Q&A (up to 4)
        for i, qna in enumerate(fixed_qna[:4]):
            # Split theory text into chunks for key concepts
            theory_sentences = theory_text.split('.') if theory_text else []
            start_idx = (i * len(theory_sentences)) // min(len(fixed_qna), 4) if theory_sentences else 0
            end_idx = ((i + 1) * len(theory_sentences)) // min(len(fixed_qna), 4) if theory_sentences else 0
            
            key_concept_text = '. '.join([s.strip() for s in theory_sentences[start_idx:end_idx] if s.strip()])
            if not key_concept_text:
                key_concept_text = theory_text[:300] if theory_text else module_content.summary or f"Key concepts from {module_content.title}"
            
            flash_cards.append({
                'id': f'flashcard-{i+1}',
                'key_concept': key_concept_text[:400],
                'question': qna.question,
                'answer': qna.answer,
                'reward': {'xp': max(10, (module_content.xp_reward * 20) // 100)}
            })
        
        # If not enough Q&A, create additional flash cards from theory
        while len(flash_cards) < 3 and theory_text:
            idx = len(flash_cards)
            theory_sentences = theory_text.split('.')
            chunk_size = len(theory_sentences) // 3
            start_idx = idx * chunk_size
            end_idx = (idx + 1) * chunk_size if idx < 2 else len(theory_sentences)
            
            key_concept_text = '. '.join([s.strip() for s in theory_sentences[start_idx:end_idx] if s.strip()])
            if key_concept_text:
                flash_cards.append({
                    'id': f'flashcard-{idx+1}',
                    'key_concept': key_concept_text[:400],
                    'question': f"What is the key concept {idx+1} from {module_content.title}?",
                    'answer': module_content.summary or theory_text[:200],
                    'reward': {'xp': max(10, (module_content.xp_reward * 20) // 100)}
                })
        
        # Ensure at least 3 flash cards
        if len(flash_cards) < 3:
            for i in range(len(flash_cards), 3):
                flash_cards.append({
                    'id': f'flashcard-{i+1}',
                    'key_concept': module_content.summary or f"Key concepts from {module_content.title}",
                    'question': f"What is the main concept of {module_content.title}?",
                    'answer': module_content.summary or "Please review the module content.",
                    'reward': {'xp': max(10, (module_content.xp_reward * 20) // 100)}
                })
        
        return Response({
            'flash_cards': flash_cards[:4],  # Max 4 flash cards
            'total': len(flash_cards[:4])
        })
        
    except ModuleContent.DoesNotExist:
        return Response({"error": "Module not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


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

