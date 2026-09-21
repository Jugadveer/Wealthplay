/**
 * The landing page.
 *
 * Asymmetric by design: a lead block beside a real sample of today's puzzle, a
 * live quote strip, then a bento of four unequal blocks. Deliberately none of
 * the generic marketing shape the old page used — centred hero, gradient CTA, a
 * 4-box stat strip, three equal feature cards, a 1-2-3 "how it works", and two
 * invented 5-star testimonials.
 */
import { ArrowRight } from 'lucide-react'

import MarketStrip from '../components/MarketStrip'
import Wire from '../components/Wire'
import { Button, cx } from '../ui'

const openAuth = (mode) => window.dispatchEvent(new CustomEvent('wp:auth', { detail: mode }))

export default function Landing() {
  return (
    <div className="mx-auto max-w-page px-4 pb-24">
      <Lead />
      <MarketStrip />
      <Bento />
      <Wire className="mt-16" />
      <Closing />
      <Footer />
    </div>
  )
}

function Lead() {
  return (
    <section className="grid gap-12 py-14 md:grid-cols-[1.3fr_1fr] md:gap-16 md:py-20">
      <div>
        <p className="eyebrow">Five minutes a day</p>
        <h1 className="mt-4 text-display">
          Money is a skill.
          <br />
          Practise it daily.
        </h1>
        <p className="measure mt-6 text-base text-ink-muted">
          One puzzle, one market call, one number to estimate, and five questions drawn from what
          you studied last week. Then trade a ₹50,000 practice portfolio where being wrong costs
          nothing.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-4">
          <Button size="lg" onClick={() => openAuth('signup')}>
            Start today&rsquo;s set
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

      <PuzzlePreview />
    </section>
  )
}

/** A sample of the actual daily puzzle rather than a stock illustration. */
function PuzzlePreview() {
  const clues = [
    ['Sector', 'Technology'],
    ['Listed in', 'India'],
    ['Market cap', '₹10T+'],
    ['Past year', '+18%'],
    ['Starts with', '?'],
  ]

  return (
    <aside className="self-start rounded-lg border border-rule bg-paper-raised p-6 shadow-raise">
      <div className="flex items-baseline justify-between gap-3">
        <p className="eyebrow">Today&rsquo;s puzzle</p>
        <p className="num text-[11px] text-ink-faint">2 of 5 guesses</p>
      </div>
      <h2 className="mt-2 text-title">Ticker Tiles</h2>
      <p className="mt-2 text-sm text-ink-muted">
        Name the listed company in five guesses. Each miss reveals one more clue.
      </p>

      <dl className="mt-5 divide-y divide-rule border-y border-rule">
        {clues.map(([label, value], index) => (
          <div
            key={label}
            className="flex items-baseline justify-between gap-3 py-2.5"
            style={{ opacity: index < 3 ? 1 : 0.3 }}
          >
            <dt className="eyebrow">{label}</dt>
            <dd className="num text-sm text-ink">{value}</dd>
          </div>
        ))}
      </dl>

      {/* The guess row, drawn in the app's own tokens rather than emoji. Two
          misses so far, which is why three clues are showing. */}
      <div className="mt-5 flex gap-1.5" aria-hidden="true">
        {['INFY', 'WIPRO', '', '', ''].map((guess, index) => (
          <span
            key={index}
            className={cx(
              'num grid h-7 flex-1 place-items-center rounded-sm border text-[10px] font-semibold',
              guess
                ? 'border-rule-strong bg-paper-sunken text-ink-faint'
                : 'border-rule border-dashed',
            )}
          >
            {guess}
          </span>
        ))}
      </div>
    </aside>
  )
}

const BLOCKS = [
  {
    label: 'Markets',
    title: 'Trade without the consequences',
    body: 'A ₹50,000 practice account over real listings plus a set of fictional stocks that move on their own. Buy, sell, and get told when an exit looked like panic rather than a plan.',
    facts: ['₹50,000 to start', 'Live quotes', 'Exit scoring'],
    span: 'md:col-span-7',
  },
  {
    label: 'Learn',
    title: 'Courses that come back to test you',
    body: 'Twenty-five courses, from what a bank account actually does through to options and valuation. Every module ends in questions that return days later, when forgetting them is the point.',
    span: 'md:col-span-5',
  },
  {
    label: 'Play',
    title: 'A new puzzle every morning',
    body: 'Ticker Tiles, a market call scored on calibration rather than luck, and one real number to estimate. Everyone gets the same puzzle, so a result is worth sharing.',
    span: 'md:col-span-5',
  },
  {
    label: 'Progress',
    title: 'Streaks that survive a bad week',
    body: 'One freeze a week, so a missed day does not erase a month. Then your week in numbers: accuracy, XP, and what you got wrong along with when it comes back.',
    facts: ['SM-2 scheduling', 'Weekly recap', 'One freeze a week'],
    span: 'md:col-span-7',
  },
]

function Bento() {
  return (
    <section className="mt-16 grid gap-4 md:grid-cols-12">
      {BLOCKS.map((block) => (
        <article
          key={block.label}
          className={cx(
            'rounded-lg border border-rule bg-paper-raised p-7 transition-colors duration-200 hover:border-rule-strong',
            block.span,
          )}
        >
          <p className="eyebrow">{block.label}</p>
          <h2 className="mt-2.5 text-title">{block.title}</h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-muted">{block.body}</p>

          {block.facts && (
            <ul className="mt-5 flex flex-wrap gap-x-6 gap-y-2 border-t border-rule pt-4">
              {block.facts.map((fact) => (
                <li key={fact} className="num text-xs text-ink-faint">
                  {fact}
                </li>
              ))}
            </ul>
          )}
        </article>
      ))}
    </section>
  )
}

/** Every link here goes somewhere real; there are no placeholder policy pages. */
function Footer() {
  return (
    <footer className="mt-16 flex flex-wrap items-center justify-between gap-4 border-t border-rule pt-6">
      <p className="text-xs text-ink-faint">
        Simulated trading only. Nothing here is investment advice.
      </p>
      <p className="num text-xs text-ink-faint">
        Quotes cached · built with Django and React
      </p>
    </footer>
  )
}

function Closing() {
  return (
    <section className="mt-20 flex flex-wrap items-end justify-between gap-8 border-t border-rule pt-12">
      <div>
        <h2 className="text-headline">Start with today&rsquo;s set.</h2>
        <p className="measure mt-3 text-sm text-ink-muted">
          No card, no real money. Everything you trade here is simulated, which is the only honest
          way to learn this.
        </p>
      </div>
      <Button size="lg" onClick={() => openAuth('signup')}>
        Create a free account
      </Button>
    </section>
  )
}
