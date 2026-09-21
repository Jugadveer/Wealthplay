/**
 * Setting a goal.
 *
 * Two steps rather than one form. First what the goal is — and the kind matters,
 * because it decides how much risk the plan may carry. Then the numbers, with
 * the plan recalculating as they are typed, so the monthly figure is visible
 * before the goal is committed rather than after.
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

const CRITICALITY_TONE = { critical: 'down', important: 'accent', flexible: 'neutral' }
const CRITICALITY_LABEL = {
  critical: 'Cannot slip',
  important: 'Can slip a little',
  flexible: 'Can slip',
}

/** Two years out, as a sensible default the user will usually change. */
function defaultDate() {
  const date = new Date()
  date.setFullYear(date.getFullYear() + 2)
  return date.toISOString().slice(0, 10)
}

export default function GoalDialog({ categories, onClose, onCreated }) {
  const [step, setStep] = useState('kind')
  const [category, setCategory] = useState(null)
  const [values, setValues] = useState({
    title: '',
    target_amount: '',
    current_amount: '',
    monthly_capacity: '',
    target_date: defaultDate(),
  })
  const [plan, setPlan] = useState(null)
  const [choice, setChoice] = useState('balanced')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  // Recalculate as the numbers are typed, debounced so a four-digit amount is
  // one request rather than four.
  useEffect(() => {
    if (step !== 'numbers' || !category) return undefined
    const amount = Number(values.target_amount)
    if (!amount || !values.target_date) {
      setPlan(null)
      return undefined
    }

    const timer = setTimeout(() => {
      api
        .planGoal({
          category: category.key,
          target_amount: amount,
          target_date: values.target_date,
          current_amount: Number(values.current_amount) || 0,
          monthly_capacity: Number(values.monthly_capacity) || 0,
        })
        .then((data) => {
          setPlan(data.plan)
          setChoice(data.plan.recommended)
        })
        .catch(() => setPlan(null))
    }, 350)

    return () => clearTimeout(timer)
  }, [step, category, values])

  const set = (field) => (event) => {
    setValues((current) => ({ ...current, [field]: event.target.value }))
    setError('')
  }

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      const { goal } = await api.createGoal({
        title: values.title.trim(),
        category: category.key,
        target_amount: Number(values.target_amount),
        current_amount: Number(values.current_amount) || 0,
        monthly_capacity: Number(values.monthly_capacity) || 0,
        target_date: values.target_date,
        plan_choice: choice,
      })
      onCreated(goal)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

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
            {step === 'numbers' && (
              <button
                type="button"
                onClick={() => setStep('kind')}
                aria-label="Back"
                className="rounded p-1 text-ink-muted transition-colors hover:text-ink"
              >
                <ArrowLeft size={16} />
              </button>
            )}
            <div>
              <p className="eyebrow">{step === 'kind' ? 'Step one' : 'Step two'}</p>
              <h2 id="goal-title" className="mt-0.5 text-title">
                {step === 'kind' ? 'What are you saving for?' : category.label}
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

        {step === 'kind' ? (
          <KindPicker
            categories={categories}
            onPick={(picked) => {
              setCategory(picked)
              setValues((current) => ({ ...current, title: current.title || picked.label }))
              setStep('numbers')
            }}
          />
        ) : (
          <form onSubmit={submit} className="px-6 py-5" noValidate>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Call it something" value={values.title} onChange={set('title')} required />
              <Field
                label="Target date"
                type="date"
                value={values.target_date}
                onChange={set('target_date')}
                required
              />
              <Field
                label="What will it cost today?"
                type="number"
                min="1"
                value={values.target_amount}
                onChange={set('target_amount')}
                hint="Today's price. We inflate it for you."
                required
              />
              <Field
                label="Saved so far"
                type="number"
                min="0"
                value={values.current_amount}
                onChange={set('current_amount')}
              />
              <Field
                label="What can you set aside monthly?"
                type="number"
                min="0"
                value={values.monthly_capacity}
                onChange={set('monthly_capacity')}
                hint="From your income, after expenses. This is what makes it a plan."
                className="sm:col-span-2"
              />
            </div>

            {plan && (
              <div className="mt-6 border-t border-rule pt-6">
                <PlanView plan={plan} chosen={choice} onChoose={setChoice} />
              </div>
            )}

            {error && (
              <p role="alert" className="mt-4 rounded-sm border border-down/30 bg-down/5 px-3 py-2 text-xs text-ink">
                {error}
              </p>
            )}

            <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-rule pt-5">
              <p className="num text-xs text-ink-faint">
                {plan
                  ? `${plan.plans.find((option) => option.key === choice)?.label}: ${money(
                      plan.plans.find((option) => option.key === choice)?.monthly_required ?? 0,
                    )} a month`
                  : 'Enter an amount and a date to see the plan'}
              </p>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button type="submit" disabled={busy || !values.target_amount}>
                  {busy ? 'Saving…' : 'Create this goal'}
                </Button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}

function KindPicker({ categories, onPick }) {
  return (
    <div className="px-6 py-5">
      <p className="measure text-sm text-ink-muted">
        The kind of goal decides how much risk its plan may carry. A holiday can slip by six months;
        school fees in the year they are due cannot.
      </p>

      <div className="stagger mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {categories.map((category, index) => {
          const Icon = GOAL_ICONS[category.icon] ?? Wallet
          return (
            <button
              key={category.key}
              type="button"
              onClick={() => onPick(category)}
              style={{ animationDelay: `${index * 35}ms` }}
              className="flex flex-col items-start gap-2 rounded-lg border border-rule bg-paper p-4 text-left transition-[border-color,transform] duration-200 hover:-translate-y-0.5 hover:border-accent/50"
            >
              <span className="grid h-9 w-9 place-items-center rounded bg-accent/10 text-accent">
                <Icon size={17} strokeWidth={1.75} />
              </span>
              <span className="text-sm font-medium text-ink">{category.label}</span>
              <Badge tone={CRITICALITY_TONE[category.criticality]}>
                {CRITICALITY_LABEL[category.criticality]}
              </Badge>
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
