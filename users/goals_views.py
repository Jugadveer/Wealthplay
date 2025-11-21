from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import FinancialGoal
import json

@login_required
def goals_page(request):
    """Goals page view"""
    goals = FinancialGoal.objects.filter(user=request.user)
    
    # Calculate summary
    total_target = sum(g.target_amount for g in goals)
    total_saved = sum(g.current_amount for g in goals)
    total_sip = sum(g.monthly_sip for g in goals)
    
    context = {
        'goals': goals,
        'total_target': total_target,
        'total_saved': total_saved,
        'total_sip': total_sip,
    }
    
    return render(request, 'goals.html', context)


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def create_goal(request):
    """API endpoint to create a new goal"""
    try:
        data = json.loads(request.body)
        
        goal = FinancialGoal.objects.create(
            user=request.user,
            name=data.get('name'),
            icon=data.get('icon', 'wallet'),
            target_amount=data.get('target_amount'),
            current_amount=data.get('current_amount', 0),
            monthly_sip=data.get('monthly_sip'),
            time_to_goal_months=data.get('time_to_goal'),
            color=data.get('color', 'from-brand-primary to-orange-500'),
            icon_bg=data.get('icon_bg', 'bg-brand-50 text-brand-600'),
        )
        
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
                'color': goal.color,
                'icon_bg': goal.icon_bg,
                'progress_percent': round(goal.progress_percent, 1),
                'remaining_amount': float(goal.remaining_amount),
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


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
        if 'icon' in data:
            goal.icon = data['icon']
        if 'target_amount' in data:
            goal.target_amount = data['target_amount']
        if 'current_amount' in data:
            goal.current_amount = data['current_amount']
        if 'monthly_sip' in data:
            goal.monthly_sip = data['monthly_sip']
        if 'time_to_goal_months' in data:
            goal.time_to_goal_months = data['time_to_goal']
        
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

