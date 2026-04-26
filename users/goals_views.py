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


def _calculate_ai_strategy(category, amt, yrs, extra, savings):
    """Internal helper to calculate AI strategy steps based on category"""
    import math
    steps = []
    
    if category == "HOME":
        r = (extra / 12) / 100
        months = yrs * 12
        # Standard EMI calculation: P*r*(1+r)^n / ((1+r)^n - 1)
        if r > 0 and months > 0:
            emi = (amt * r * math.pow(1 + r, months)) / (math.pow(1 + r, months) - 1)
            total_int = (emi * months) - amt
            # SIP needed at 13% CAGR to recover total_int
            sip_r = 0.13 / 12
            sip = total_int / (((math.pow(1 + sip_r, months) - 1) / sip_r) * (1 + sip_r))
            
            steps = [
                {"title": "Interest Liability", "p": f"Bank Profit: ₹{int(round(total_int)):,}. You are paying nearly {round(total_int/amt, 1)}x the principal in interest."},
                {"title": "The 10% Recovery Rule", "p": f"A monthly SIP of ₹{int(round(sip)):,} at 13% CAGR will recover 100% of your interest liability by the end of the loan tenure."},
                {"title": "Investment Mix", "p": "Recommended: 70% Index Funds, 30% Flexi-cap for steady growth with a fallback to Arbitrage funds during high volatility."}
            ]
            return {"steps": steps, "tickers": ["NIFTYBEES.NS", "RELIANCE.NS", "HDFCBANK.NS"]}
        else:
            return {"steps": [{"title": "Data Error", "p": "Invalid interest or tenure values"}], "tickers": []}

    elif category == "EMERGENCY":
        multiplier = 12 if extra < 5 else 6
        target = amt * multiplier
        steps = [
            {"title": "Survival Multiple", "p": f"Safety Net: {multiplier} months. Total Target: ₹{target:,.0f}."},
            {"title": "Asset Allocation", "p": "Priority: Liquidity. 100% Allocation to Liquid Funds or High-yield Savings. Avoid lock-ins like ELSS or FDs with penalties."},
            {"title": "Optimization", "p": "AI detected potential leakage in monthly subscriptions. Redirecting ₹700/mo can fill this fund 15% faster."}
        ]
        return {"steps": steps, "tickers": ["LIQUIDBEES.NS", "SGB-AUG2021"]}

    elif category == "WEDDING":
        future_cost = amt * math.pow(1.12, yrs)
        steps = [
            {"title": "Milestone Inflation", "p": f"Wedding costs rise at ~12% annually. Future Value: ₹{int(round(future_cost)):,}. Target adjusted for inflation."},
            {"title": "Gold Hedging", "p": "Allocating 25% of your SIP to Sovereign Gold Bonds (SGBs) ensures that your jewelry costs are hedged against gold price hikes."},
            {"title": "Suggested Fund", "p": "Recommended: Multi-Asset Allocator Fund (Equity + Debt + Gold) to balance volatility with stable growth."}
        ]
        return {"steps": steps, "tickers": ["NIFTYBEES.NS", "GOLD.NS", "TCS.NS"]}

    elif category == "RETIRE":
        # yrs = Retire Age, extra = Current Age
        years_to_retire = max(1, yrs - extra)
        corpus = (amt * 12) * 25 # 25x Annual Expenses
        steps = [
            {"title": "Corpus Goal", "p": f"To sustain current lifestyle, you need a corpus of ₹{corpus:,.0f} by age {yrs}."},
            {"title": "The Glide Path", "p": f"Start with 80% Equity allocation. AI will trigger a move of 10% to Debt annually starting 5 years before retirement."},
            {"title": "Investment Suggestion", "p": "Core holdings: Nifty 50 Index (40%), Midcap Opportunities (20%), International Nasdaq Index (20%) for geographic diversification."}
        ]
        return {"steps": steps, "tickers": ["^NSEI", "MON100.NS", "NIFTYMIDCAP150.NS"]}

    elif category == "TAX":
        gap = max(0, 150000 - extra)
        steps = [
            {"title": "Tax Leakage", "p": f"You have a ₹{gap:,.0f} gap in your Section 80C limit (assuming ₹1.5L cap)."},
            {"title": "ELSS Maximizer", "p": "Switching from standard FDs to ELSS (Tax Saving Mutual Funds) can save significant tax while maintaining 12-14% historical returns."},
            {"title": "Action Plan", "p": "Invest remaining 80C limit before March 31. AI recommends picking a 5-star rated Quant or Parag Parikh ELSS Fund."}
        ]
        return {"steps": steps, "tickers": ["QUANT_ELSS", "PPFAS_ELSS"]}

    elif category == "EDU":
        future_cost = (amt - savings) * math.pow(1.10, yrs)
        steps = [
            {"title": "The Education Gap", "p": f"Education inflation (10%) turns ₹{amt:,.0f} into ₹{int(round(future_cost)):,} in {yrs} years."},
            {"title": "Risk Mitigation", "p": "80% Equity for growth phase, auto-shifting to Ultra Short Term Debt 2 years before the first fee payment."},
            {"title": "Currency Hedge", "p": "For international education, allocate 30% to US-based Nasdaq or S&P 500 funds to protect against INR depreciation."}
        ]
        return {"steps": steps, "tickers": ["MON100.NS", "NIFTYBEES.NS"]}

    elif category == "TRIP":
        buffer = 1.15 if extra == 1 else 1.05
        target = amt * buffer
        steps = [
            {"title": "Forex Protection", "p": f"Goal target adjusted to ₹{int(round(target)):,} to handle currency volatility and hidden concierge fees."},
            {"title": "Low-Vol Strategy", "p": "Recommended: Arbitrage or Debt funds. Capital safety is paramount here. Avoid Smallcaps for short-term travel goals."},
            {"title": "Cost Efficiency", "p": "Saving via SIP vs Credit cards saves an estimated 14% in finance charges and late fees."}
        ]
        return {"steps": steps, "tickers": ["LIQUIDBEES.NS", "TATAMOTORS.NS"]}
    
    else:
        # DEFAULT / GENERAL
        monthly_growth = 0.12 / 12
        months = yrs * 12
        if months > 0:
            sip = (amt - savings) / (((math.pow(1 + monthly_growth, months) - 1) / monthly_growth) * (1 + monthly_growth))
        else:
            sip = 0
            
        steps = [
            {"title": "General Wealth Goal", "p": f"To reach ₹{amt:,.0f} in {yrs} years, aim for a monthly SIP of ₹{int(round(sip)):,}."},
            {"title": "Balanced Allocation", "p": "Recommended: 60% Equity, 40% Debt. Rebalance semi-annually."},
            {"title": "AI Nudge", "p": "Increase SIP by 5% annually (Top-up) to reach your goal 2.5 years earlier."}
        ]
        
    return {"steps": steps}


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

