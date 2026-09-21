"""
Tests for the market data adapter.

The one that matters is the NaN filter. The provider returns a row for days it
has no price for, with ``NaN`` in the close, and neither ``float()`` nor
``round()`` complains about it. Those rows used to leave this module intact and
break two things far away from here: the Oracle's chart question returned a 500
because ``json.dumps`` refuses NaN, and the Rank It board failed SQLite's
``JSON_VALID`` constraint and was skipped. Both were intermittent, because which
symbols get drawn depends on the day.
"""

import math
from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase

from market_data import services


def frame(closes, volumes=None):
    """A provider frame with a daily index, as yfinance returns one."""
    volumes = volumes if volumes is not None else [1_000] * len(closes)
    return pd.DataFrame(
        {'Close': closes, 'Volume': volumes},
        index=pd.date_range('2026-01-01', periods=len(closes), freq='D'),
    )


class HistoryTests(TestCase):
    def _history(self, data):
        ticker = Mock()
        ticker.history.return_value = data
        with patch.object(services.yf, 'Ticker', return_value=ticker):
            return services._fetch_history('TEST', 90)

    def test_a_clean_series_comes_through(self):
        points = self._history(frame([100.0, 101.5, 99.25]))
        self.assertEqual([p['close'] for p in points], [100.0, 101.5, 99.25])

    def test_a_day_with_no_price_is_dropped(self):
        points = self._history(frame([100.0, float('nan'), 102.0]))
        self.assertEqual([p['close'] for p in points], [100.0, 102.0])

    def test_no_close_is_ever_non_finite(self):
        points = self._history(frame([float('nan'), 100.0, float('inf'), 101.0]))
        self.assertTrue(all(math.isfinite(p['close']) for p in points))

    def test_a_missing_volume_becomes_zero_rather_than_raising(self):
        """`int(nan)` raises, which would take out the whole request."""
        points = self._history(frame([100.0, 101.0], volumes=[float('nan'), 5_000]))
        self.assertEqual([p['volume'] for p in points], [0, 5_000])

    def test_an_empty_frame_is_not_an_error(self):
        self.assertEqual(self._history(pd.DataFrame()), [])

    def test_every_point_survives_json(self):
        """What actually broke: the response could not be serialised."""
        import json

        points = self._history(frame([100.0, float('nan'), 102.0]))
        self.assertNotIn('NaN', json.dumps(points))
