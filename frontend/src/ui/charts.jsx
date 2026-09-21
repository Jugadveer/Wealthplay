/**
 * Charts, hand-rolled as SVG.
 *
 * Built rather than pulled from a library so the mark specs hold exactly: 2px
 * strokes, 4px rounded data-ends anchored to the baseline, a 2px surface gap
 * between adjacent fills, recessive grid and axes, and a real crosshair.
 *
 * The categorical palette below is validated, not chosen by eye — both modes
 * clear the lightness band, chroma floor, CVD separation and normal-vision
 * floor on this app's own surfaces (#F7F5EF light, #1D1C17 dark). Four of the
 * light steps sit under 3:1 contrast, which obligates visible direct labels;
 * every chart here ships them, and `Breakdown` pairs the marks with a labelled
 * table rather than relying on colour alone.
 *
 * Series colour is assigned by fixed slot order and never cycled.
 */
import { useId, useState } from 'react'

import { money, percent, shortDate } from '../lib/format'
import { cx } from './index'

const SERIES_LIGHT = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
const SERIES_DARK = ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300']

/** Slot colour for a series index. Past the palette, callers fold into "Other". */
export function seriesColor(index, dark = false) {
  const palette = dark ? SERIES_DARK : SERIES_LIGHT
  return palette[index % palette.length]
}

const isDark = () => document.documentElement.dataset.theme === 'dark'

/* -------------------------------------------------------------------------- */
/* Scales                                                                      */
/* -------------------------------------------------------------------------- */

/**
 * A y-domain that frames the data instead of starting at zero.
 *
 * Zero-anchoring a price series flattens it into a straight line — which is
 * exactly what the portfolio chart used to do, plotting ₹50,000 on a ₹0–₹100
 * axis. Padded by 8% so marks never touch the frame.
 */
function domainFor(values, { includeZero = false } = {}) {
  const clean = values.filter(Number.isFinite)
  if (!clean.length) return [0, 1]

  let low = Math.min(...clean)
  let high = Math.max(...clean)
  if (includeZero) low = Math.min(low, 0)

  if (low === high) return [low - 1, high + 1]

  const pad = (high - low) * 0.08
  return [low - pad, high + pad]
}

/** Four or five round tick values across a domain. */
function ticksFor([low, high], count = 4) {
  const step = (high - low) / count
  return Array.from({ length: count + 1 }, (_, i) => low + step * i)
}

/* -------------------------------------------------------------------------- */
/* Line chart                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * One or more series over time, with a crosshair and tooltip.
 *
 * @param {Array<{label: string, points: Array<{x: string|number, y: number}>}>} series
 * @param {(n: number) => string} [formatY]
 */
