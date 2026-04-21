from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import HistoricalCrisis, HistoricalNews, TimeCapsuleSession
from django.utils import timezone
from decimal import Decimal
import yfinance as yf
import random

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_crises(request):
    """List all available historical crises"""
    crises = HistoricalCrisis.objects.all()
    data = []
    for c in crises:
        data.append({
            'id': c.id,
            'name': c.name,
            'slug': c.slug,
            'description': c.description,
            'difficulty': c.difficulty,
            'icon': c.icon,
            'narrative_intro': c.narrative_intro,
            'start_date': c.start_date,
            'end_date': c.end_date,
            'initial_balance': c.initial_balance,
        })
    return Response({'crises': data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request, crisis_id):
    """Start or resume a Time Capsule session"""
    crisis = get_object_or_404(HistoricalCrisis, id=crisis_id)
    session, created = TimeCapsuleSession.objects.get_or_create(
        user=request.user,
        crisis=crisis,
        defaults={
            'portfolio_balance': crisis.initial_balance,
            'holdings': {},
            'current_sim_day': 0,
            'equity_curve': [{'day': 0, 'value': float(crisis.initial_balance)}]
        }
    )
    
    if created:
        print(f"Created new session for {request.user.username} in {crisis.name}")
    
    return Response({
        'session_id': session.id,
        'current_day': session.current_sim_day,
        'balance': session.portfolio_balance,
        'holdings': session.holdings,
        'crisis_name': crisis.name,
        'start_date': crisis.start_date.isoformat()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sim_data(request, session_id):
    """Fetch next data point for the simulation flow"""
    session = get_object_or_404(TimeCapsuleSession, id=session_id, user=request.user)
    crisis = session.crisis
    
    # 1. Update Simulation Day
    # In a real minute-per-month sim, we would calculate based on elapsed time
    # For now, let's just increment by 1 day per heartbeat
    session.current_sim_day += 1
    session.save()
    
    # 2. Check for News
    news = HistoricalNews.objects.filter(crisis=crisis, relative_day=session.current_sim_day).first()
    news_data = None
    if news:
        news_data = {
            'headline': news.headline,
            'description': news.impact_description,
            'sentiment': news.sentiment
        }
    
    # 3. Simulate Price Movement
    # We use yfinance to get the "Historical Base" for a representative index (e.g. SPY)
    # Then we add AI Jitter.
    # To keep it fast, we'll return a mock movement based on the news sentiment if it exists.
    base_change = random.uniform(-0.01, 0.01)
    if news:
        if news.sentiment == 'panic': base_change = random.uniform(-0.08, -0.04)
        elif news.sentiment == 'bearish': base_change = random.uniform(-0.04, -0.01)
        elif news.sentiment == 'bullish': base_change = random.uniform(0.02, 0.05)
    
    # Apply change to balance if they have holdings?
    # Simple model: they are trading 'Market Units' for this sim.
    
    return Response({
        'current_day': session.current_sim_day,
        'news': news_data,
        'market_change': base_change,
        'is_peak_crisis': session.current_sim_day < 60 # Arbitrary early phase
    })
