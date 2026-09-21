"""Social endpoints: the copy-trading board and the shared rationale feed."""

from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import ChallengeLeaderboard, DemoPortfolio, PortfolioFollow, TradeRationalePost
from .valuation import value_portfolio


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_copy_trading_hub(request):
    """Top traders and the shared rationale feed."""
    following = set(
        PortfolioFollow.objects.filter(follower=request.user).values_list('followed_user_id', flat=True)
    )

    traders = []
    leaders = (
        ChallengeLeaderboard.objects.select_related('user')
        .exclude(user=request.user)
        .order_by('-total_score', '-current_streak')[:10]
    )
    portfolios = {
        p.user_id: p for p in DemoPortfolio.objects.filter(user__in=[entry.user for entry in leaders])
    }

    for entry in leaders:
        portfolio = portfolios.get(entry.user_id)
        traders.append(
            {
                'user_id': entry.user_id,
                'username': entry.user.username,
                'score': entry.total_score,
                'streak': entry.current_streak,
                'portfolio_return_percent': (
                    round(value_portfolio(portfolio)['total_pnl_percent'], 2) if portfolio else 0.0
                ),
                'is_followed': entry.user_id in following,
            }
        )

    feed = [
        {
            'id': post.id,
            'username': post.author.username,
            'author_id': post.author_id,
            'symbol': post.symbol,
            'action': post.action,
            'rationale': post.rationale,
            'created_at': post.created_at.isoformat(),
            'is_following_author': post.author_id in following,
        }
        for post in TradeRationalePost.objects.select_related('author')[:25]
    ]

    return Response({'top_traders': traders, 'feed': feed, 'following_count': len(following)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def follow_copy_trader(request):
    """Follow or unfollow another trader."""
    try:
        target_id = int(request.data.get('user_id'))
    except (TypeError, ValueError):
        return Response({'error': 'A numeric user_id is required.'}, status=400)

    if target_id == request.user.id:
        return Response({'error': 'You cannot follow yourself.'}, status=400)

    if not ChallengeLeaderboard.objects.filter(user_id=target_id).exists():
        return Response({'error': 'That trader was not found.'}, status=404)

    if request.data.get('follow', True):
        PortfolioFollow.objects.get_or_create(follower=request.user, followed_user_id=target_id)
        followed = True
    else:
        PortfolioFollow.objects.filter(follower=request.user, followed_user_id=target_id).delete()
        followed = False

    return Response({'success': True, 'is_followed': followed})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_trade_rationale(request):
    """Share why a trade was made. Capped short so it stays a thesis, not an essay."""
    symbol = (request.data.get('symbol') or '').strip().upper()
    action = (request.data.get('action') or '').strip().upper()
    rationale = (request.data.get('rationale') or '').strip()

    if not symbol:
        return Response({'error': 'A symbol is required.'}, status=400)
    if action not in {'BUY', 'SELL', 'HOLD'}:
        return Response({'error': 'Action must be BUY, SELL or HOLD.'}, status=400)
    if not 1 <= len(rationale) <= 140:
        return Response({'error': 'A rationale of 1 to 140 characters is required.'}, status=400)

    post = TradeRationalePost.objects.create(
        author=request.user, symbol=symbol, action=action, rationale=rationale
    )

    return Response(
        {
            'success': True,
            'post': {
                'id': post.id,
                'username': request.user.username,
                'symbol': post.symbol,
                'action': post.action,
                'rationale': post.rationale,
                'created_at': post.created_at.isoformat(),
            },
        }
    )
