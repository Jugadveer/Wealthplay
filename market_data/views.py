from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import yfinance as yf


@api_view(['GET'])
@permission_classes([AllowAny])
def market_news(request):
    symbol = request.GET.get('symbol', 'AAPL')
    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news
        if not raw_news:
            return JsonResponse({'news': []})

        # Return only the TOP news item
        article = raw_news[0]
        title = article.get('title', '')
        publisher = article.get('publisher', '')
        link = article.get('link', '')
        
        # Single Paragraph Intelligence
        prompt = f"""You are WealthPlay's news analyst. 
        Write a single, concise 3-4 sentence paragraph summarizing why this news is relevant for {symbol}:
        Headline: {title}
        Publisher: {publisher}
        """
        
        summary = ""
        try:
            from mentor_engine.gemini_client import gemini_chat
            summary = str(gemini_chat(prompt, max_tokens=150)).strip()
        except:
            summary = f"Latest market news for {symbol}: {title}. Coverage by {publisher} suggests significant activity in this sector."

        result = {
            'title': title,
            'link': link,
            'publisher': publisher,
            'providerPublishTime': article.get('providerPublishTime', 0),
            'summary': summary
        }

        return JsonResponse({'news': [result]})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
