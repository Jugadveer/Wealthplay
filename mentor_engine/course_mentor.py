"""
Course Mentor with Two-Layer Response System
1. Fixed Q&A (immediate authoritative answers)
2. Ollama LLM with course context (for additional queries)
"""
import json
import os
import difflib
from django.conf import settings
from ollama import Client

# Load courses JSON
COURSES_JSON_PATH = os.path.join(settings.BASE_DIR, 'financial_course.json')

# Load courses at module level
COURSES_DATA = None

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
        if isinstance(messages, list):
            for i, msg in enumerate(messages):
                text = msg.get('text', '')
                
                # If message contains Q&A pattern
                if 'Q:' in text or ('?' in text and len(text) > 10):
                    # Try to find answer in next message
                    if i + 1 < len(messages):
                        answer_text = messages[i + 1].get('text', '')
                        if answer_text and len(answer_text) > 5:
                            fixed_qna.append({
                                'q': text.replace('Q:', '').strip(),
                                'a': answer_text.replace('A:', '').strip()
                            })
        
        # Ensure fixed_qna is always a list
        if not isinstance(fixed_qna, list):
            fixed_qna = []
        
        module = {
            'id': lesson.get('id', ''),
            'title': lesson.get('title', ''),
            'summary': lesson.get('title', ''),
            'fixed_qna': fixed_qna
        }
        modules.append(module)
    
    # Calculate duration estimate (5 mins per lesson)
    duration_mins = len(lessons) * 5
    
    course = {
        'id': topic.get('id', ''),
        'title': topic.get('title', ''),
        'overview': topic.get('summary', topic.get('title', '')),
        'duration_mins': duration_mins,
        'source': '',
        'modules': modules
    }
    
    return course


