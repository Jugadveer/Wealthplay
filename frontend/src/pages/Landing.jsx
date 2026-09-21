/**
 * The landing page.
 *
 * Built as a newspaper front page: a masthead rule, a lead story, a markets
 * strip, and columns. Deliberately none of the generic marketing shape the old
 * page used — centred hero, gradient CTA, a 4-box stat strip, three equal
 * feature cards, a 1-2-3 "how it works", and two invented 5-star testimonials.
 */
import { useEffect, useState } from 'react'
import { ArrowRight } from 'lucide-react'

import { api } from '../lib/api'
import { percent } from '../lib/format'
import { Button } from '../ui'

const openAuth = (mode) => window.dispatchEvent(new CustomEvent('wp:auth', { detail: mode }))

const today = new Date().toLocaleDateString('en-GB', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

export default function Landing() {
  return (
    <div className="mx-auto max-w-page px-4 pb-20">
      <Masthead />
      <Lead />
      <Ticker />
      <Columns />
      <Closing />
    </div>
  )
}

function Masthead() {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-rule py-3 text-[11px] uppercase tracking-widest text-ink-faint">
      <span>{today}</span>
      <span>Practice edition · virtual money only</span>
    </div>
  )
}

function Lead() {
  return (
    <section className="grid gap-10 border-b border-rule py-12 md:grid-cols-[1.25fr_1fr] md:gap-16 md:py-16">
      <div>
        <p className="eyebrow">The daily financial workout</p>
        <h1 className="mt-3 text-display">
          Learn money the way you
          <br />
          read the paper.
        </h1>
        <p className="measure mt-5 text-base text-ink-muted">
          Five minutes a day: one puzzle, one market call, one number to estimate, and five
          questions drawn from what you studied last week. Then practise on a ₹50,000 portfolio
          where being wrong costs nothing.
        </p>

        <div className="mt-7 flex flex-wrap items-center gap-3">
          <Button size="lg" onClick={() => openAuth('signup')}>
            Read today's edition
            <ArrowRight size={16} />
          </Button>
          <button
            type="button"
            onClick={() => openAuth('login')}
            className="text-sm text-ink-muted underline decoration-rule-strong underline-offset-4 transition-colors hover:text-ink"
          >
            I already have an account
          </button>
        </div>
      </div>

      {/* The masthead's counterpart: a sample of the actual daily puzzle rather
          than a stock illustration. */}
      <aside className="self-start rounded-lg border border-rule bg-paper-raised p-5">
        <p className="eyebrow">Today's puzzle</p>
        <h2 className="mt-1 text-title">Ticker Tiles</h2>
        <p className="mt-2 text-sm text-ink-muted">
          Name the listed company in five guesses. Each miss reveals one more clue.
        </p>

        <ol className="mt-4 space-y-2 text-sm">
          {[
            ['Sector', 'Technology'],
            ['Listed in', 'India'],
            ['Market cap', 'over ₹10 trillion'],
            ['Past year', '+18%'],
            ['Starts with', '?'],
          ].map(([label, value], index) => (
            <li
              key={label}
              className="flex items-baseline justify-between gap-3 border-b border-rule pb-2 last:border-0"
              style={{ opacity: index < 3 ? 1 : 0.35 }}
            >
              <span className="eyebrow">{label}</span>
              <span className="num text-ink">{value}</span>
            </li>
          ))}
        </ol>

        <div className="mt-4 flex gap-1" aria-hidden="true">
          {['🟩', '⬛', '⬛', '⬛', '⬛'].map((square, index) => (
            <span key={index} className="text-lg leading-none">
              {square}
            </span>
          ))}
        </div>
      </aside>
    </section>
  )
}

/** Live quotes, because a finance product that shows fake prices is a bad sign. */
function Ticker() {
  const [quotes, setQuotes] = useState([])

  useEffect(() => {
    api
      .quotes('AAPL,MSFT,NVDA,RELIANCE,TCS,HDFCBANK')
      .then((data) => setQuotes(data.quotes.filter((q) => q.price > 0)))
      .catch(() => setQuotes([]))
  }, [])

  if (!quotes.length) return null

  return (
    <section className="overflow-x-auto border-b border-rule py-4">
      <div className="flex min-w-max gap-8">
        {quotes.map((quote) => (
          <div key={quote.symbol} className="flex items-baseline gap-2">
            <span className="num text-xs font-semibold text-ink">{quote.symbol}</span>
            <span className="num text-xs text-ink-muted">
              {quote.currency === 'INR' ? '₹' : '$'}
              {quote.price.toLocaleString('en-IN', { maximumFractionDigits: 2 })}
            </span>
            <span
              className={`num text-xs ${quote.change_percent >= 0 ? 'text-up' : 'text-down'}`}
            >
              {percent(quote.change_percent, 1)}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}

const SECTIONS = [
  {
    kicker: 'Section A',
    title: 'The desk',
    body: 'A ₹50,000 practice portfolio over real listings and a set of fictional stocks that move on their own. Buy, sell, and get told when an exit looked like panic rather than a plan.',
  },
  {
    kicker: 'Section B',
    title: 'The classroom',
    body: 'Twenty-five courses from what a bank account actually does through to options and valuation. Every module ends in questions that come back days later, when forgetting them is the point.',
  },
  {
    kicker: 'Section C',
    title: 'The puzzle page',
    body: 'Ticker Tiles, a daily market call scored on calibration rather than luck, and one real number to estimate. Streaks survive one missed day — you get a freeze every week.',
  },
]

function Columns() {
  return (
    <section className="grid gap-px border-b border-rule bg-rule md:grid-cols-3">
      {SECTIONS.map((section) => (
        <article key={section.title} className="bg-paper px-0 py-10 md:px-6">
          <p className="eyebrow">{section.kicker}</p>
          <h2 className="mt-2 text-title">{section.title}</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-muted">{section.body}</p>
        </article>
      ))}
    </section>
  )
}

function Closing() {
  return (
    <section className="flex flex-wrap items-end justify-between gap-6 py-14">
      <div>
        <h2 className="text-headline">Start with today's edition.</h2>
        <p className="measure mt-2 text-sm text-ink-muted">
          No card, no real money. Everything you trade here is simulated, which is the only
          honest way to learn this.
        </p>
      </div>
      <Button size="lg" onClick={() => openAuth('signup')}>
        Create a free account
      </Button>
    </section>
  )
}