export function LineChart({ series, formatY = (n) => money(n), height = 220, className }) {
  const gradientId = useId()
  const [hover, setHover] = useState(null)
  const dark = isDark()

  const drawn = series.filter((s) => s.points.length > 1)
  if (!drawn.length) {
    return <ChartEmpty height={height} message="Not enough history to draw a line yet." />
  }

  const width = 640
  const pad = { top: 12, right: 12, bottom: 24, left: 52 }
  const plotW = width - pad.left - pad.right
  const plotH = height - pad.top - pad.bottom

  const length = Math.max(...drawn.map((s) => s.points.length))
  const domain = domainFor(drawn.flatMap((s) => s.points.map((p) => p.y)))
  const [low, high] = domain

  const xAt = (i) => pad.left + (i / (length - 1)) * plotW
  const yAt = (v) => pad.top + plotH - ((v - low) / (high - low)) * plotH

  const single = drawn.length === 1
  const axisLabels = endpointLabels(drawn[0].points)

  return (
    <figure className={cx('m-0', className)}>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full"
        style={{ height }}
        role="img"
        aria-label={`${drawn.map((s) => s.label).join(' and ')} over time`}
        onMouseLeave={() => setHover(null)}
        onMouseMove={(event) => {
          const box = event.currentTarget.getBoundingClientRect()
          const ratio = ((event.clientX - box.left) / box.width) * width
          const index = Math.round(((ratio - pad.left) / plotW) * (length - 1))
          setHover(index >= 0 && index < length ? index : null)
        }}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={seriesColor(0, dark)} stopOpacity="0.18" />
            <stop offset="100%" stopColor={seriesColor(0, dark)} stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid stays recessive: hairlines in the rule token, never boxed. */}
        {ticksFor(domain).map((value) => (
          <g key={value}>
            <line
              x1={pad.left}
              x2={width - pad.right}
              y1={yAt(value)}
              y2={yAt(value)}
              className="stroke-rule"
              strokeWidth="1"
            />
            <text
              x={pad.left - 8}
              y={yAt(value) + 3}
              textAnchor="end"
              className="fill-ink-faint text-[9px]"
            >
              {formatY(value)}
            </text>
          </g>
        ))}

        {single && (
          <path
            d={`${linePath(drawn[0].points, xAt, yAt)} L ${xAt(drawn[0].points.length - 1)} ${pad.top + plotH} L ${xAt(0)} ${pad.top + plotH} Z`}
            fill={`url(#${gradientId})`}
          />
        )}

        {drawn.map((s, index) => (
          <path
            key={s.label}
            d={linePath(s.points, xAt, yAt)}
            fill="none"
            stroke={seriesColor(index, dark)}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}

        {hover !== null && (
          <g>
            <line
              x1={xAt(hover)}
              x2={xAt(hover)}
              y1={pad.top}
              y2={pad.top + plotH}
              className="stroke-ink-faint"
              strokeWidth="1"
              strokeDasharray="3 3"
            />
            {drawn.map((s, index) => {
              const point = s.points[Math.min(hover, s.points.length - 1)]
              return (
                <circle
                  key={s.label}
                  cx={xAt(hover)}
                  cy={yAt(point.y)}
                  r="4.5"
                  fill={seriesColor(index, dark)}
                  // 2px surface ring keeps overlapping markers separable.
                  className="stroke-paper-raised"
                  strokeWidth="2"
                />
              )
            })}
          </g>
        )}

        {/* Only the endpoints are labelled — a number on every point is noise. */}
        <text x={pad.left} y={height - 6} className="fill-ink-faint text-[9px]">
          {axisLabels[0]}
        </text>
        <text
          x={width - pad.right}
          y={height - 6}
          textAnchor="end"
          className="fill-ink-faint text-[9px]"
        >
          {axisLabels[1]}
        </text>
      </svg>

      {hover !== null && (
        <figcaption className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
          <span className="text-ink-faint">
            {labelOf(drawn[0].points[Math.min(hover, drawn[0].points.length - 1)])}
          </span>
          {drawn.map((s, index) => (
            <span key={s.label} className="flex items-center gap-1.5">
              <span
                className="h-2 w-2 rounded-sm"
                style={{ background: seriesColor(index, dark) }}
                aria-hidden="true"
              />
              <span className="text-ink-muted">{s.label}</span>
              <span className="num font-medium text-ink">
                {formatY(s.points[Math.min(hover, s.points.length - 1)].y)}
              </span>
            </span>
          ))}
        </figcaption>
      )}

      {/* A legend is always present for two or more series, so identity is
          never carried by colour alone. */}
      {drawn.length > 1 && hover === null && (
        <figcaption className="mt-2 flex flex-wrap gap-4 text-xs">
          {drawn.map((s, index) => (
            <span key={s.label} className="flex items-center gap-1.5 text-ink-muted">
              <span
                className="h-2 w-2 rounded-sm"
                style={{ background: seriesColor(index, dark) }}
                aria-hidden="true"
              />
              {s.label}
            </span>
          ))}
        </figcaption>
      )}
    </figure>
  )
}

const labelOf = (point) => (typeof point?.x === 'string' ? shortDate(point.x) : String(point?.x ?? ''))

/**
 * Labels for the first and last point.
 *
 * When the whole series falls on one day — a portfolio opened this morning —
 * two identical dates tell the reader nothing, so it switches to clock time.
 */
function endpointLabels(points) {
  const first = points[0]
  const last = points.at(-1)
  const sameDay = labelOf(first) === labelOf(last)

  if (!sameDay) return [labelOf(first), labelOf(last)]

  const time = (point) => {
    const date = new Date(point.x)
    return Number.isNaN(date.getTime())
      ? labelOf(point)
      : date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }
  return [time(first), `${time(last)} · ${labelOf(last)}`]
}

function linePath(points, xAt, yAt) {
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xAt(i)} ${yAt(p.y)}`).join(' ')
}

/* -------------------------------------------------------------------------- */
/* Sparkline                                                                   */
/* -------------------------------------------------------------------------- */

/** A bare trend line for tight spaces. Coloured by direction, never by brand. */
export function Sparkline({ values, height = 32, className }) {
  if (!values || values.length < 2) return null

  const width = 100
  const [low, high] = domainFor(values)
  const rising = values.at(-1) >= values[0]

  const path = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width
      const y = height - ((value - low) / (high - low)) * height
      return `${index === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={cx('w-full', className)}
      style={{ height }}
      aria-hidden="true"
    >
      <path
        d={path}
        fill="none"
        strokeWidth="2"
        strokeLinecap="round"
        className={rising ? 'stroke-up' : 'stroke-down'}
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  )
}

