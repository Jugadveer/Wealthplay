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

  const current = STEPS[step]

  async function choose(value) {
    const next = { ...answers, [current.field]: value }
    setAnswers(next)

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
            className={cx(
              'w-full p-4 text-left transition-colors',
              'hover:border-accent hover:bg-paper-raised',
            )}
          >
            <span className="block text-[15px] font-medium text-ink">{label}</span>
            {detail && <span className="mt-0.5 block text-sm text-ink-muted">{detail}</span>}
          </Panel>
        ))}
      </div>

      {step > 0 && (
        <Button variant="ghost" size="sm" className="mt-6" onClick={() => setStep(step - 1)}>
          Back
        </Button>
      )}
    </div>
  )
}
