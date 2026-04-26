from django.db import models

class MarketNewsCache(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True)
    news_json = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.symbol} - {self.last_updated}"