/* -------------------------------------------------------------------------- */
/* Breakdown                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * Composition as labelled horizontal bars.
 *
 * A bar chart rather than a donut: labels sit beside their marks, magnitudes
 * are directly comparable, and it does not depend on colour discrimination —
 * which matters because a donut would need the stricter all-pairs colour gate
 * that only three slots clear. The previous donut also simply did not render.
 */
export function Breakdown({ items, total, formatValue = (n) => money(n), className }) {
  const dark = isDark()
  const rows = [...items].sort((a, b) => b.value - a.value)
  const sum = total || rows.reduce((acc, row) => acc + row.value, 0) || 1

  if (!rows.length) {
    return <ChartEmpty height={120} message="Nothing to break down yet." />
  }

  return (
    <div className={cx('space-y-3', className)}>
      {rows.map((row, index) => {
        const share = (row.value / sum) * 100
        return (
          <div key={row.label}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="flex items-center gap-2 text-ink">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-sm"
                  style={{ background: seriesColor(index, dark) }}
                  aria-hidden="true"
                />
                {row.label}
              </span>
              <span className="num shrink-0 text-ink-muted">
                {formatValue(row.value)}
                <span className="ml-2 border-l border-rule pl-2 text-ink-faint">
                  {share.toFixed(0)}%
                </span>
              </span>
            </div>
            <div className="mt-1.5 h-2 overflow-hidden rounded-sm bg-paper-sunken">
              <div
                className="h-full rounded-sm transition-[width] duration-500 ease-out"
                style={{ width: `${share}%`, background: seriesColor(index, dark) }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Column chart                                                                */
/* -------------------------------------------------------------------------- */

/** Vertical bars with rounded data-ends and a 2px gap between neighbours. */
export function Columns({ items, height = 160, formatValue = (n) => money(n), className }) {
  const [hover, setHover] = useState(null)
  const dark = isDark()

  if (!items.length) return <ChartEmpty height={height} message="No data." />

  const max = Math.max(...items.map((i) => i.value), 0) || 1
  const gap = 2

  return (
    <figure className={cx('m-0', className)}>
      <div className="flex items-end gap-0.5" style={{ height }}>
        {items.map((item, index) => (
          <button
            key={item.label}
            type="button"
            className="group relative flex h-full flex-1 flex-col justify-end"
            style={{ marginRight: index === items.length - 1 ? 0 : gap }}
            onMouseEnter={() => setHover(index)}
            onMouseLeave={() => setHover(null)}
            onFocus={() => setHover(index)}
            onBlur={() => setHover(null)}
            aria-label={`${item.label}: ${formatValue(item.value)}`}
          >
            <div
              className="w-full rounded-t transition-[height] duration-500 ease-out"
              style={{
                height: `${Math.max(2, (item.value / max) * 100)}%`,
                background: item.color || seriesColor(index, dark),
                opacity: hover === null || hover === index ? 1 : 0.55,
              }}
            />
          </button>
        ))}
      </div>

      <figcaption className="mt-2 flex justify-between text-[10px] text-ink-faint">
        <span>{items[0].label}</span>
        {hover !== null && (
          <span className="num text-ink">
            {items[hover].label} · {formatValue(items[hover].value)}
          </span>
        )}
        <span>{items.at(-1).label}</span>
      </figcaption>
    </figure>
  )
}

/* -------------------------------------------------------------------------- */
/* Shared                                                                      */
/* -------------------------------------------------------------------------- */

function ChartEmpty({ height, message }) {
  return (
    <div
      className="grid place-items-center rounded border border-dashed border-rule text-xs text-ink-faint"
      style={{ height }}
    >
      {message}
    </div>
  )
}

/** A signed percentage in its market colour, for use beside a chart. */
export function Delta({ value, className }) {
  const tone = value > 0 ? 'text-up' : value < 0 ? 'text-down' : 'text-ink-muted'
  return <span className={cx('num', tone, className)}>{percent(value)}</span>
}
