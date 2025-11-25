from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import ChatMessage, Attachment, TopicChatMessage
from .serializers import ChatMessageSerializer, ChatMessageCreateSerializer, AttachmentSerializer
from courses.models import Lesson

# Import mentor engines
import sys
import os
from django.conf import settings
sys.path.insert(0, os.path.join(settings.BASE_DIR, 'mentor_engine'))
try:
    from mentor import generate_response as generate_rag_response
    RAG_MENTOR_AVAILABLE = True
except Exception as e:
    RAG_MENTOR_AVAILABLE = False
    RAG_MENTOR_ERROR = str(e)

try:
    # Try importing from mentor_engine first
    try:
        from mentor_engine.course_mentor import mentor_respond as course_mentor_respond_func, load_courses
    except ImportError:
        # Fallback to direct import (if sys.path was modified)
        from course_mentor import mentor_respond as course_mentor_respond_func, load_courses
    COURSE_MENTOR_AVAILABLE = True
except Exception as e:
    COURSE_MENTOR_AVAILABLE = False
    COURSE_MENTOR_ERROR = str(e)


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            return ChatMessage.objects.filter(lesson_id=lesson_id).order_by('created_at')
        return ChatMessage.objects.all().order_by('-created_at')[:50]

    def create(self, request, *args, **kwargs):
        serializer = ChatMessageCreateSerializer(data=request.data)
        if serializer.is_valid():
            lesson_id = request.data.get('lesson_id')
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

            message = ChatMessage.objects.create(
                lesson=lesson,
                sender=serializer.validated_data.get('sender', 'user'),
                text=serializer.validated_data.get('text', ''),
                time_display=serializer.validated_data.get('time_display', timezone.now().strftime('%H:%M'))
            )

            serializer_response = ChatMessageSerializer(message)
            return Response(serializer_response.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def by_lesson(self, request):
        lesson_id = request.query_params.get('lesson_id')
        if not lesson_id:
            return Response({'error': 'lesson_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lesson = Lesson.objects.get(id=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'error': 'Lesson not found'}, status=status.HTTP_404_NOT_FOUND)

        messages = ChatMessage.objects.filter(lesson=lesson).order_by('created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class AttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer


# Mentor Chatbot Endpoint (RAG-based - original)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def mentor_respond_rag(request):
    """Mentor chatbot endpoint using Ollama + RAG (vector DB)"""
    if not RAG_MENTOR_AVAILABLE:
        return JsonResponse({
            "reply": "Sorry, the mentor is currently unavailable. Please check if Ollama is running and the model is installed."
        }, status=503)
    
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        user_message = data.get("message", "")
        
        if not user_message:
            return JsonResponse({"reply": "Please provide a message."}, status=400)
        
        # Generate response using RAG mentor engine
        reply = generate_rag_response(user_message)
        
        return JsonResponse({"reply": reply})
    except Exception as e:
        return JsonResponse({
            "reply": f"Sorry, I encountered an error: {str(e)}"
        }, status=500)


# Course Mentor Endpoint (Two-layer: Fixed Q&A + Ollama)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def mentor_respond(request):
    """
    Course mentor endpoint with two-layer response:
    1. Fixed Q&A (immediate authoritative answers)
    2. Ollama LLM with course context (for additional queries)
    """
    # Always try to respond, even if Ollama is unavailable (will use fixed Q&A or fallback)
    # The mentor_respond function handles fallbacks internally
    
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        course_id = data.get("course_id", "")
        module_id = data.get("module_id", None)
        question = data.get("question", "")
        
        if not question:
            return JsonResponse({
                "reply": "Please provide a question.",
                "type": "error"
            }, status=400)
        
        if not course_id:
            return JsonResponse({
                "reply": "Please provide a course_id.",
                "type": "error"
            }, status=400)
        
        # Save user message to topic chat if user is authenticated
        user = request.user if request.user.is_authenticated else None
        if user:
            TopicChatMessage.objects.create(
                user=user,
                course_id=course_id,
                module_id=module_id or "",
                sender='user',
                text=question,
                time_display=timezone.now().strftime('%H:%M')
            )
        
        # Hardcoded simple response for now
        question_lower = question.lower().strip()
        if question_lower in ['hey', 'hi', 'hello', 'hi there', 'hey there']:
            # Get course/topic name
            from courses.models import Course, Topic
            course_name = "this course"
            try:
                course = Course.objects.get(id=course_id)
                course_name = course.title
            except:
                pass
            
            answer = f"Hey, I am here to take your doubts about {course_name}. How can I help you?"
            reply = answer
            reply_type = "fixed"
        else:
            # For other questions, use the course mentor function
            result = course_mentor_respond_func(course_id, module_id, question)
            
            # Handle case where result might be a string (error case)
            if isinstance(result, str):
                return JsonResponse({
                    "reply": result,
                    "type": "error"
                })
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                return JsonResponse({
                    "reply": str(result) if result else "No response generated.",
                    "type": "llm"
                })
            
            answer = result.get("answer", "")
            reply = result.get("answer", "") or result.get("reply", "")
            reply_type = result.get("type", "llm")
        
        # Save mentor response to topic chat if user is authenticated
        if user and answer:
            TopicChatMessage.objects.create(
                user=user,
                course_id=course_id,
                module_id=module_id or "",
                sender='nex',
                text=answer,
                time_display=timezone.now().strftime('%H:%M')
            )
        
        return JsonResponse({
            "reply": reply,
            "answer": reply,  # Also include "answer" key
            "type": reply_type,
            "source": result.get("source", "") if 'result' in locals() else "",
            "confidence": result.get("confidence", 0) if 'result' in locals() else 0,
            "matched_question": result.get("matched_question", None) if 'result' in locals() else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "reply": f"Sorry, I encountered an error: {str(e)}",
            "type": "error"
        }, status=500)


# General Inquiry Endpoint (Ollama without course context)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def general_inquiry(request):
    """
    General inquiry endpoint for New Inquiry button
    Uses Ollama LLM directly without course context
    """
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        question = data.get("question", "")
        
        if not question:
            return JsonResponse({
                "reply": "Please provide a question.",
                "type": "error"
            }, status=400)
        
        # Use Ollama directly for general inquiries
        try:
            from ollama import Client
            ollama = Client()
            
            system_prompt = """You are a helpful financial advisor assistant for WealthPlay. 
            Provide clear, practical advice about financial topics. Keep answers concise and actionable."""
            
            response = ollama.chat(
                model=os.environ.get("OLLAMA_MODEL", "phi3"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]
            )
            
            answer = response.get("message", {}).get("content", "")
            
            return JsonResponse({
                "reply": answer,
                "type": "llm"
            })
        except Exception as e:
            return JsonResponse({
                "reply": f"Sorry, I encountered an error connecting to Ollama: {str(e)}. Please ensure Ollama is running.",
                "type": "error"
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            "reply": f"Sorry, I encountered an error: {str(e)}",
            "type": "error"
        }, status=500)


# Topic-specific chat history endpoints
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_topic_chat(request, course_id, module_id=''):
    """Get chat history for a specific topic (course + module)"""
    user = request.user if request.user.is_authenticated else None
    if not user:
        return JsonResponse({"messages": []})
    
    # Handle optional module_id from URL
    if not module_id or module_id == 'None':
        module_id = ''
    
    messages = TopicChatMessage.objects.filter(
        user=user,
        course_id=course_id,
        module_id=module_id
    ).order_by('created_at')
    
    messages_data = [{
        "sender": msg.sender,
        "text": msg.text,
        "time_display": msg.time_display,
        "created_at": msg.created_at.isoformat()
    } for msg in messages]
    
    return JsonResponse({"messages": messages_data})


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def save_topic_message(request):
    """Save a single message to topic chat"""
    user = request.user if request.user.is_authenticated else None
    if not user:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    try:
        data = request.data if hasattr(request, 'data') else json.loads(request.body)
        course_id = data.get("course_id", "")
        module_id = data.get("module_id", "")
        sender = data.get("sender", "user")
        text = data.get("text", "")
        
        if not course_id or not text:
            return JsonResponse({"error": "course_id and text are required"}, status=400)
        
        message = TopicChatMessage.objects.create(
            user=user,
            course_id=course_id,
            module_id=module_id or "",
            sender=sender,
            text=text,
            time_display=timezone.now().strftime('%H:%M')
        )
        
        return JsonResponse({
            "id": message.id,
            "sender": message.sender,
            "text": message.text,
            "time_display": message.time_display
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
