@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_ai_recommendation(request):
    """Get AI recommendation for stocks - handles both custom and real stocks"""
    try:
        symbol = request.data.get('symbol')
        if not symbol:
            return Response({'error': 'Symbol required'}, status=400)

        # First check if it's a custom stock
        from .models import CustomStock
        from .simulator_engine import generate_stock_analysis
        try:
            custom_stock = CustomStock.objects.get(symbol=symbol)
            analysis_data = generate_stock_analysis(custom_stock, float(custom_stock.current_price), float(custom_stock.change_percent))
            
            return Response({
                'symbol': symbol,
                'recommendation': analysis_data['recommendation'],
                'confidence': analysis_data['confidence'],
                'message': analysis_data['analysis'],
                'target_price': analysis_data['target_price'],
                'regime': 'Virtual Simulation',
                'is_custom': True
            })
        except CustomStock.DoesNotExist:
            pass # Continue to real stocks

        # Try to get from cache first for instant response
        try:
            cached = PredictedStockData.objects.get(symbol=symbol)
            cache_age = timezone.now() - cached.last_updated
            
            if cache_age.total_seconds() < 600:  # 10 minutes - use cache
                recommendation = cached.ml_direction
                confidence = cached.ml_confidence
                regime = cached.ml_regime
                vol = cached.ml_volatility
                
                # Convert prediction to recommendation message
                if recommendation == 'bullish':
                    message = f"ML Analysis: The model suggests an **Up** move with {round(confidence * 100)}% confidence."
                    action_text = "BUY"
                elif recommendation == 'bearish':
                    message = f"ML Analysis: The model suggests a **Down** move with {round(confidence * 100)}% confidence."
                    action_text = "SELL"
                else:
                    message = f"ML Analysis: The model is **Neutral** with {round(confidence * 100)}% confidence."
                    action_text = "HOLD"
                
                return Response({
                    'symbol': symbol,
                    'recommendation': action_text,
                    'confidence': confidence,
                    'message': message,
                    'regime': regime,
                    'is_custom': False
                })
        except PredictedStockData.DoesNotExist:
            pass  # Fall through to live prediction
        
        # Fallback to live prediction if cache miss
        stock_info = get_stock_info(symbol, use_cache=False)
        if stock_info.get('current_price', 0.0) <= 0.0:
            return Response({'error': 'Stock data not available for AI analysis'}, status=404)
        
        # Run the actual ML prediction
        prediction_results = ML_PREDICTOR.predict(symbol)
        
        recommendation = prediction_results['direction']
        confidence = prediction_results['confidence']
        regime = prediction_results['regime']
        vol = prediction_results['vol']
        
        # Convert prediction to recommendation message
        if recommendation == 'bullish':
            message = f"ML Analysis: The model suggests an **Up** move with {round(confidence * 100)}% confidence."
            action_text = "BUY"
        elif recommendation == 'bearish':
            message = f"ML Analysis: The model suggests a **Down** move with {round(confidence * 100)}% confidence."
            action_text = "SELL"
        else:
            message = f"ML Analysis: The model is **Neutral** with {round(confidence * 100)}% confidence."
            action_text = "HOLD"
        
        reasons = [
            f'Market Regime: Currently **{regime}** (Volatility: {round(vol * 100, 2)}%)',
            f'Confidence Level: {round(confidence * 100)}%',
            f'Predicted Action: {action_text}.'
        ]
        
        return Response({
            'symbol': symbol,
            'recommendation': recommendation,
            'confidence': round(confidence, 2),
            'message': message,
            'reasons': reasons,
            'metadata': {
                'regime': regime,
                'volatility': round(vol, 4)
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_ai_recommendation: {e}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=500)
