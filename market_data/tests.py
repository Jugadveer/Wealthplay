"""
Tests for the market data adapter.

The one that matters is the gap filter. The provider returns an entry for days
it has no price for, with `null` in the close. Those used to arrive from pandas
as `NaN`, which neither `float()` nor `round()` complains about, so they left
this module intact and broke two things far from the cause: the Oracle's chart
question returned a 500 because `json.dumps` refuses NaN, and the Rank It board
failed SQLite's `JSON_VALID` constraint and was silently skipped. Both were
intermittent, because which symbols get drawn depends on the day.

Everything here mocks the transport. A test suite that calls Yahoo is a test
suite that fails when Yahoo is slow.
"""

import json
import math
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from django.test import TestCase, override_settings

from market_data import services

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def chart(closes, volumes=None, meta=None, start=date(2026, 1, 5)):
    """A chart payload shaped the way the provider returns one."""
    midnight = datetime.min.time()
    base = int(datetime.combine(start, midnight, tzinfo=timezone.utc).timestamp())
    return {
        'chart': {
            'result': [{
                'meta': {'regularMarketPrice': 100.0, 'currency': 'USD', **(meta or {})},
                'timestamp': [base + i * 86_400 for i in range(len(closes))],
                'indicators': {'quote': [{
                    'close': closes,
                    'volume': volumes if volumes is not None else [1_000] * len(closes),
                }]},
            }]
        }
    }


@override_settings(CACHES=LOCMEM)
class HistoryTests(TestCase):
    def _history(self, payload, days=90):
        with patch.object(services, '_json', return_value=payload):
            return services._fetch_history('TEST', days)

    def test_a_clean_series_comes_through(self):
        points = self._history(chart([100.0, 101.5, 99.25]))
        self.assertEqual([p['close'] for p in points], [100.0, 101.5, 99.25])

    def test_a_day_with_no_price_is_dropped(self):
        points = self._history(chart([100.0, None, 102.0]))
        self.assertEqual([p['close'] for p in points], [100.0, 102.0])

    def test_no_close_is_ever_non_finite(self):
        points = self._history(chart([None, 100.0, float('inf'), 101.0]))
        self.assertTrue(all(math.isfinite(p['close']) for p in points))

    def test_every_point_survives_json(self):
        """What actually broke: the response could not be serialised."""
        points = self._history(chart([100.0, None, 102.0]))
        self.assertNotIn('NaN', json.dumps(points))

    def test_a_missing_volume_becomes_zero(self):
        points = self._history(chart([100.0, 101.0], volumes=[None, 5_000]))
        self.assertEqual([p['volume'] for p in points], [0, 5_000])

    def test_dates_are_iso_formatted_and_ordered(self):
        points = self._history(chart([1.0, 2.0, 3.0], start=date(2026, 3, 2)))
        self.assertEqual([p['date'] for p in points],
                         ['2026-03-02', '2026-03-03', '2026-03-04'])

    def test_an_empty_payload_is_not_an_error(self):
        self.assertEqual(self._history({'chart': {'result': []}}), [])

    def test_a_provider_failure_is_not_an_error(self):
        self.assertEqual(self._history(None), [])


@override_settings(CACHES=LOCMEM)
class QuoteTests(TestCase):
    def _quote(self, payload, profile=None):
        with patch.object(services, '_json', return_value=payload), \
             patch.object(services, '_fetch_profile', return_value=profile or {}):
            return services._fetch_quote('TEST')

    def test_the_days_move_is_computed_from_the_last_two_closes(self):
        """`chartPreviousClose` is the close before the window, so on a year-long
        range it reports the move since last year rather than since yesterday."""
        quote = self._quote(chart([100.0, 110.0], meta={'regularMarketPrice': 110.0}))
        self.assertEqual(quote['price'], 110.0)
        self.assertEqual(quote['change_percent'], 10.0)

    def test_a_single_bar_reports_no_move_rather_than_a_wrong_one(self):
        quote = self._quote(chart([100.0], meta={'regularMarketPrice': 100.0}))
        self.assertEqual(quote['change_percent'], 0.0)

    def test_the_profile_supplies_sector_and_market_cap(self):
        quote = self._quote(
            chart([100.0, 101.0]),
            profile={'name': 'Test Corp', 'sector': 'Technology', 'marketCap': 1_000},
        )
        self.assertEqual(quote['name'], 'Test Corp')
        self.assertEqual(quote['sector'], 'Technology')
        self.assertEqual(quote['market_cap'], 1_000)

    def test_an_unknown_sector_does_not_become_null(self):
        self.assertEqual(self._quote(chart([100.0, 101.0]))['sector'], 'Unknown')

    def test_a_provider_failure_returns_none(self):
        self.assertIsNone(self._quote(None))


