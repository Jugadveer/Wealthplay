/**
 * Onboarding: five questions that place the learner at a starting level.
 *
 * The point is not data collection — it is skipping material someone already
 * knows. Answers map to a starting XP so an experienced user is not made to
 * sit through "what is a savings account".
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'
import { api } from '../lib/api'
import { invalidate } from '../lib/query'
import { Button, Meter, Panel, cx } from '../ui'

const STEPS = [
  {
    field: 'investment_experience',
    question: 'How much investing have you actually done?',
    options: [
      ['beginner', 'None yet', 'I have not bought anything'],
      ['basics', 'A little', 'A savings account, maybe an FD or a SIP'],
      ['experienced', 'A fair bit', 'I hold funds or stocks and follow them'],
      ['very_experienced', 'A lot', 'I read filings and manage my own allocation'],
    ],
  },
  {
    field: 'financial_goal',
    question: 'What are you doing this for?',
    options: [
      ['long_term_wealth', 'Building wealth', 'A long horizon, no specific date'],
      ['specific_goals', 'Something specific', 'A house, a course, a wedding'],
      ['extra_income', 'Extra income', 'Money that pays me while I work'],
      ['learning', 'Just learning', 'I want to understand how this works'],
    ],
  },
  {
    field: 'risk_tolerance',
    question: 'Your investment drops 20% in a month. What do you do?',
    options: [
      ['safe', 'Sell', 'I would not sleep through that'],
      ['balanced', 'Hold', 'Uncomfortable, but I would wait it out'],
      ['aggressive', 'Buy more', 'Cheaper than last month'],
    ],
  },
  {
    field: 'timeline',
    question: 'When do you need this money?',
    options: [
      ['less_than_1', 'Within a year', ''],
      ['1_to_5', 'One to five years', ''],
      ['5_plus', 'Five years or more', ''],
    ],
  },
  {
    field: 'initial_investment',
    question: 'Roughly how much would you start with?',
    options: [
      ['under_10k', 'Under ₹10,000', ''],
      ['10k_50k', '₹10,000 to ₹50,000', ''],
      ['50k_1lakh', '₹50,000 to ₹1 lakh', ''],
      ['above_1lakh', 'Over ₹1 lakh', ''],
    ],
  },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const { refresh } = useAuth()
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const current = STEPS[step]
  const chosen = answers[current.field]

  async function choose(value) {
    const next = { ...answers, [current.field]: value }
    setAnswers(next)
    setError('')

    if (step < STEPS.length - 1) {
      setStep(step + 1)
      return
    }

    setBusy(true)
    try {
      await api.saveOnboarding(next)
      await refresh()
      invalidate('')
      navigate('/today')
    } catch (failure) {
      // Without this the last answer looked like a dead button: the request
      // failed, `finally` cleared `busy`, and nothing on screen changed.
      setError(failure.message || 'That did not save. Try once more.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl px-4 py-16">
      <p className="eyebrow">
        Question {step + 1} of {STEPS.length}
      </p>
      <Meter value={step} max={STEPS.length} className="mt-3" />

      <h1 className="mt-8 text-headline">{current.question}</h1>

      <div className="mt-8 space-y-2">
        {current.options.map(([value, label, detail]) => (
          <Panel
            as="button"
            key={value}
            onClick={() => choose(value)}
            disabled={busy}
            // Going back has to show what was picked. The answer was already
            // being kept; nothing read it, so every question looked unanswered
            // the second time you saw it.
            aria-pressed={chosen === value}
            // A ring rather than a border colour. `Panel` always applies
            // `border-rule`, and Tailwind emits both at the same specificity,
            // so which one wins is decided by its own sort order rather than
            // by the order they are listed here — `border-accent` lost, and the
            // selected option looked identical to the others.
            className={cx(
              'w-full p-4 text-left transition-colors',
              'hover:border-accent hover:bg-paper-raised',
              chosen === value && 'ring-2 ring-accent',
            )}
          >
            <span className="block text-[15px] font-medium text-ink">{label}</span>
            {detail && <span className="mt-0.5 block text-sm text-ink-muted">{detail}</span>}
          </Panel>
        ))}
      </div>

      {error && (
        <p role="alert" className="mt-4 rounded border border-down/30 bg-down/5 px-3 py-2 text-sm text-ink">
          {error}
        </p>
      )}

      <div className="mt-6 flex items-center gap-3">
        {step > 0 && (
          <Button variant="ghost" size="sm" onClick={() => setStep(step - 1)}>
            Back
          </Button>
        )}
        {/* Only once this question has an answer: it is the way forward after
            going back, and the options themselves advance on first pass. */}
        {chosen && step < STEPS.length - 1 && (
          <Button variant="ghost" size="sm" onClick={() => setStep(step + 1)}>
            Next
          </Button>
        )}
        {busy && <span className="text-sm text-ink-muted">Saving…</span>}
      </div>
    </div>
  )
}
