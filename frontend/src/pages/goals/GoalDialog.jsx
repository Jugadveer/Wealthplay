/**
 * Setting a goal.
 *
 * The first version made the user pick their goal's kind from a grid, which
 * asks them to already know the answer the app exists to work out. Now they
 * describe it in their own words and give their numbers, and the app does the
 * classifying: what kind of goal this is, and how much risk their finances can
 * actually absorb.
 *
 * Then it asks. Capacity and appetite are different questions — the arithmetic
 * decides the first, the person decides the second — so the assessment ends in
 * a choice rather than a verdict.
 */
import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  Briefcase,
  Car,
  Gift,
  GraduationCap,
  Heart,
  Home,
  Plane,
  Shield,
  Sparkles,
  Sunset,
  Wallet,
  X,
} from 'lucide-react'

import { api } from '../../lib/api'
import { money } from '../../lib/format'
import { Badge, Button, cx } from '../../ui'
import PlanView from './PlanView'

export const GOAL_ICONS = {
  shield: Shield,
  'graduation-cap': GraduationCap,
  sunset: Sunset,
  home: Home,
  heart: Heart,
  briefcase: Briefcase,
  car: Car,
  plane: Plane,
  gift: Gift,
  wallet: Wallet,
}

const STANCE_TONE = { can_take_risk: 'up', be_careful: 'accent', stay_safe: 'down' }
const CAPACITY_LABEL = { high: 'Room to take risk', moderate: 'Some room', low: 'Little room' }

function defaultDate() {
  const date = new Date()
  date.setFullYear(date.getFullYear() + 5)
  return date.toISOString().slice(0, 10)
}

