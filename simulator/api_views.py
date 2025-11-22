"""
API views for scenario quiz - returns JSON for React frontend
"""
import json
import random
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Scenario, DecisionOption, QuizRun


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz_api(request):
    """Start a new quiz session - returns JSON with runId"""
    try:
        # Get all scenario IDs
        all_ids = list(Scenario.objects.values_list('id', flat=True))
        
        if len(all_ids) == 0:
            return Response({'error': 'No scenarios available'}, status=404)
        
        if len(all_ids) < 5:
            selected_ids = all_ids
        else:
            selected_ids = random.sample(all_ids, 5)
        
        id_string = ",".join(map(str, selected_ids))
        
        # Create a new Quiz Session
        run = QuizRun.objects.create(
            user=request.user,
            scenario_ids=id_string,
            current_question_index=0,
            total_score=0
        )
        
        return Response({
            'success': True,
            'runId': run.id,
            'redirect': f'/scenario/quiz/{run.id}'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_question(request, run_id):
    """Get current quiz question - returns JSON"""
    try:
        run = get_object_or_404(QuizRun, id=run_id, user=request.user)
        
        if run.is_completed:
            return Response({
                'completed': True,
                'redirect': f'/scenario/quiz/{run_id}/result'
            })
        
        scenario_list = run.get_scenario_list()
        
        # Safety checks
        if not scenario_list or len(scenario_list) == 0:
            run.is_completed = True
            run.save()
            return Response({'error': 'No scenarios in quiz', 'completed': True}, status=400)
        
        if run.current_question_index >= len(scenario_list):
            run.is_completed = True
            run.save()
            return Response({
                'completed': True,
                'redirect': f'/scenario/quiz/{run_id}/result'
            })
        
        current_scenario_id = scenario_list[run.current_question_index]
        scenario = get_object_or_404(Scenario, id=current_scenario_id)
        
        options_data = []
        for option in scenario.options.all():
            options_data.append({
                'id': option.id,
                'text': option.text,
                'type': option.decision_type,
                'score': option.score,
                'impact': {
                    'balance': float(option.balance_impact),
                    'confidence': option.confidence_delta,
                    'risk': option.risk_score_delta,
                    'growth_rate': float(option.future_growth_rate)
                },
                'content': {
                    'why_matters': option.why_it_matters,
                    'mentor': option.mentor_feedback
                }
            })
        
        return Response({
            'run_id': run.id,
            'scenario': {
                'id': scenario.id,
                'title': scenario.title,
                'description': scenario.description,
                'starting_balance': float(scenario.starting_balance),
            },
            'question_number': run.current_question_index + 1,
            'total_questions': len(scenario_list),
            'choices': options_data,
            'total_score': run.total_score,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer_api(request):
    """Submit quiz answer - returns JSON"""
    try:
        run_id = request.data.get('run_id')
        score = request.data.get('score')
        option_id = request.data.get('option_id')
        
        if not run_id or score is None:
            return Response({'error': 'Missing run_id or score'}, status=400)
        
        run = get_object_or_404(QuizRun, id=run_id, user=request.user)
        
        if not run.is_completed:
            score_value = int(score) if score else 0
            if score_value >= 0:
                run.total_score += score_value
                run.save()
                
                # Award XP
                from users.models import UserProfile
                try:
                    profile = UserProfile.objects.get(user=request.user)
                    xp_to_award = min(score_value, 20)
                    profile.xp += xp_to_award
                    profile.save()
                except Exception:
                    pass
        
        run.refresh_from_db()
        
        # Check if there are more questions
        scenario_list = run.get_scenario_list()
        has_more = run.current_question_index + 1 < len(scenario_list)
        
        return Response({
            'success': True,
            'total_score': run.total_score,
            'score_added': int(score) if score else 0,
            'has_more': has_more,
            'next_url': f'/scenario/quiz/{run_id}/next' if has_more else None,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def next_question_api(request, run_id):
    """Move to next question - returns JSON"""
    try:
        run = get_object_or_404(QuizRun, id=run_id, user=request.user)
        scenario_list = run.get_scenario_list()
        
        if run.current_question_index + 1 >= len(scenario_list):
            run.is_completed = True
            run.save()
            return Response({
                'completed': True,
                'redirect': f'/scenario/quiz/{run_id}/result'
            })
        
        run.current_question_index += 1
        run.save()
        
        return Response({
            'success': True,
            'redirect': f'/scenario/quiz/{run_id}'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_result(request, run_id):
    """Get quiz result - returns JSON"""
    try:
        run = get_object_or_404(QuizRun, id=run_id, user=request.user)
        scenario_list = run.get_scenario_list()
        total_possible_score = len(scenario_list) * 20
        
        if total_possible_score == 0:
            percentage = 0
        else:
            percentage = (run.total_score / total_possible_score) * 100
        
        badge = "Financial Novice"
        badge_color = "gray"
        
        if percentage >= 80:
            badge = "Wealth Master"
            badge_color = "gold"
        elif percentage >= 50:
            badge = "Smart Saver"
            badge_color = "silver"
        elif percentage >= 30:
            badge = "Budding Investor"
            badge_color = "bronze"
        
        return Response({
            'run_id': run.id,
            'total_score': run.total_score,
            'max_score': total_possible_score,
            'percentage': int(percentage),
            'badge': badge,
            'badge_color': badge_color,
            'total_questions': len(scenario_list),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

