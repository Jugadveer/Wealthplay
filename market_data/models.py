from django.db import models


class MarketNewsCache(models.Model):
    """Durable news cache, kept as a backstop behind the in-memory cache.

    ``market_data.services`` serves reads from Django's cache. This table
    survives a restart, so a cold process does not have to hit the provider for
    every symbol at once.
    """

    symbol = models.CharField(max_length=20, primary_key=True)
    news_json = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'market news cache'

    def __str__(self):
        return f'{self.symbol} @ {self.last_updated:%Y-%m-%d %H:%M}'
