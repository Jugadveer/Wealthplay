/**
 * The stock list and the trade ticket.
 *
 * Real listings quote in their own currency — Apple in dollars, Reliance in
 * rupees. The old screen printed a rupee sign on everything, so AAPL showed as
 * ₹302.45.
 */
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Search } from 'lucide-react'

import { api } from '../../lib/api'
import { compactMoney, money, percent, toneFor } from '../../lib/format'
import { useQuery } from '../../lib/query'
import { Badge, Panel, Skeleton, Tabs, cx } from '../../ui'
import { Sparkline } from '../../ui/charts'
import Trade from './Trade'

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'real', label: 'Listed' },
  { value: 'sim', label: 'Simulated' },
]

export default function Explore() {
  const { symbol } = useParams()
  const navigate = useNavigate()
  const { data, loading } = useQuery('stocks', api.stocks, { ttl: 60_000 })

  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('all')

  const stocks = useMemo(() => {
    const all = data?.stocks ?? []
    const term = query.trim().toLowerCase()

    return all.filter((stock) => {
      if (filter === 'real' && stock.is_custom) return false
      if (filter === 'sim' && !stock.is_custom) return false
      if (!term) return true
      return (
        stock.symbol.toLowerCase().includes(term) || stock.name.toLowerCase().includes(term)
      )
    })
  }, [data, query, filter])

  if (symbol) {
    return <Trade symbol={symbol} onDone={() => navigate('/markets/holdings')} />
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <label className="flex h-10 flex-1 items-center gap-2 rounded border border-rule-strong bg-paper px-3 transition-colors focus-within:border-accent sm:max-w-xs">
          <Search size={15} className="shrink-0 text-ink-faint" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search stocks…"
            aria-label="Search stocks"
            autoComplete="off"
            spellCheck="false"
            className="w-full bg-transparent text-sm text-ink outline-none"
          />
        </label>
        <Tabs items={FILTERS} value={filter} onChange={setFilter} />
      </div>

      {loading && !data ? (
        <div className="grid gap-px bg-rule sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 9 }, (_, index) => (
            <Skeleton key={index} className="h-28 bg-paper" />
          ))}
        </div>
      ) : (
        <div className="grid gap-px border border-rule bg-rule sm:grid-cols-2 lg:grid-cols-3">
          {stocks.map((stock) => (
            <StockRow key={stock.symbol} stock={stock} />
          ))}
        </div>
      )}

      {!loading && stocks.length === 0 && (
        <p className="py-10 text-center text-sm text-ink-muted">Nothing matches “{query}”.</p>
      )}
    </div>
  )
}

function StockRow({ stock }) {
  const navigate = useNavigate()

  return (
    <button
      type="button"
      onClick={() => navigate(`/markets/explore/${stock.symbol}`)}
      className="flex flex-col bg-paper p-4 text-left transition-colors hover:bg-paper-raised"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <span className="num font-semibold text-ink">{stock.symbol}</span>
          <p className="truncate text-xs text-ink-muted">{stock.name}</p>
        </div>
        {stock.is_custom && <Badge>sim</Badge>}
      </div>

      <div className="mt-3 flex items-baseline justify-between gap-2">
        <span className="num text-lg font-semibold text-ink">
          {money(stock.current_price, { currency: stock.currency })}
        </span>
        <span className={cx('num text-sm', toneFor(stock.change_percent))}>
          {percent(stock.change_percent, 2)}
        </span>
      </div>

      <p className="mt-1 text-[11px] text-ink-faint">
        {stock.sector} · {stock.category}
      </p>
    </button>
  )
}