@override_settings(CACHES=LOCMEM)
class NewsTests(TestCase):
    def _news(self, payload, limit=3):
        with patch.object(services, '_json', return_value=payload):
            return services._fetch_news('TEST', limit)

    def test_headlines_are_normalised(self):
        stories = self._news({'news': [{
            'title': 'Something happened',
            'publisher': 'Reuters',
            'link': 'https://example.com/a',
            'providerPublishTime': 1_790_992_895,
        }]})
        self.assertEqual(stories[0]['title'], 'Something happened')
        self.assertEqual(stories[0]['publisher'], 'Reuters')
        self.assertTrue(stories[0]['published'].startswith('2026-'))

    def test_a_story_with_no_title_is_dropped(self):
        """This is what rendered an empty headline dated 1 January 1970."""
        self.assertEqual(self._news({'news': [{'title': '   ', 'publisher': 'X'}]}), [])

    def test_a_missing_timestamp_does_not_become_1970(self):
        stories = self._news({'news': [{'title': 'No date', 'publisher': 'X'}]})
        self.assertEqual(stories[0]['published'], '')

    def test_the_limit_is_respected(self):
        payload = {'news': [{'title': f'Story {i}', 'publisher': 'X'} for i in range(10)]}
        self.assertEqual(len(self._news(payload, limit=3)), 3)

    def test_a_provider_failure_is_not_an_error(self):
        self.assertEqual(self._news(None), [])


class SessionTests(TestCase):
    def test_an_html_crumb_is_rejected(self):
        """An error page is HTML, and an HTML crumb fails every later call."""
        services._reset_session()
        with patch.object(services.curl_requests, 'Session') as session_cls:
            session = session_cls.return_value
            session.get.return_value.status_code = 200
            session.get.return_value.text = '<!DOCTYPE html><html>error</html>'
            _, crumb = services._session()
        services._reset_session()
        self.assertEqual(crumb, '')

    def test_a_good_crumb_is_kept(self):
        services._reset_session()
        with patch.object(services.curl_requests, 'Session') as session_cls:
            session = session_cls.return_value
            session.get.return_value.status_code = 200
            session.get.return_value.text = '39Bdk.Qn6sJ'
            _, crumb = services._session()
        services._reset_session()
        self.assertEqual(crumb, '39Bdk.Qn6sJ')


@override_settings(CACHES=LOCMEM)
class MarketWireTests(TestCase):
    """The wire that merges several symbols' feeds into one list."""

    def _leaders(self, when):
        universe = list(services.TRACKED_SYMBOLS)
        stride = max(1, len(universe) // services.NEWS_SOURCES)
        start = when.toordinal()
        return [universe[(start + o * stride) % len(universe)]
                for o in range(services.NEWS_SOURCES)]

    def test_every_day_polls_a_listing_that_has_news(self):
        """The provider's search index carries no stories for `.NS` tickers.

        The picks used to be five consecutive entries, and the tracked list is
        eight US listings followed by the NSE ones — so roughly a third of days
        landed on an all-Indian window and the whole wire came back empty.
        """
        for offset in range(40):
            day = date(2026, 1, 1) + timedelta(days=offset)
            leaders = self._leaders(day)
            self.assertTrue(
                [s for s in leaders if s not in services.NSE_SYMBOLS],
                f'{day} polls only NSE symbols: {leaders}',
            )

    def test_the_same_story_is_not_listed_twice(self):
        """One story syndicates across several listings' feeds."""
        story = {'title': 'Shared story', 'publisher': 'Reuters',
                 'link': 'https://example.com/a', 'summary': '', 'published': ''}
        with patch.object(services, '_fetch_news', return_value=[story]):
            wire = services._fetch_market_news(limit=8)
        self.assertEqual(len(wire), 1)

    def test_a_failing_symbol_does_not_empty_the_wire(self):
        calls = {'n': 0}

        def flaky(symbol, limit):
            calls['n'] += 1
            if calls['n'] == 1:
                raise RuntimeError('provider down')
            return [{'title': f'Story {symbol}', 'publisher': 'X',
                     'link': f'https://example.com/{symbol}', 'summary': '', 'published': ''}]

        with patch.object(services, '_fetch_news', side_effect=flaky):
            wire = services._fetch_market_news(limit=8)
        self.assertEqual(len(wire), services.NEWS_SOURCES - 1)

    def test_newest_first(self):
        def feed(symbol, limit):
            order = {'AAPL': '2026-01-03T00:00:00', 'MSFT': '2026-01-05T00:00:00'}
            return [{'title': f'S {symbol}', 'publisher': 'X', 'link': f'u/{symbol}',
                     'summary': '', 'published': order.get(symbol, '2026-01-01T00:00:00')}]

        with patch.object(services, '_fetch_news', side_effect=feed):
            wire = services._fetch_market_news(limit=8)
        stamps = [a['published'] for a in wire]
        self.assertEqual(stamps, sorted(stamps, reverse=True))
