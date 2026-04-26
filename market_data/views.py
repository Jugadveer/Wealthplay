from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import yfinance as yf
import random
from django.utils import timezone


@api_view(['GET'])
@permission_classes([AllowAny])
def market_news(request):
    symbol = request.GET.get('symbol', 'AAPL')
    try:
        # 1. First check if it's a CustomStock
        from users.models import CustomStock
        try:
            custom_stock = CustomStock.objects.get(symbol=symbol)
            # Generate simulated news for algorithmic stocks
            sim_titles = {
                'bullish': [f"Breakthrough reported in {symbol}'s core technology segment", f"{symbol} expands into high-growth emerging markets"],
                'bearish': [f"Analysts downgrade {symbol} amid supply chain concerns", f"Profit taking observed in {symbol} following recent rally"],
                'neutral': [f"{symbol} consolidation phase continues as investors await earnings", f"Sector-wide stability supports current {symbol} valuation"]
            }
            trend = custom_stock.trend or 'neutral'
            title = random.choice(sim_titles.get(trend, sim_titles['neutral']))
            summary = f"Recent algorithmic analysis of {custom_stock.name} ({symbol}) shows strong correlation with current {trend} market sentiment. Internal metrics suggest a confidence factor of {custom_stock.trend_strength or 0.5}, marking a significant period for institutional positioning."
            
            return JsonResponse({
                'news': [{
                    'title': title,
                    'link': '#',
                    'publisher': 'WealthPlay Oracle',
                    'providerPublishTime': int(timezone.now().timestamp()),
                    'summary': summary,
                    'thumbnail': ''
                }]
            })
        except CustomStock.DoesNotExist:
            pass

        # 2. Check persistent news cache
        from .models import MarketNewsCache
        cache_entry = MarketNewsCache.objects.filter(symbol=symbol).first()
        if cache_entry:
            age = timezone.now() - cache_entry.last_updated
            if age.total_seconds() < 1800:  # 30 minutes cache
                return JsonResponse(cache_entry.news_json)

        # 3. Fallback to live data if cache miss or stale
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news
        
        if not raw_news:
            return JsonResponse({'news': []})

        # Return only the TOP news item (highest relevance)
        article = raw_news[0]
        title = article.get('title', '')
        publisher = article.get('publisher', '')
        link = article.get('link', '')
        
        resolutions = article.get('thumbnail', {}).get('resolutions', [])
        thumbnail = resolutions[0].get('url', '') if resolutions else ''
        
        summary = article.get('summary', '') or article.get('description', '')
        
        if not summary:
            summary = f"Latest market report: {title}. This development, reported by {publisher}, is currently impacting trader sentiment for {symbol}. Analysts are monitoring volume and price action closely following this announcement."
        else:
            summary = summary.split('\n')[0]

        result = {
            'news': [{
                'title': title,
                'link': link,
                'publisher': publisher,
                'providerPublishTime': article.get('providerPublishTime', 0),
                'summary': summary,
                'thumbnail': thumbnail
            }]
        }

        # Update cache
        MarketNewsCache.objects.update_or_create(
            symbol=symbol,
            defaults={'news_json': result}
        )

        return JsonResponse(result)
    except Exception as e:
        print(f"Error in market_news for {symbol}: {e}")
        return JsonResponse({'error': str(e)}, status=500)
