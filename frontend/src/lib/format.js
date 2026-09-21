/**
 * Number and date formatting.
 *
 * Everything user-facing goes through here. The app previously rendered
 * "₹45,521.5" next to "₹45,521.50" and put the sign before the symbol
 * ("+₹0.00"); both came from ad-hoc template strings scattered across pages.
 */

const SYMBOLS = { INR: '₹', USD: '$', EUR: '€', GBP: '£' }

/** Locale that gives the right digit grouping for a currency (1,00,000 vs 100,000). */
const localeFor = (currency) => (currency === 'INR' ? 'en-IN' : 'en-US')

/**
 * Format money. The sign always follows the symbol: "-₹1,200.00", never "₹-1,200.00".
 *
 * @param {number} value
 * @param {object} [options]
 * @param {string} [options.currency='INR']  ISO code. AAPL is USD, RELIANCE is INR.
 * @param {boolean} [options.signed=false]   Prefix non-negative values with "+".
 * @param {number} [options.decimals=2]
 */
export function money(value, { currency = 'INR', signed = false, decimals = 2 } = {}) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'

  const symbol = SYMBOLS[currency] ?? `${currency} `
  const body = Math.abs(n).toLocaleString(localeFor(currency), {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })

  const sign = n < 0 ? '-' : signed ? '+' : ''
  return `${sign}${symbol}${body}`
}

/** Compact money for tight spaces: ₹1.2Cr, $4.5B. */
export function compactMoney(value, currency = 'INR') {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'

  const symbol = SYMBOLS[currency] ?? `${currency} `
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''

  // Indian numbering uses lakh/crore; everywhere else uses K/M/B/T.
  const scale =
    currency === 'INR'
      ? [
          [1e7, 'Cr'],
          [1e5, 'L'],
          [1e3, 'K'],
        ]
      : [
          [1e12, 'T'],
          [1e9, 'B'],
          [1e6, 'M'],
          [1e3, 'K'],
        ]

  for (const [threshold, suffix] of scale) {
    if (abs >= threshold) {
      return `${sign}${symbol}${(abs / threshold).toFixed(abs / threshold >= 100 ? 0 : 1)}${suffix}`
    }
  }
  return `${sign}${symbol}${abs.toFixed(0)}`
}

/** Percentages are always signed — the reader needs the direction, not just the size. */
export function percent(value, decimals = 2) {
  const n = Number(value)
  if (!Number.isFinite(n)) return '—'
  return `${n >= 0 ? '+' : '-'}${Math.abs(n).toFixed(decimals)}%`
}

/** Plain integer with grouping: 1,240. */
export function count(value) {
  const n = Number(value)
  return Number.isFinite(n) ? n.toLocaleString('en-IN') : '—'
}

/**
 * Tailwind text colour for a market value.
 * Zero is deliberately neutral: a flat day is not a win.
 */
export function toneFor(value) {
  const n = Number(value)
  if (!Number.isFinite(n) || n === 0) return 'text-ink-muted'
  return n > 0 ? 'text-up' : 'text-down'
}

/** "17 Sep" / "17 Sep 2025" when the year differs from now. */
export function shortDate(input) {
  const d = input instanceof Date ? input : new Date(input)
  if (Number.isNaN(d.getTime())) return '—'

  const sameYear = d.getFullYear() === new Date().getFullYear()
  return d.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    ...(sameYear ? {} : { year: 'numeric' }),
  })
}

/** "2h ago", "3d ago". Returns null for timestamps that are clearly bogus. */
export function relativeTime(input) {
  const d = input instanceof Date ? input : new Date(input)
  // yfinance hands back 0 for missing timestamps, which becomes 1 Jan 1970.
  if (Number.isNaN(d.getTime()) || d.getFullYear() < 2000) return null

  const seconds = Math.round((Date.now() - d.getTime()) / 1000)
  const steps = [
    [60, 'second'],
    [60, 'minute'],
    [24, 'hour'],
    [7, 'day'],
    [4.35, 'week'],
    [12, 'month'],
  ]

  let value = seconds
  let unit = 'second'
  for (const [size, name] of steps) {
    if (Math.abs(value) < size) break
    value = Math.round(value / size)
    unit = name
  }

  if (unit === 'second' && Math.abs(value) < 45) return 'just now'
  return `${value}${unit[0]}${unit === 'month' ? 'o' : ''} ago`
}
