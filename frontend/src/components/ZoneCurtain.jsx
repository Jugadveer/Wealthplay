/**
 * Booting the practice terminal.
 *
 * Markets is the one place in the app that stops being a reader and becomes an
 * environment: the site navigation goes away and a trading terminal takes over.
 * This is the handover — a running tape, a connection line, and the account
 * opening — so the change of mode reads as arriving somewhere rather than as a
 * page that lost its header.
 *
 * Nowhere else gets one. Today, Learn, Play and Progress are surfaces you open
 * constantly, and a curtain in front of one is an interruption.
 *
 * It fires only on entering Markets from outside — moving between terminal
 * screens shows nothing — lasts under a second, and is skipped entirely under
 * `prefers-reduced-motion`. A transition you cannot skip is a loading screen,
 * and this is not one: the page underneath has already rendered.
 */
import { useEffect, useRef, useState } from 'react'

const DURATION = 850

const ZONES = {
  markets: {
    eyebrow: 'Connecting',
    title: 'Practice terminal',
    lede: 'Real listings. Virtual money. Nothing here touches a real account.',
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

  const { eyebrow, title, lede } = ZONES[showing] ?? {}
  if (!title) return null

  return (
    <div className="curtain" aria-hidden="true">
      <div className="flex w-[min(460px,84vw)] flex-col items-center gap-5 text-center">
        <Tape />
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h2 className="mt-2 text-display leading-none">{title}</h2>
          <p className="mt-2 text-sm text-ink-muted">{lede}</p>
        </div>
        <span className="curtain-link h-px w-full bg-accent" />
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