def load_courses():
    """Load courses from JSON file - use as-is, no transformation"""
    global COURSES_DATA
    if COURSES_DATA is None:
        try:
            with open(COURSES_JSON_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct array of courses (expected format)
                COURSES_DATA = data
                print(f"Mentor engine: Loaded {len(COURSES_DATA)} courses")
            elif isinstance(data, dict):
                # Object with 'topics' or 'courses' key
                if 'topics' in data and isinstance(data['topics'], list):
                    # Transform topics to courses format
                    topics = data['topics']
                    COURSES_DATA = [transform_topic_to_course(topic) for topic in topics]
                    print(f"Mentor engine: Loaded {len(COURSES_DATA)} courses (transformed from topics)")
                elif 'courses' in data and isinstance(data['courses'], list):
                    COURSES_DATA = data['courses']
                    print(f"Mentor engine: Loaded {len(COURSES_DATA)} courses")
                else:
                    print(f"Mentor engine: JSON structure not recognized. Keys: {list(data.keys())}")
                    COURSES_DATA = []
            else:
                print(f"Mentor engine: Unexpected JSON structure: {type(data)}")
                COURSES_DATA = []
        except Exception as e:
            print(f"Mentor engine: Error loading courses: {e}")
            import traceback
            traceback.print_exc()
            COURSES_DATA = []
    return COURSES_DATA


def find_course(course_id):
    """Find a course by ID"""
    courses = load_courses()
    
    # Ensure courses is a list
    if not isinstance(courses, list):
        print(f"ERROR: Courses is not a list, type: {type(courses)}")
        return None
    
    if not course_id:
        print(f"ERROR: course_id is empty")
        return None
    
    print(f"Looking for course_id: '{course_id}' in {len(courses)} courses")
    
    for course in courses:
        if isinstance(course, dict):
            course_id_val = course.get("id")
            print(f"  Checking course: '{course_id_val}' == '{course_id}'? {course_id_val == course_id}")
            if course_id_val == course_id:
                print(f"  FOUND course: {course.get('title')}")
                return course
    
    print(f"  Course '{course_id}' NOT FOUND")
    return None


def find_module(course, module_id=None):
    """Find a module within a course"""
    if not course or not isinstance(course, dict):
        return None
    
    modules = course.get("modules", [])
    if not isinstance(modules, list) or not modules:
        return None
    
    if module_id:
        for module in modules:
            if isinstance(module, dict) and module.get("id") == module_id:
                return module
    
    # Return first module if no ID specified
    return modules[0] if modules else None


def fuzzy_match_q(fixed_qna, user_q, cutoff=0.7):
    """
    Find best question match using fuzzy matching
    Returns the matching Q&A if found, None otherwise
    """
    if not fixed_qna:
        return None
    
    best = None
    best_score = 0
    
    for qa in fixed_qna:
        q = qa.get("q", "").lower()
        score = difflib.SequenceMatcher(None, q, user_q.lower()).ratio()
        if score > best_score:
            best_score = score
            best = qa
    
    return best if best_score >= cutoff else None


def generate_ollama_response(course, module, user_question, ollama_model="phi3"):
    """
    Generate response using Ollama with course context and few-shot examples
    """
    try:
        ollama_host = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
        ollama = Client(host=ollama_host)
        
        # Handle empty or None model string
        if not ollama_model or ollama_model.strip() == '':
            ollama_model = "phi3"
        
        # Test connection by listing models
        try:
            models = ollama.list()
            model_names = [m.get('name', '') for m in models.get('models', [])]
            # Try common model names if phi3 is not available
            if ollama_model not in model_names:
                if 'llama3' in model_names:
                    ollama_model = 'llama3'
                elif 'llama2' in model_names:
                    ollama_model = 'llama2'
                elif 'mistral' in model_names:
                    ollama_model = 'mistral'
                elif len(model_names) > 0:
                    ollama_model = model_names[0]
                else:
                    raise Exception("No Ollama models found. Please install a model: ollama pull llama3")
        except Exception as e:
            raise Exception(f"Could not connect to Ollama at {ollama_host}: {str(e)}. Please ensure Ollama is running.")
    except Exception as e:
        raise Exception(f"Could not connect to Ollama: {str(e)}. Please ensure Ollama is running.")
    
    # Build system prompt
    system_prompt = """You are an empathetic, practical financial mentor speaking to first-time earners. Keep answers short (2-4 short paragraphs), avoid jargon unless user asks for definitions, include one simple actionable next-step and note sources. When unsure, say you are unsure and suggest where to learn (cite module source)."""
    
    # Build context message
    context_msg = f"""Course: {course.get('title', '')}
Module: {module.get('title', '')}
Module Summary: {module.get('summary', '')}
Source: {course.get('source', '')}"""
    
    # Build few-shot examples from fixed Q&A or database
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "system", "content": context_msg}
    ]
    
    # Try to get enriched content from database first
    fixed_qna = module.get("fixed_qna", [])
    if not fixed_qna:
        # Try loading from database
        try:
            from courses.models import ModuleContent
            full_module_id = f"{course.get('id', '')}_{module.get('id', '')}"
            try:
                module_content = ModuleContent.objects.get(module_id=full_module_id)
                # Get Q&A from database
                qna_pairs = module_content.qna_pairs.all()[:3]
                fixed_qna = [{"q": qa.question, "a": qa.answer} for qa in qna_pairs]
                # Also add theory text to context
                if module_content.theory_text:
                    theory_context = f"Theory: {module_content.theory_text[:300]}"
                    messages.append({"role": "system", "content": theory_context})
            except ModuleContent.DoesNotExist:
                pass
        except Exception as e:
            print(f"Could not load from database: {e}")
    
    # Add up to 3 fixed Q&A as few-shot examples
    for qa in fixed_qna[:3]:
        if isinstance(qa, dict):
            messages.append({"role": "user", "content": qa.get("q", "")})
            messages.append({"role": "assistant", "content": qa.get("a", "")})
    
    # Add user's question
    messages.append({"role": "user", "content": user_question})
    
    try:
        # Call Ollama chat API with timeout
        import requests
        response = ollama.chat(
            model=ollama_model,
            messages=messages,
            options={
                'temperature': 0.7,
                'top_p': 0.9
            }
        )
        
        answer = response.get("message", {}).get("content", "")
        if not answer:
            raise Exception("Empty response from Ollama")
        return answer
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Could not connect to Ollama server. Please ensure Ollama is running on {ollama_host}")
    except Exception as e:
        error_msg = str(e)
        if "model" in error_msg.lower() or "not found" in error_msg.lower():
            raise Exception(f"Model '{ollama_model}' not found. Please install it: ollama pull {ollama_model}")
        raise Exception(f"Ollama error: {error_msg}")


