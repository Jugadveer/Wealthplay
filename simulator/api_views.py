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
from .models import Scenario, DecisionOption, QuizRun, UserScenarioAttempt
from users.models import UserProfile, ChallengeLeaderboard
from django.utils import timezone
from datetime import timedelta


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz_api(request):
    """Start a new quiz session - returns JSON with runId"""
    try:
        # Get all scenario IDs
        all_ids = list(Scenario.objects.values_list('id', flat=True))
        
        if len(all_ids) == 0:
            return Response({'error': 'No scenarios available'}, status=404)
        
        # Select 5 random scenarios (or all if less than 5)
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
            'scenario_ids': run.scenario_ids,  # Add scenario_ids for frontend
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
    """Submit quiz answer - tracks user attempt but doesn't award XP yet (awarded on result view)"""
    try:
        run_id = request.data.get('run_id')
        score = request.data.get('score')
        option_id = request.data.get('option_id')
        
        if not run_id or score is None or not option_id:
            return Response({'error': 'Missing run_id, score, or option_id'}, status=400)
        
        try:
            run = QuizRun.objects.get(id=run_id, user=request.user)
        except QuizRun.DoesNotExist:
            return Response({
                'error': 'QuizRun not found. Please start a new quiz.',
                'redirect': '/scenario'
            }, status=404)
        
        if not run.is_completed:
            # Get the current scenario to find the highest scoring option
            scenario_list = run.get_scenario_list()
            if run.current_question_index < len(scenario_list):
                current_scenario_id = scenario_list[run.current_question_index]
                scenario = get_object_or_404(Scenario, id=current_scenario_id)
                
                # Find the highest score among all options for this scenario
                all_options = scenario.options.all()
                max_score = max((opt.score for opt in all_options), default=0)
                
                # Convert option_id to integer if it's a string
                try:
                    option_id_int = int(option_id)
                except (ValueError, TypeError):
                    return Response({
                        'error': f'Invalid option_id: {option_id}. Must be an integer.',
                        'debug': {
                            'option_id': option_id,
                            'option_id_type': type(option_id).__name__,
                            'scenario_id': current_scenario_id,
                            'available_option_ids': [opt.id for opt in all_options]
                        }
                    }, status=400)
                
                # Get the selected option - try without scenario constraint first for better error message
                try:
                    selected_option = DecisionOption.objects.get(id=option_id_int)
                    # Verify it belongs to the scenario
                    if selected_option.scenario_id != scenario.id:
                        return Response({
                            'error': f'Option {option_id_int} does not belong to scenario {scenario.id}',
                            'debug': {
                                'option_scenario_id': selected_option.scenario_id,
                                'current_scenario_id': scenario.id,
                                'available_option_ids': [opt.id for opt in all_options]
                            }
                        }, status=400)
                except DecisionOption.DoesNotExist:
                    return Response({
                        'error': f'DecisionOption with id {option_id_int} does not exist',
                        'debug': {
                            'option_id': option_id_int,
                            'scenario_id': current_scenario_id,
                            'available_option_ids': [opt.id for opt in all_options]
                        }
                    }, status=404)
                score_value = int(score) if score else selected_option.score
                
                # Award points based on score:
                # - Highest score (correct answer): full points (20)
                # - Medium score (neutral choice): 10 points
                # - Low score (wrong answer): 5 points
                is_correct = score_value >= max_score and score_value > 0
                
                if is_correct:
                    # Best answer - full points
                    run.total_score += score_value
                    run.save()
                elif score_value > 0:
                    # Neutral/moderate answer - give partial points (10 or 5)
                    # If score is between max_score/2 and max_score, give 10 points
                    # Otherwise give 5 points
                    if score_value >= max_score / 2:
                        partial_score = 10
                    else:
                        partial_score = 5
                    run.total_score += partial_score
                    run.save()
                    score_value = partial_score
                else:
                    # Wrong answer - no points
                    score_value = 0
                
                # Track user attempt (create or update)
                attempt, created = UserScenarioAttempt.objects.update_or_create(
                    user=request.user,
                    scenario=scenario,
                    quiz_run=run,
                    defaults={
                        'chosen_option': selected_option,
                        'score_earned': score_value,
                        'is_correct': is_correct,
                        'xp_awarded': 0,  # Will be awarded when viewing results
                    }
                )
            else:
                # Already completed
                is_correct = False
                score_value = 0
        else:
            is_correct = False
            score_value = 0
        
        run.refresh_from_db()
        
        # Check if there are more questions (don't auto-advance - let frontend handle it)
        scenario_list = run.get_scenario_list()
        has_more = run.current_question_index + 1 < len(scenario_list)
        
        # Don't auto-advance - frontend will handle it when user clicks "Next Question"
        # This allows user to explore other options before moving on
        
        return Response({
            'success': True,
            'total_score': run.total_score,
            'score_added': score_value,
            'is_correct': is_correct,
            'has_more': has_more,
            'current_question_index': run.current_question_index,  # Return current index
            'next_url': f'/scenario/quiz/{run_id}' if has_more else f'/scenario/quiz/{run_id}/result',
        })
    except Exception as e:
        import traceback
        print(f"Error in submit_answer_api: {e}")
        print(traceback.format_exc())
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
def get_scenarios_list(request):
    """Get list of all available scenarios"""
    try:
        scenarios = Scenario.objects.all()
        scenarios_data = []
        for scenario in scenarios:
            scenarios_data.append({
                'id': scenario.id,
                'title': scenario.title,
                'description': scenario.description,
                'starting_balance': float(scenario.starting_balance),
            })
        return Response(scenarios_data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_scenario_detail(request, scenario_id):
    """Get a single scenario with all its options"""
    try:
        scenario = get_object_or_404(Scenario, id=scenario_id)
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
            'id': scenario.id,
            'title': scenario.title,
            'description': scenario.description,
            'starting_balance': float(scenario.starting_balance),
            'choices': options_data,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_result(request, run_id):
    """Get quiz result and check for achievements"""
    """Get quiz result - awards XP and updates streaks when viewing results"""
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
        xp_awarded = 0
        
        # Award XP only once when viewing results
        if not run.xp_awarded:
            # Get all attempts for this quiz run
            attempts = UserScenarioAttempt.objects.filter(
                user=request.user,
                quiz_run=run,
                xp_awarded=0  # Only award XP for attempts not yet awarded
            )
            
            total_xp = 0
            correct_count = 0
            
            for attempt in attempts:
                # Award XP based on score (1 XP per point, max 20 XP per question)
                xp_for_attempt = min(attempt.score_earned, 20)
                attempt.xp_awarded = xp_for_attempt
                attempt.save()
                total_xp += xp_for_attempt
                
                if attempt.is_correct:
                    correct_count += 1
            
            # Bonus XP based on percentage
            if percentage >= 80:
                badge = "Wealth Master"
                badge_color = "gold"
                bonus_xp = 100
            elif percentage >= 50:
                badge = "Smart Saver"
                badge_color = "silver"
                bonus_xp = 50
            elif percentage >= 30:
                badge = "Budding Investor"
                badge_color = "bronze"
                bonus_xp = 25
            else:
                bonus_xp = 10  # Completion reward
            
            total_xp += bonus_xp
            xp_awarded = total_xp
            
            # Update user profile XP
            try:
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                profile.xp += total_xp
                profile.save()
            except Exception as e:
                print(f"Error updating user profile XP: {e}")
            
            # Update streak and leaderboard
            try:
                leaderboard, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
                
                # Update streak logic
                # Check if user had a correct answer in this quiz
                if correct_count > 0:
                    # Check last attempt date to determine if streak continues
                    last_attempt = UserScenarioAttempt.objects.filter(
                        user=request.user
                    ).exclude(quiz_run=run).order_by('-attempt_date').first()
                    
                    if last_attempt:
                        # Check if last attempt was today or yesterday (within 24 hours)
                        time_diff = timezone.now() - last_attempt.attempt_date
                        if time_diff <= timedelta(days=1):
                            # Continue streak
                            leaderboard.current_streak += 1
                        else:
                            # Reset streak (gap too long)
                            leaderboard.current_streak = 1
                    else:
                        # First attempt
                        leaderboard.current_streak = 1
                    
                    # Update best streak
                    if leaderboard.current_streak > leaderboard.best_streak:
                        leaderboard.best_streak = leaderboard.current_streak
                else:
                    # No correct answers - reset streak
                    leaderboard.current_streak = 0
                
                # Update totals
                leaderboard.total_score += run.total_score
                leaderboard.total_predictions += len(scenario_list)
                leaderboard.correct_predictions += correct_count
                leaderboard.save()
            except Exception as e:
                print(f"Error updating leaderboard: {e}")
            
            # Mark XP as awarded
            run.xp_awarded = True
            run.save()
        
        # Get streak info from leaderboard
        try:
            leaderboard = ChallengeLeaderboard.objects.get(user=request.user)
            streak = leaderboard.current_streak
        except ChallengeLeaderboard.DoesNotExist:
            streak = 0
        
        return Response({
            'run_id': run.id,
            'total_score': run.total_score,
            'max_score': total_possible_score,
            'percentage': int(percentage),
            'badge': badge,
            'badge_color': badge_color,
            'total_questions': len(scenario_list),
            'xp_awarded': xp_awarded,
            'streak': streak,
        })
    except Exception as e:
        import traceback
        print(f"Error in get_quiz_result: {e}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)

