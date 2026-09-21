"""Read-only market endpoints. All data comes from the cached service layer."""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import services


@api_view(['GET'])
@permission_classes([AllowAny])
def market_news(request):
    """Headlines: one symbol's when asked for, otherwise the day's whole wire.

    Returns ``{"news": []}`` when the provider has nothing, so the client can
    render an honest empty state. The previous version manufactured a summary
    out of empty fields and shipped it as real reporting.
    """
    symbol = request.GET.get('symbol')
    limit = max(1, min(12, int(request.GET.get('limit') or 8)))

    news = services.get_news(symbol) if symbol else services.get_market_news(limit)
    return Response({'news': news})


@api_view(['GET'])
@permission_classes([AllowAny])
def market_quotes(request):
    """Quotes for a comma-separated ``symbols`` list, capped at 20 per call."""
    raw = request.GET.get('symbols', '')
    symbols = [s.strip() for s in raw.split(',') if s.strip()][:20]
    if not symbols:
        symbols = list(services.TRACKED_SYMBOLS[:8])

    quotes = services.get_quotes(symbols)
    return Response({'quotes': [q.as_dict() for q in quotes.values()]})


@api_view(['GET'])
@permission_classes([AllowAny])
def market_history(request, symbol):
    """Daily closes for one symbol. ``days`` is clamped to 5..365."""
    days = max(5, min(365, int(request.GET.get('days', 90) or 90)))
    return Response(
        {
            'symbol': symbol.upper(),
            'currency': services.currency_for(symbol),
            'series': services.get_history(symbol, days),
        }
    )
