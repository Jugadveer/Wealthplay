
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import FinancialGoal
import json

@login_required


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_goal(request):
    """API endpoint to create a new goal with AI strategy"""
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        if not data.get('name'):
            return JsonResponse({'success': False, 'error': 'Goal name is required'}, status=400)
        
        target_amount = float(data.get('target_amount', 0))
        current_amount = float(data.get('current_amount', 0))
        tenure_yrs = float(data.get('tenure_years') or data.get('time_to_goal', 5))
        category = data.get('category', 'GENERAL').upper()
        extra_val = float(data.get('extra_val', 0))
        
        # Time calc
        from datetime import timedelta
        target_date = timezone.now().date() + timedelta(days=int(tenure_yrs * 365))
        
        # AI strategy calculation
        strategy = _calculate_ai_strategy(category, target_amount, tenure_yrs, extra_val, current_amount)
        
        # Estimate SIP if not provided (fallback)
        monthly_sip = float(data.get('monthly_sip') or 0)
        if monthly_sip <= 0 and category == "GENERAL":
             # Use the calc from _calculate_ai_strategy if available in steps? 
             # For now just use a simple 10% rule
             monthly_sip = (target_amount - current_amount) / (tenure_yrs * 12) if tenure_yrs > 0 else 0

        goal = FinancialGoal.objects.create(
            user=request.user,
            title=data.get('name'),
            name=data.get('name'),
            icon=data.get('icon', 'wallet'),
            target_amount=target_amount,
            current_amount=current_amount,
            monthly_sip=monthly_sip,
            time_to_goal_months=int(tenure_yrs * 12),
            target_date=target_date,
            category=category,
            extra_data={
                'extra_val': extra_val,
                'tenure_years': tenure_yrs
            },
            strategy_report=strategy,
            color=data.get('color', 'from-brand-primary to-orange-500'),
            icon_bg=data.get('icon_bg', 'bg-brand-50 text-brand-600'),
        )
        
        return JsonResponse({
            'success': True,
            'goal': {
                'id': goal.id,
                'name': goal.name,
                'category': goal.category,
                'strategy': goal.strategy_report,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount),
                'monthly_sip': float(goal.monthly_sip),
                'progress_percent': round(goal.progress_percent, 1),
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({'success': False, 'error': str(e), 'traceback': traceback.format_exc()}, status=400)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def update_goal(request, goal_id):
    """API endpoint to update a goal"""
    try:
        goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
        data = json.loads(request.body)
        
        if 'name' in data:
            goal.name = data['name']
            goal.title = data['name']  # Sync title with name
        if 'icon' in data:
            goal.icon = data['icon']
        if 'target_amount' in data:
            goal.target_amount = data['target_amount']
        if 'current_amount' in data:
            goal.current_amount = data['current_amount']
        if 'monthly_sip' in data:
            goal.monthly_sip = data['monthly_sip']
        if 'time_to_goal' in data or 'time_to_goal_months' in data:
            time_months = data.get('time_to_goal') or data.get('time_to_goal_months')
            if time_months:
                goal.time_to_goal_months = int(time_months)
                from datetime import timedelta
                goal.target_date = timezone.now().date() + timedelta(days=int(time_months) * 30)
        if 'color' in data:
            goal.color = data['color']
        if 'icon_bg' in data:
            goal.icon_bg = data['icon_bg']
        
        goal.save()
        
        return JsonResponse({
            'success': True,
            'goal': {
                'id': goal.id,
                'name': goal.name,
                'icon': goal.icon,
                'target_amount': float(goal.target_amount),
                'current_amount': float(goal.current_amount),
                'monthly_sip': float(goal.monthly_sip),
                'time_to_goal_months': goal.time_to_goal_months,
                'progress_percent': round(goal.progress_percent, 1),
                'remaining_amount': float(goal.remaining_amount),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_goal(request, goal_id):
    """API endpoint to delete a goal"""
    try:
        goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
        goal.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def get_goals_api(request):
    """API endpoint to get all goals as JSON"""
    goals = FinancialGoal.objects.filter(user=request.user)
    
    goals_data = [{
        'id': g.id,
        'name': g.name,
        'icon': g.icon,
        'target_amount': float(g.target_amount),
        'current_amount': float(g.current_amount),
        'monthly_sip': float(g.monthly_sip),
        'time_to_goal_months': g.time_to_goal_months,
        'color': g.color,
        'icon_bg': g.icon_bg,
        'progress_percent': g.progress_percent,
        'remaining_amount': float(g.remaining_amount),
    } for g in goals]
    
    return JsonResponse({'goals': goals_data})

