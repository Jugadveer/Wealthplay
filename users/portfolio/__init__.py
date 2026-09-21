"""Demo trading portfolio.

Layers, outermost first:

* :mod:`views`      -- HTTP endpoints, no logic
* :mod:`insights`   -- analysis over a valued portfolio
* :mod:`valuation`  -- what the holdings are worth
* :mod:`pricing`    -- quotes and currency, delegating to ``market_data.services``
* :mod:`simulation` -- daily movement for the fictional practice stocks
"""

from .pricing import history, price, quote, sector_profile, to_inr, usd_to_inr
from .valuation import read_history, record_snapshot, value_portfolio

__all__ = [
    'history',
    'price',
    'quote',
    'read_history',
    'record_snapshot',
    'sector_profile',
    'to_inr',
    'usd_to_inr',
    'value_portfolio',
]
