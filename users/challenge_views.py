"""
API endpoints for stock prediction challenges and leaderboard
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import F, Q
from .models import StockPredictionChallenge, ChallengeLeaderboard, UserProfile, StockPredictionQuestion
from simulator.models import UserScenarioAttempt
import re
import random


def extract_direction_from_prediction(prediction_text):
    """Extract direction (up/down/neutral) from prediction text"""
    prediction_lower = prediction_text.lower()
    
    # Check for down/bearish indicators
    down_keywords = ['down', 'fall', 'drop', 'decrease', 'decline', 'bearish', 'sell', 'crash', 'plunge']
    if any(keyword in prediction_lower for keyword in down_keywords):
        return 'down'
    
    # Check for up/bullish indicators
    up_keywords = ['up', 'rise', 'increase', 'grow', 'bullish', 'buy', 'surge', 'rally', 'gain']
    if any(keyword in prediction_lower for keyword in up_keywords):
        return 'up'
    
    return 'neutral'


def analyze_stock_trend(stock_symbol, price_history):
    """Analyze stock trend based on price history - returns bullish/bearish/neutral"""
    if not price_history or len(price_history) < 2:
        return 'neutral'
    
    # Get recent prices
    recent_prices = [h['price'] for h in price_history[-10:]]
    if len(recent_prices) < 2:
        return 'neutral'
    
    # Calculate trend
    first_price = recent_prices[0]
    last_price = recent_prices[-1]
    change_percent = ((last_price - first_price) / first_price) * 100
    
    # Check moving averages if available
    latest = price_history[-1]
    ma20 = latest.get('ma20')
    ma50 = latest.get('ma50')
    current_price = latest.get('price', 0)
    
    # If price is above both MAs, bullish; below both, bearish
    if ma20 and ma50 and current_price:
        if current_price > ma20 and current_price > ma50:
            return 'bullish'
        elif current_price < ma20 and current_price < ma50:
            return 'bearish'
    
    # Fallback to price trend
    if change_percent > 2:
        return 'bullish'
    elif change_percent < -2:
        return 'bearish'
    
    return 'neutral'


def evaluate_prediction(user_direction, ai_direction):
    """Evaluate if user's prediction matches AI analysis"""
    # Map directions
    direction_map = {
        'up': 'bullish',
        'down': 'bearish',
        'neutral': 'neutral',
    }
    
    mapped_user_direction = direction_map.get(user_direction, 'neutral')
    
    # Check if they match
    if mapped_user_direction == ai_direction:
        return True, 15  # Correct prediction, base score
    elif ai_direction == 'neutral' or mapped_user_direction == 'neutral':
        return False, 5  # Partial match, lower score
    else:
        return False, 0  # Wrong prediction, no score


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_leaderboard(request):
    """Get leaderboard for top scores and streaks"""
    try:
        leaderboard_type = request.query_params.get('type', 'scores')  # 'scores' or 'streaks'
        
        # Get or create leaderboard entries for all users
        users = User.objects.all()
        for user in users:
            ChallengeLeaderboard.objects.get_or_create(user=user)
        
        # Update leaderboard from predictions and scenarios
        from simulator.models import UserScenarioAttempt
        
        for entry in ChallengeLeaderboard.objects.all():
            # Stock predictions
            predictions = StockPredictionChallenge.objects.filter(user=entry.user)
            stock_score = sum(p.score for p in predictions)
            entry.stock_score = stock_score
            entry.total_predictions = predictions.count()
            entry.correct_predictions = predictions.filter(is_correct=True).count()
            
            # Scenario quizzes
            scenario_attempts = UserScenarioAttempt.objects.filter(user=entry.user)
            scenario_score = sum(attempt.score_earned for attempt in scenario_attempts)
            entry.scenario_score = scenario_score
            entry.scenario_attempts = scenario_attempts.count()
            
            # Total score
            entry.total_score = stock_score + scenario_score
            
            # Calculate current streak
            recent_predictions = predictions.order_by('-created_at')[:10]
            streak = 0
            for pred in recent_predictions:
                if pred.is_correct:
                    streak += 1
                else:
                    break
            entry.current_streak = streak
            entry.best_streak = max(entry.best_streak, streak)
            entry.save()
        
        # Get leaderboard based on type
        if leaderboard_type == 'streaks':
            entries = ChallengeLeaderboard.objects.all().order_by('-current_streak', '-total_score')[:20]
        else:
            entries = ChallengeLeaderboard.objects.all().order_by('-total_score', '-current_streak')[:20]
        
        leaderboard_data = []
        for idx, entry in enumerate(entries):
            leaderboard_data.append({
                'rank': idx + 1,
                'username': entry.user.username,
                'total_score': entry.total_score,
                'current_streak': entry.current_streak,
                'best_streak': entry.best_streak,
                'total_predictions': entry.total_predictions,
                'correct_predictions': entry.correct_predictions,
            })
        
        return Response({
            'type': leaderboard_type,
            'leaderboard': leaderboard_data,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_challenge_stats(request):
    """Get current user's challenge statistics including scenario scores"""
    try:
        from simulator.models import QuizRun, UserScenarioAttempt
        
        leaderboard_entry, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
        
        # Update from stock predictions
        predictions = StockPredictionChallenge.objects.filter(user=request.user)
        stock_score = sum(p.score for p in predictions)
        leaderboard_entry.stock_score = stock_score
        leaderboard_entry.total_predictions = predictions.count()
        leaderboard_entry.correct_predictions = predictions.filter(is_correct=True).count()
        
        # Update from scenario quizzes
        scenario_attempts = UserScenarioAttempt.objects.filter(user=request.user)
        scenario_score = sum(attempt.score_earned for attempt in scenario_attempts)
        leaderboard_entry.scenario_score = scenario_score
        leaderboard_entry.scenario_attempts = scenario_attempts.count()
        
        # Calculate total score (stock + scenario)
        leaderboard_entry.total_score = stock_score + scenario_score
        
        # Calculate current streak from stock predictions
        recent_predictions = predictions.order_by('-created_at')[:10]
        streak = 0
        for pred in recent_predictions:
            if pred.is_correct:
                streak += 1
            else:
                break
        leaderboard_entry.current_streak = streak
        leaderboard_entry.best_streak = max(leaderboard_entry.best_streak, streak)
        leaderboard_entry.save()
        
        # Calculate win rate (both activities)
        total_activities = leaderboard_entry.total_predictions + leaderboard_entry.scenario_attempts
        total_correct = leaderboard_entry.correct_predictions + scenario_attempts.filter(is_correct=True).count()
        win_rate = (total_correct / total_activities * 100) if total_activities > 0 else 0
        
        return Response({
            'total_score': leaderboard_entry.total_score,
            'stock_score': leaderboard_entry.stock_score,
            'scenario_score': leaderboard_entry.scenario_score,
            'current_streak': leaderboard_entry.current_streak,
            'best_streak': leaderboard_entry.best_streak,
            'total_predictions': leaderboard_entry.total_predictions,
            'correct_predictions': leaderboard_entry.correct_predictions,
            'scenario_attempts': leaderboard_entry.scenario_attempts,
            'win_rate': round(win_rate, 1),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_random_stock_question(request):
    """Get a random stock prediction question"""
    try:
        questions = StockPredictionQuestion.objects.filter(is_active=True)
        if not questions.exists():
            return Response({'error': 'No questions available'}, status=404)
        
        question = random.choice(list(questions))
        
        return Response({
            'id': question.id,
            'stock_name': question.stock_name,
            'stock_symbol': question.stock_symbol,
            'question': question.question,
            'chart_data': question.chart_data,
            'difficulty': question.difficulty,
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_stock_prediction(request):
    """Submit stock prediction and get AI judge feedback - uses questions if question_id provided"""
    try:
        question_id = request.data.get('question_id')
        stock_symbol = request.data.get('stock_symbol')
        prediction_text = request.data.get('prediction', '')
        
        if not prediction_text:
            return Response({'error': 'Prediction text required'}, status=400)
        
        # If question_id is provided, use the question-based system
        if question_id:
            try:
                question = StockPredictionQuestion.objects.get(id=question_id, is_active=True)
                
                # Analyze user's prediction using keyword matching and AI-like analysis
                user_direction = extract_direction_from_prediction(prediction_text)
                prediction_lower = prediction_text.lower()
                
                # Check if user's answer contains expected keywords
                keyword_matches = sum(1 for keyword in question.expected_keywords if keyword in prediction_lower)
                keyword_score = min(keyword_matches / len(question.expected_keywords), 1.0) if question.expected_keywords else 0.5
                
                # Check direction match
                direction_map = {
                    'up': 'up',
                    'down': 'down',
                    'neutral': 'neutral',
                }
                direction_match = (user_direction == question.expected_direction)
                
                # Calculate score based on keyword matches and direction
                if direction_match and keyword_score > 0.5:
                    is_correct = True
                    score = question.max_score
                    feedback = f"Excellent! {question.explanation}"
                elif direction_match or keyword_score > 0.6:
                    is_correct = True
                    score = question.base_score + int((question.max_score - question.base_score) * keyword_score)
                    feedback = f"Good prediction! {question.explanation}"
                elif keyword_score > 0.3:
                    is_correct = False
                    score = int(question.base_score * keyword_score)
                    feedback = f"Partially correct. {question.explanation}"
                else:
                    is_correct = False
                    score = 0
                    feedback = f"Not quite right. {question.explanation}"
                
                # Save prediction
                prediction = StockPredictionChallenge.objects.create(
                    user=request.user,
                    stock_symbol=question.stock_symbol,
                    prediction=prediction_text,
                    prediction_direction=user_direction,
                    ai_analysis=question.explanation,
                    ai_direction=question.expected_direction,
                    is_correct=is_correct,
                    score=score,
                    feedback=feedback,
                )
                
                # Update leaderboard
                leaderboard_entry, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
                leaderboard_entry.total_score += score
                leaderboard_entry.total_predictions += 1
                if is_correct:
                    leaderboard_entry.correct_predictions += 1
                    leaderboard_entry.current_streak += 1
                    leaderboard_entry.best_streak = max(leaderboard_entry.best_streak, leaderboard_entry.current_streak)
                else:
                    leaderboard_entry.current_streak = 0
                leaderboard_entry.save()
                
                # Check for achievements
                from .achievement_views import check_and_unlock_achievements
                check_and_unlock_achievements(request.user)
                
                return Response({
                    'success': True,
                    'score': score,
                    'is_correct': is_correct,
                    'feedback': feedback,
                    'ai_analysis': question.explanation,
                    'prediction_direction': user_direction,
                    'ai_direction': question.expected_direction,
                    'total_score': leaderboard_entry.total_score,
                    'current_streak': leaderboard_entry.current_streak,
                })
            except StockPredictionQuestion.DoesNotExist:
                return Response({'error': 'Question not found'}, status=404)
        
        # Fallback to original system if no question_id
        from .portfolio_views import get_stock_detail, get_stock_info
        
        if not stock_symbol:
            return Response({'error': 'Stock symbol required when not using questions'}, status=400)
        
        # Get stock info and detail with price history
        stock_info = get_stock_info(stock_symbol, use_cache=True)
        if not stock_info or stock_info.get('current_price', 0.0) <= 0.0:
            return Response({'error': 'Stock not found or data unavailable'}, status=404)
        
        # Get stock detail with price history using helper functions
        from .portfolio_views import generate_price_history
        from .models import PredictedStockData
        from django.utils import timezone
        
        # Try to get price history from cache first
        price_history = []
        try:
            cached = PredictedStockData.objects.get(symbol=stock_symbol)
            cache_age = timezone.now() - cached.last_updated
            if cache_age.total_seconds() < 600:  # 10 minutes
                price_history = cached.price_history or []
        except PredictedStockData.DoesNotExist:
            pass
        
        # If no cached history, generate it
        if not price_history:
            price_history = generate_price_history(stock_symbol, days=60, use_cache=False)
        
        if not price_history:
            return Response({'error': 'Price history not available for this stock'}, status=404)
        
        # Analyze stock trend using actual price history
        ai_direction = analyze_stock_trend(stock_symbol, price_history)
        
        # Also get ML prediction for more accurate analysis
        from .ml_predictor import ML_PREDICTOR
        ml_prediction = ML_PREDICTOR.predict(stock_symbol)
        ml_direction = ml_prediction.get('direction', 'neutral')
        
        # Use ML prediction if available, otherwise use trend analysis
        if ml_direction != 'neutral':
            ai_direction = ml_direction  # 'bullish', 'bearish', or 'neutral'
        
        # Extract user's prediction direction
        user_direction = extract_direction_from_prediction(prediction_text)
        
        # Evaluate prediction
        is_correct, base_score = evaluate_prediction(user_direction, ai_direction)
        
        # Generate feedback
        import random
        if is_correct:
            score = base_score + random.randint(0, 5)  # 15-20 points for correct
            feedback = "Great prediction! Your analysis shows good understanding of market trends."
            ai_analysis = f"The stock's technical indicators and ML analysis suggest a {ai_direction} trend, confirming your prediction."
        else:
            score = base_score  # 0-5 points for incorrect
            if user_direction == 'down' and ai_direction == 'bullish':
                feedback = "Your prediction was incorrect. The stock shows bullish indicators, contradicting your prediction of downward movement."
                ai_analysis = f"The stock's technical indicators and ML analysis suggest a {ai_direction} trend. Your prediction of a downward movement does not align with the current market analysis."
            elif user_direction == 'up' and ai_direction == 'bearish':
                feedback = "Your prediction was incorrect. The stock shows bearish indicators, contradicting your prediction of upward movement."
                ai_analysis = f"The stock's technical indicators and ML analysis suggest a {ai_direction} trend. Your prediction of an upward movement does not align with the current market analysis."
            else:
                feedback = "Your prediction is partially correct. Consider analyzing the technical indicators more carefully."
                ai_analysis = f"The stock's technical indicators and ML analysis suggest a {ai_direction} trend."
        
        # Save prediction
        prediction = StockPredictionChallenge.objects.create(
            user=request.user,
            stock_symbol=stock_symbol,
            prediction=prediction_text,
            prediction_direction=user_direction,
            ai_analysis=ai_analysis,
            ai_direction=ai_direction,
            is_correct=is_correct,
            score=score,
            feedback=feedback,
        )
        
        # Update leaderboard
        leaderboard_entry, _ = ChallengeLeaderboard.objects.get_or_create(user=request.user)
        leaderboard_entry.total_score += score
        leaderboard_entry.total_predictions += 1
        if is_correct:
            leaderboard_entry.correct_predictions += 1
            leaderboard_entry.current_streak += 1
            leaderboard_entry.best_streak = max(leaderboard_entry.best_streak, leaderboard_entry.current_streak)
        else:
            leaderboard_entry.current_streak = 0
        leaderboard_entry.save()
        
        return Response({
            'success': True,
            'score': score,
            'is_correct': is_correct,
            'feedback': feedback,
            'ai_analysis': ai_analysis,
            'prediction_direction': user_direction,
            'ai_direction': ai_direction,
            'total_score': leaderboard_entry.total_score,
            'current_streak': leaderboard_entry.current_streak,
        })
    except Exception as e:
        import traceback
        print(f"Error in submit_stock_prediction: {e}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)

