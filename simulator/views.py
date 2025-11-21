import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Scenario, DecisionOption, UserScenarioLog, QuizRun

# 1. START A NEW QUIZ (Random 5)
@login_required(login_url='/')
def start_quiz(request):
    # Get all scenario IDs
    all_ids = list(Scenario.objects.values_list('id', flat=True))
    
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
                    
                    # Award XP to user based on score (1 XP per point, max 20 XP per question)
                    from users.models import UserProfile
                    try:
                        profile = UserProfile.objects.get(user=request.user)
                        xp_to_award = min(score_value, 20)  # Max 20 XP per question
                        profile.xp += xp_to_award
                        profile.save()
                    except Exception as e:
                        print(f"Error awarding XP: {e}")
            
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
    
    if percentage >= 80:
        badge = "Wealth Master"
        badge_color = "gold"
        badge_icon = "trophy"
        # Award XP for completing quiz with high score
        from users.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.xp += 100  # Bonus for excellent performance
            profile.save()
        except:
            pass
    elif percentage >= 50:
        badge = "Smart Saver"
        badge_color = "silver"
        badge_icon = "star"
        from users.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.xp += 50  # Good performance reward
            profile.save()
        except:
            pass
    elif percentage >= 30:
        badge = "Budding Investor"
        badge_color = "bronze"
        badge_icon = "trending-up"
        from users.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.xp += 25  # Participation reward
            profile.save()
        except:
            pass
    else:
        # Award minimal XP for completion
        from users.models import UserProfile
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.xp += 10  # Completion reward
            profile.save()
        except:
            pass

    return render(request, 'quiz_result.html', {
        'run': run,
        'badge': badge,
        'badge_color': badge_color,
        'badge_icon': badge_icon,
        'percentage': int(percentage),
        'total_questions': len(scenario_list),
        'total_score': run.total_score,
        'max_score': total_possible_score
    })

def home(request):
    return redirect('start_quiz')