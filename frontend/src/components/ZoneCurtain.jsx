/**
 * The transition into Markets and into Play.
 *
 * Only those two. They are the places where the app stops being a reader and
 * becomes an environment — a trading account, an arcade — and the entry says
 * so: a running tape for Markets, flipping tiles for Play. Today, Learn and
 * Progress are reading surfaces you arrive at constantly, and a curtain in
 * front of them is an interruption rather than an arrival.
 *
 * It fires only when the zone actually changes — moving between tabs inside
 * Markets shows nothing — lasts under a second, and is skipped entirely when
 * the visitor has asked for reduced motion. A transition you cannot skip is a
 * loading screen, and this is not one: the page underneath has already rendered.
 */
import { useEffect, useRef, useState } from 'react'

const DURATION = 850

const ZONES = {
  markets: {
    eyebrow: 'Practice account',
    title: 'Markets',
    lede: 'Real listings, virtual money.',
    motif: Tape,
  },
  play: {
    eyebrow: 'Scored on reasoning',
    title: 'Play',
    lede: 'Call it, defend it, climb the board.',
    motif: Tiles,
  },
}

const prefersReducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

export default function ZoneCurtain({ zone }) {
  const [showing, setShowing] = useState(null)
  const previous = useRef(zone)

  useEffect(() => {
    const changed = zone && zone !== previous.current && zone in ZONES
    previous.current = zone

    // Nothing on first paint, on a zone without an entry, or when the visitor
    // has asked for less movement.
    if (!changed || prefersReducedMotion()) return undefined

    setShowing(zone)
    const timer = setTimeout(() => setShowing(null), DURATION)
    return () => clearTimeout(timer)
  }, [zone])

  if (!showing) return null

  const { eyebrow, title, lede, motif: Motif } = ZONES[showing] ?? {}
  if (!title) return null

  return (
    <div className="curtain" aria-hidden="true">
      <div className="flex flex-col items-center gap-5 px-6 text-center">
        <Motif />
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 className="mt-2 text-display leading-none">{title}</h2>
          <p className="mt-2 text-sm text-ink-muted">{lede}</p>
        </div>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Motifs                                                                      */
/* -------------------------------------------------------------------------- */

const TAPE = ['RELIANCE', 'AAPL', 'TCS', 'NVDA', 'INFY', 'MSFT', 'SBIN']

/** A running tape, which is what a trading screen is. */
function Tape() {
  return (
    <div className="no-scrollbar w-[min(420px,80vw)] overflow-hidden border-y border-rule py-2">
      <div className="curtain-tape flex w-max gap-6">
        {[...TAPE, ...TAPE].map((symbol, index) => (
          <span key={index} className="num text-xs font-semibold text-accent">
            {symbol}
          </span>
        ))}
      </div>
    </div>
  )
}

/** Four tiles turning over, which is what every game here does. */
function Tiles() {
  return (
    <div className="flex gap-2">
      {[0, 1, 2, 3].map((index) => (
        <span
          key={index}
          className="curtain-tile h-10 w-10 rounded-sm bg-accent"
          style={{ animationDelay: `${index * 90}ms` }}
        />
      ))}
    </div>
  )
}
