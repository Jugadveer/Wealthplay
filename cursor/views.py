"""
Cursor API endpoints for Nex mentor interactions
"""
from django .http import JsonResponse 
from django .views .decorators .csrf import csrf_exempt 
from django .views .decorators .http import require_http_methods 
from django .utils .decorators import method_decorator 
from rest_framework .decorators import api_view ,permission_classes 
from rest_framework .permissions import AllowAny 
from rest_framework .response import Response 
from rest_framework import status 
import json 

from .mentor_engine import NexMentorEngine ,add_disclaimer 


@api_view (['POST'])
@permission_classes ([AllowAny ])
def explain (request ):
    """
    POST /api/cursor/explain
    
    Generate structured explanation from Nex mentor
    
    Request body:
    {
        "action": "explain" | "quiz" | "summarize" | "compare" | "next_steps",
        "lesson_id": "investing_basics_01",
        "page_type": "course" | "dashboard" | "scenario",
        "user_context": {
            "user_id": "user_123",
            "demo_balance": 50000,
            "progress": 0.35,
            "confidence_level": "low" | "med" | "high",
            "recent_choices": []
        },
        "requested_depth": "short" | "medium" | "long",
        "allow_web_fetch": true | false,
        "sources": [
            {"label": "Investopedia - Investing Intro", "url": "https://..."}
        ],
        "user_message": "Explain this attachment"
    }
    
    Response:
    {
        "title": "string",
        "explanation": "string",
        "bullet_steps": ["step1", "step2", ...],
        "links": [{"label": "string", "url": "string"}],
        "quiz": {
            "question": "string",
            "options": ["opt1", "opt2", ...],
            "correct_index": 1,
            "explanation": "string"
        },
        "apply_actions": {
            "apply_to_demo_portfolio": true
        }
    }
    """
    try :
        data =request .data if hasattr (request ,'data')else json .loads (request .body )


        required_fields =['action','lesson_id']
        for field in required_fields :
            if field not in data :
                return Response (
                {'error':f'Missing required field: {field }'},
                status =status .HTTP_400_BAD_REQUEST 
                )


        mentor =NexMentorEngine ()


        response =mentor .generate_response (data )


        response =add_disclaimer (response )

        return Response (response ,status =status .HTTP_200_OK )

    except json .JSONDecodeError :
        return Response (
        {'error':'Invalid JSON in request body'},
        status =status .HTTP_400_BAD_REQUEST 
        )
    except Exception as e :
        return Response (
        {'error':f'Internal server error: {str (e )}'},
        status =status .HTTP_500_INTERNAL_SERVER_ERROR 
        )


@api_view (['GET'])
@permission_classes ([AllowAny ])
def health (request ):
    """Health check endpoint"""
    return Response ({'status':'ok','mentor':'Nex'},status =status .HTTP_200_OK )