def mentor_respond(course_id, module_id=None, question=""):
    """
    Main mentor response function with two-layer system:
    1. Check fixed Q&A (fuzzy match)
    2. If no match, use Ollama with context
    """
    if not question:
        return {
            "type": "error",
            "answer": "Please provide a question.",
            "confidence": 0
        }
    
    # Find course and module
    course = find_course(course_id)
    if not course:
        return {
            "type": "error",
            "answer": f"Course '{course_id}' not found.",
            "confidence": 0
        }
    
    module = find_module(course, module_id)
    if not module:
        return {
            "type": "error",
            "answer": f"Module not found in course '{course_id}'.",
            "confidence": 0
        }
    
    # Layer 1: Check fixed Q&A (from JSON or database)
    fixed_qna = module.get("fixed_qna", [])
    
    # Try to get enriched Q&A from database if not in module
    if not fixed_qna:
        try:
            from courses.models import ModuleContent
            full_module_id = f"{course_id}_{module_id or ''}"
            try:
                module_content = ModuleContent.objects.get(module_id=full_module_id)
                qna_pairs = module_content.qna_pairs.all()
                fixed_qna = [{"q": qa.question, "a": qa.answer} for qa in qna_pairs]
            except ModuleContent.DoesNotExist:
                pass
        except Exception as e:
            print(f"Could not load Q&A from database: {e}")
    
    match = fuzzy_match_q(fixed_qna, question, cutoff=0.7)
    
    if match:
        return {
            "type": "fixed_qna",
            "answer": match.get("a", ""),
            "source": course.get("source", ""),
            "confidence": 0.99,
            "matched_question": match.get("q", "")
        }
    
    # Layer 2: Use Ollama with course context
    try:
        # Get Ollama model from environment or use default
        ollama_model = os.environ.get("OLLAMA_MODEL", "phi3")
        # Handle empty string
        if not ollama_model or ollama_model.strip() == '':
            ollama_model = "phi3"
        
        answer = generate_ollama_response(course, module, question, ollama_model)
        
        return {
            "type": "llm",
            "answer": answer,
            "source": course.get("source", ""),
            "confidence": 0.85
        }
    except Exception as e:
        # If Ollama fails, provide a helpful fallback response using module content
        module_summary = module.get("summary", "")
        theory_text = module.get("theory_text", "")
        
        # Try to get enriched content from database
        try:
            from courses.models import ModuleContent
            full_module_id = f"{course_id}_{module_id or ''}"
            try:
                module_content = ModuleContent.objects.get(module_id=full_module_id)
                theory_text = module_content.theory_text or theory_text
                module_summary = module_content.summary or module_summary
            except ModuleContent.DoesNotExist:
                pass
        except:
            pass
        
        # Create a fallback answer from module content
        if theory_text:
            fallback_answer = f"Based on {module.get('title', 'this module')}: {theory_text[:200]}..."
        elif module_summary:
            fallback_answer = f"{module_summary} This is educational content about {module.get('title', 'this topic')}."
        else:
            fallback_answer = f"I can help explain {module.get('title', 'this topic')}. Please check if Ollama is running for detailed AI responses, or refer to the module content above."
        
        return {
            "type": "fallback",
            "answer": fallback_answer + f"\n\nNote: Full AI responses require Ollama to be running. Error: {str(e)[:100]}",
            "source": course.get("source", ""),
            "confidence": 0.6
        }

