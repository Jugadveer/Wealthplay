import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Scenario, DecisionOption, UserScenarioLog, QuizRun, UserScenarioAttempt
from users.models import UserProfile, ChallengeLeaderboard
from django.utils import timezone
from datetime import timedelta

# 1. START A NEW QUIZ (Random 5)
@login_required(login_url='/')
def start_quiz(request):
    # Get all scenario IDs
    all_ids = list(Scenario.objects.values_list('id', flat=True))
    
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
    
    return redirect('play_quiz_question', run_id=run.id)

# 2. PLAY CURRENT QUESTION
@login_required(login_url='/')
def play_quiz_question(request, run_id):
    run = get_object_or_404(QuizRun, id=run_id, user=request.user)
    
    if run.is_completed:
        return redirect('quiz_result', run_id=run.id)

    scenario_list = run.get_scenario_list()
    
    # Safety check for empty or invalid scenario list
    if not scenario_list or len(scenario_list) == 0:
        run.is_completed = True
        run.save()
        return redirect('scenario_home')
    
    # Safety check for index out of bounds
    if run.current_question_index >= len(scenario_list):
        run.is_completed = True
        run.save()
        return redirect('quiz_result', run_id=run.id)

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

    game_config = {
        'run_id': run.id,
        'scenario_id': scenario.id,
        'question_number': run.current_question_index + 1,
        'total_questions': len(scenario_list),
        'start_balance': float(scenario.starting_balance),
        'choices': options_data
    }

    return render(request, 'scenario_play.html', {
        'scenario': scenario,
        'game_config': game_config # FIXED: Matches template variable name
    })

# 3. SUBMIT ANSWER (AJAX)
@csrf_exempt
@login_required(login_url='/')
def submit_quiz_answer(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            run_id = data.get('run_id')
            score = data.get('score')
            option_id = data.get('option_id')
            
            # Validate inputs
            if not run_id or score is None:
                return JsonResponse({'status': 'error', 'message': 'Missing run_id or score'}, status=400)
            
            run = get_object_or_404(QuizRun, id=run_id, user=request.user)
            
            # Only update if quiz is not completed and score is valid
            if not run.is_completed:
                score_value = int(score) if score else 0
                if score_value >= 0:  # Ensure score is non-negative
                    run.total_score += score_value
                    run.save()
                    
                    # Track user attempt
                    scenario_list = run.get_scenario_list()
                    if run.current_question_index < len(scenario_list):
                        current_scenario_id = scenario_list[run.current_question_index]
                        scenario = get_object_or_404(Scenario, id=current_scenario_id)
                        
                        # Find max score for this scenario
                        all_options = scenario.options.all()
                        max_score = max((opt.score for opt in all_options), default=0)
                        is_correct = score_value >= max_score and score_value > 0
                        
                        # Get selected option if provided
                        chosen_option = None
                        if option_id:
                            try:
                                chosen_option = DecisionOption.objects.get(id=option_id, scenario=scenario)
                            except DecisionOption.DoesNotExist:
                                pass
                        
                        # Track attempt (XP will be awarded when viewing results)
                        UserScenarioAttempt.objects.update_or_create(
                            user=request.user,
                            scenario=scenario,
                            quiz_run=run,
                            defaults={
                                'chosen_option': chosen_option,
                                'score_earned': score_value,
                                'is_correct': is_correct,
                                'xp_awarded': 0,  # Will be awarded when viewing results
                            }
                        )
            
            # Refresh from database to get latest total_score
            run.refresh_from_db()
            return JsonResponse({
                'status': 'success', 
                'total_score': run.total_score,
                'score_added': int(score) if score else 0
            })
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
        except Exception as e:
            import traceback
            print(f"Error in submit_quiz_answer: {e}")
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Only POST allowed'}, status=400)

# 4. NEXT QUESTION LOGIC
@login_required(login_url='/')
def next_question(request, run_id):
    run = get_object_or_404(QuizRun, id=run_id, user=request.user)
    
    scenario_list = run.get_scenario_list()
    
    # Check if quiz is complete
    if run.current_question_index + 1 >= len(scenario_list):
        run.is_completed = True
        run.save()
        return redirect('quiz_result', run_id=run.id)
    
    run.current_question_index += 1
    run.save()
    
    return redirect('play_quiz_question', run_id=run.id)

# 5. QUIZ RESULT PAGE
@login_required(login_url='/')
def quiz_result(request, run_id):
    run = get_object_or_404(QuizRun, id=run_id, user=request.user)
    
    scenario_list = run.get_scenario_list()
    total_possible_score = len(scenario_list) * 20
    
    # Handle division by zero
    if total_possible_score == 0:
        percentage = 0
    else:
        percentage = (run.total_score / total_possible_score) * 100
    
    badge = "Financial Novice"
    badge_color = "gray"
    badge_icon = "award"
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
            badge_icon = "trophy"
            bonus_xp = 100
        elif percentage >= 50:
            badge = "Smart Saver"
            badge_color = "silver"
            badge_icon = "star"
            bonus_xp = 50
        elif percentage >= 30:
            badge = "Budding Investor"
            badge_color = "bronze"
            badge_icon = "trending-up"
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
            if correct_count > 0:
                # Check last attempt date to determine if streak continues
                last_attempt = UserScenarioAttempt.objects.filter(
                    user=request.user
                ).exclude(quiz_run=run).order_by('-attempted_at').first()
                
                if last_attempt:
                    # Check if last attempt was today or yesterday (within 24 hours)
                    time_diff = timezone.now() - last_attempt.attempted_at
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

    return render(request, 'quiz_result.html', {
        'run': run,
        'badge': badge,
        'badge_color': badge_color,
        'badge_icon': badge_icon,
        'percentage': int(percentage),
        'total_questions': len(scenario_list),
        'total_score': run.total_score,
        'max_score': total_possible_score,
        'xp_awarded': xp_awarded,
    })

def home(request):
    return redirect('start_quiz')