export default function GoalDialog({ onClose, onCreated }) {
  const [step, setStep] = useState('details')
  const [values, setValues] = useState({
    description: '',
    target_amount: '',
    target_date: defaultDate(),
    current_amount: '',
    monthly_income: '',
    monthly_commitments: '',
    dependants: '0',
    has_emergency_fund: false,
  })
  const [read, setRead] = useState(null)
  const [appetite, setAppetite] = useState('balanced')
  const [plan, setPlan] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const set = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value
    setValues((current) => ({ ...current, [field]: value }))
    setError('')
  }

  async function assess(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const result = await api.assessGoal(values)
      setRead(result)
      setAppetite(result.assessment.stance === 'stay_safe' ? 'safe' : 'balanced')
      setStep('read')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function showPlan(choice) {
    setAppetite(choice)
    setBusy(true)

    try {
      const result = await api.planGoal({
        category: read.assessment.category,
        target_amount: Number(values.target_amount),
        target_date: values.target_date,
        current_amount: Number(values.current_amount) || 0,
        monthly_capacity: monthlyCapacity(values),
        appetite: choice,
      })
      setPlan(result.plan)
      setStep('plan')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function create() {
    setBusy(true)
    try {
      const { goal } = await api.createGoal({
        title: values.description.trim().slice(0, 120),
        category: read.assessment.category,
        target_amount: Number(values.target_amount),
        current_amount: Number(values.current_amount) || 0,
        monthly_capacity: monthlyCapacity(values),
        target_date: values.target_date,
        plan_choice: plan.recommended,
      })
      onCreated(goal)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const titles = {
    details: 'Tell us about the goal',
    read: 'What your numbers say',
    plan: 'The plan',
  }
  const steps = { details: 'Step one', read: 'Step two', plan: 'Step three' }

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto overscroll-contain bg-scrim/60 p-4 backdrop-blur-sm"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="goal-title"
        className="rise mx-auto w-full max-w-3xl rounded-lg border border-rule bg-paper-raised shadow-float"
      >
        <header className="flex items-start justify-between gap-4 border-b border-rule px-6 py-4">
          <div className="flex items-center gap-3">
            {step !== 'details' && (
              <button
                type="button"
                onClick={() => setStep(step === 'plan' ? 'read' : 'details')}
                aria-label="Back"
                className="rounded p-1 text-ink-muted transition-colors hover:text-ink"
              >
                <ArrowLeft size={16} />
              </button>
            )}
            <div>
              <p className="eyebrow">{steps[step]}</p>
              <h2 id="goal-title" className="mt-0.5 text-title">
                {titles[step]}
              </h2>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded p-1.5 text-ink-muted transition-colors hover:text-ink"
          >
            <X size={16} />
          </button>
        </header>

        {step === 'details' && (
          <Details values={values} set={set} onSubmit={assess} busy={busy} error={error} />
        )}

        {step === 'read' && (
          <Read read={read} busy={busy} appetite={appetite} onChoose={showPlan} />
        )}

        {step === 'plan' && plan && (
          <div className="px-6 py-5">
            {plan.appetite_note && (
              <p className="measure mb-5 rounded border border-play/40 bg-play/10 px-3 py-2 text-xs text-ink">
                {plan.appetite_note}
              </p>
            )}

            <PlanView plan={plan} chosen={plan.recommended} />

            <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-5">
              <p className="num text-xs text-ink-faint">
                {money(
                  plan.plans.find((option) => option.key === plan.recommended)?.monthly_required ?? 0,
                )}{' '}
                a month
              </p>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" onClick={() => setStep('read')}>
                  Change the risk
                </Button>
                <Button type="button" onClick={create} disabled={busy}>
                  {busy ? 'Saving…' : 'Create this goal'}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function monthlyCapacity(values) {
  const income = Number(values.monthly_income) || 0
  const commitments = Number(values.monthly_commitments) || 0
  return Math.max(0, income - commitments)
}

function Details({ values, set, onSubmit, busy, error }) {
  return (
    <form onSubmit={onSubmit} className="px-6 py-5" noValidate>
      <label className="block">
        <span className="eyebrow">What are you saving for? Say it however you like.</span>
        <textarea
          value={values.description}
          onChange={set('description')}
          rows={2}
          maxLength={200}
          placeholder="My daughter's college fees, she's two now"
          className="mt-1.5 w-full rounded border border-rule-strong bg-paper px-3 py-2 text-sm text-ink outline-none transition-colors focus:border-accent"
          required
        />
        <span className="mt-1 block text-[11px] text-ink-faint">
          We work out what kind of goal this is from what you write — you do not have to categorise it.
        </span>
      </label>

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <Field label="What will it cost today?" type="number" min="1"
               value={values.target_amount} onChange={set('target_amount')} required />
        <Field label="When do you need it?" type="date"
               value={values.target_date} onChange={set('target_date')} required />
        <Field label="Saved so far" type="number" min="0"
               value={values.current_amount} onChange={set('current_amount')} />
        <Field label="People who depend on you" type="number" min="0" max="10"
               value={values.dependants} onChange={set('dependants')} />
        <Field label="Your monthly take-home" type="number" min="0"
               value={values.monthly_income} onChange={set('monthly_income')}
               hint="Used to work out how much risk you can afford, not stored anywhere else." required />
        <Field label="Monthly expenses and EMIs" type="number" min="0"
               value={values.monthly_commitments} onChange={set('monthly_commitments')}
               hint="Everything that goes out before you can invest." required />
      </div>

      <label className="mt-4 flex items-start gap-2.5">
        <input
          type="checkbox"
          checked={values.has_emergency_fund}
          onChange={set('has_emergency_fund')}
          className="mt-0.5 h-4 w-4 accent-[rgb(var(--accent))]"
        />
        <span className="text-sm text-ink">
          I already have six months of expenses set aside
          <span className="mt-0.5 block text-[11px] text-ink-faint">
            Without one, a bad month forces you to sell — which changes what you can safely hold.
          </span>
        </span>
      </label>

      {error && (
        <p role="alert" className="mt-4 rounded-sm border border-down/30 bg-down/5 px-3 py-2 text-xs text-ink">
          {error}
        </p>
      )}

      <div className="mt-6 flex justify-end border-t border-rule pt-5">
        <Button type="submit" disabled={busy || !values.description.trim()}>
          {busy ? 'Reading your numbers…' : 'See what this means'}
        </Button>
      </div>
    </form>
  )
}

function Read({ read, busy, appetite, onChoose }) {
  const { assessment, options } = read
  const Icon = GOAL_ICONS[assessment.icon] ?? Wallet

  return (
    <div className="px-6 py-5">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded bg-accent/10 text-accent">
          <Icon size={18} strokeWidth={1.75} />
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium text-ink">{assessment.category_label}</p>
            <Badge tone={STANCE_TONE[assessment.stance]}>
              {CAPACITY_LABEL[assessment.capacity.level]}
            </Badge>
            {assessment.available ? (
              <span className="flex items-center gap-1 text-[11px] text-ink-faint">
                <Sparkles size={11} />
                written for you
              </span>
            ) : (
              <span className="text-[11px] text-ink-faint">computed from your numbers</span>
            )}
          </div>
          <p className="measure mt-2 text-[15px] leading-relaxed text-ink">{assessment.headline}</p>
        </div>
      </div>

      <ul className="mt-5 space-y-2 border-t border-rule pt-4">
        {assessment.reasoning.map((line, index) => (
          <li key={index} className="measure text-sm leading-relaxed text-ink-muted">
            {line}
          </li>
        ))}
      </ul>

      <p className="measure mt-6 border-t border-rule pt-5 text-[15px] text-ink">
        {assessment.question}
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {options.map((option) => {
          const disabled = option.available === false
          return (
            <button
              key={option.key}
              type="button"
              disabled={disabled || busy}
              onClick={() => onChoose(option.key)}
              className={cx(
                'rounded-lg border p-4 text-left transition-[border-color,transform] duration-200',
                disabled
                  ? 'cursor-not-allowed border-rule opacity-50'
                  : 'border-rule hover:-translate-y-0.5 hover:border-accent/60',
                option.key === appetite && !disabled && 'border-accent',
              )}
            >
              <p className="text-sm font-medium text-ink">{option.label}</p>
              <p className="mt-1.5 text-[11px] leading-snug text-ink-muted">{option.detail}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function Field({ label, hint, className, ...props }) {
  return (
    <label className={cx('block', className)}>
      <span className="eyebrow">{label}</span>
      <input
        {...props}
        className="mt-1.5 h-10 w-full rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none transition-colors focus:border-accent"
      />
      {hint && <span className="mt-1 block text-[11px] text-ink-faint">{hint}</span>}
    </label>
  )
}
