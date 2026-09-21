/**
 * A live quote strip.
 *
 * Polled rather than fetched once, because a markets product whose prices never
 * move is a screenshot. A price that changed flashes in its direction for a
 * moment — the only animation in the app that is carrying information rather
 * than decorating.
 *
 * Shared by the landing page and the signed-in home so there is one place to
 * change how a quote is rendered.
 */
import { useEffect, useRef, useState } from 'react'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { cx } from '../ui'

export const DEFAULT_SYMBOLS = 'AAPL,MSFT,NVDA,RELIANCE,TCS,HDFCBANK'
const REFRESH_MS = 30_000

export default function MarketStrip({ symbols = DEFAULT_SYMBOLS, className }) {
  const [quotes, setQuotes] = useState([])
  const previous = useRef({})

  useEffect(() => {
    let cancelled = false

    const load = () =>
      api
        .quotes(symbols)
        .then((data) => {
          if (cancelled) return
          setQuotes((current) => {
            previous.current = Object.fromEntries(current.map((quote) => [quote.symbol, quote.price]))
            return data.quotes.filter((quote) => quote.price > 0)
          })
        })
        .catch(() => {})

    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [symbols])

  if (!quotes.length) return null

  return (
    <section
      className={cx('no-scrollbar overflow-x-auto border-y border-rule py-3.5', className)}
      aria-label="Live quotes"
    >
      <div className="flex min-w-max items-baseline gap-7">
        {quotes.map((quote) => {
          const was = previous.current[quote.symbol]
          const moved =
            was !== undefined && was !== quote.price ? (quote.price > was ? 'up' : 'down') : null

          return (
            <div key={quote.symbol} className="flex items-baseline gap-2">
              <span className="num text-xs font-semibold text-ink">{quote.symbol}</span>
              <span
                key={`${quote.symbol}-${quote.price}`}
                className={cx('num rounded-sm px-1 text-xs text-ink-muted', moved && `flash-${moved}`)}
              >
                {quote.currency === 'INR' ? '₹' : '$'}
                {quote.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
              </span>
              <span
                className={cx('num text-xs', quote.change_percent >= 0 ? 'text-up' : 'text-down')}
              >
                {percent(quote.change_percent, 1)}
              </span>
            </div>
          )
        })}
      </div>
    </section>
  )
}
