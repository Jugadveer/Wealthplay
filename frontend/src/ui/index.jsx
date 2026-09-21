/**
 * The whole UI kit. Small enough to live in one file, which means there is one
 * place to look when something needs to change everywhere.
 *
 * Nothing here holds state or fetches. Composition happens in pages.
 */
import { forwardRef } from 'react'
import { Link } from 'react-router-dom'

/** Join class names, dropping falsey ones. */
export const cx = (...parts) => parts.filter(Boolean).join(' ')

/* -------------------------------------------------------------------------- */
/* Button                                                                      */
/* -------------------------------------------------------------------------- */

// The filled button is ink, not the accent. Keeping the accent off buttons is
// what lets it mean "interactive" everywhere else without competing.
const BUTTON_VARIANTS = {
  primary: 'bg-ink text-paper hover:bg-ink/90',
  secondary:
    'border border-rule-strong bg-paper-raised text-ink hover:border-ink-faint hover:bg-paper-sunken',
  ghost: 'text-ink-muted hover:bg-paper-sunken hover:text-ink',
  danger: 'bg-down text-white hover:opacity-90',
}

const BUTTON_SIZES = {
  sm: 'h-8 gap-1.5 px-3 text-xs',
  md: 'h-10 gap-2 px-4 text-sm',
  lg: 'h-12 gap-2 px-6 text-[15px]',
}

/**
 * Renders as <button>, <a> or react-router <Link> depending on the props given,
 * so a "button that navigates" is still a real link for keyboard and middle-click.
 */
export const Button = forwardRef(function Button(
  { variant = 'primary', size = 'md', to, href, className, disabled, ...props },
  ref,
) {
  const classes = cx(
    'inline-flex select-none items-center justify-center rounded font-medium',
    'transition-[background-color,border-color,color,transform,opacity] duration-200 ease-out',
    'active:scale-[0.98] disabled:pointer-events-none disabled:opacity-45',
    BUTTON_VARIANTS[variant],
    BUTTON_SIZES[size],
    className,
  )

  if (to && !disabled) return <Link ref={ref} to={to} className={classes} {...props} />
  if (href && !disabled) return <a ref={ref} href={href} className={classes} {...props} />
  return <button ref={ref} type="button" className={classes} disabled={disabled} {...props} />
})

/* -------------------------------------------------------------------------- */
/* Surfaces                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * A bordered surface. Elevation is opt-in via `float` because in this design a
 * shadow means "this is above the page", not "this is a card".
 */
export function Panel({ as: Tag = 'section', float = false, className, ...props }) {
  return (
    <Tag
      className={cx(
        'rounded-lg border border-rule bg-paper-raised',
        float ? 'shadow-float' : 'shadow-raise',
        className,
      )}
      {...props}
    />
  )
}

/** Section header: a hairline, a label, a title. The rule separates, the space carries. */
export function SectionHead({ label, title, action, className }) {
  return (
    <div className={cx('flex items-end justify-between gap-4 border-t border-rule pt-4', className)}>
      <div>
        {label && <p className="eyebrow">{label}</p>}
        <h2 className="mt-1.5 text-title">{title}</h2>
      </div>
      {action}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Data display                                                                */
/* -------------------------------------------------------------------------- */

/**
 * A labelled figure. `tone` colours the value for market direction; leave it
 * unset for neutral counts so red never appears where nothing was lost.
 */
export function Stat({ label, value, sub, tone, size = 'md' }) {
  return (
    <div>
      <p className="eyebrow">{label}</p>
      <p
        className={cx(
          'num mt-1.5 font-semibold',
          size === 'lg' ? 'text-3xl' : 'text-xl',
          tone || 'text-ink',
        )}
      >
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-ink-muted">{sub}</p>}
    </div>
  )
}

const BADGE_TONES = {
  neutral: 'border-rule-strong text-ink-muted',
  accent: 'border-accent/40 bg-accent/10 text-accent',
  up: 'border-up/40 bg-up/10 text-up',
  down: 'border-down/40 bg-down/10 text-down',
  play: 'border-play/40 bg-play/10 text-play',
}

/** Square-cornered label, not a pill — pills read as generated. */
export function Badge({ tone = 'neutral', className, ...props }) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 rounded-sm border px-1.5 py-0.5',
        'text-[10px] font-semibold uppercase tracking-wider',
        BADGE_TONES[tone],
        className,
      )}
      {...props}
    />
  )
}

/** Horizontal progress bar. `tone` picks the fill colour. */
export function Meter({ value, max = 100, tone = 'accent', className }) {
  const pct = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0
  const fill = { accent: 'bg-accent', play: 'bg-play', up: 'bg-up' }[tone]

  return (
    <div
      className={cx('h-1.5 w-full overflow-hidden rounded-sm bg-paper-sunken', className)}
      role="progressbar"
      aria-valuenow={Math.round(pct)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className={cx('h-full rounded-sm transition-[width] duration-500 ease-out', fill)}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* States                                                                      */
/* -------------------------------------------------------------------------- */

/** Layout-shaped placeholder. Sized by the caller to match what is loading. */
export function Skeleton({ className }) {
  return <div className={cx('skeleton', className)} aria-hidden="true" />
}

/**
 * Empty states are a composed view with a way forward, not a shrug. Every one
 * in the app takes an action.
 */
export function EmptyState({ icon: Icon, title, body, action }) {
  return (
    <div className="flex flex-col items-center px-6 py-14 text-center">
      {Icon && (
        <div className="mb-4 grid h-11 w-11 place-items-center rounded-lg border border-rule bg-paper-sunken text-ink-faint">
          <Icon size={18} strokeWidth={1.5} />
        </div>
      )}
      <p className="font-display text-title">{title}</p>
      {body && <p className="measure mt-1.5 text-sm text-ink-muted">{body}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

/** Inline failure with a retry. Never an alert(), never a dead end. */
export function ErrorNote({ message, onRetry }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded border border-down/30 bg-down/5 px-4 py-3">
      <p className="text-sm text-ink">{message}</p>
      {onRetry && (
        <Button size="sm" variant="secondary" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Navigation                                                                  */
/* -------------------------------------------------------------------------- */

/**
 * Underline tabs. Rendered once — the portfolio previously shipped two tab bars
 * stacked on top of each other because two components each drew their own.
 */
export function Tabs({ items, value, onChange }) {
  return (
    <div className="flex gap-1 border-b border-rule" role="tablist">
      {items.map((item) => {
        const active = item.value === value
        return (
          <button
            key={item.value}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(item.value)}
            className={cx(
              '-mb-px border-b-2 px-3 py-2.5 text-sm font-medium transition-colors duration-200',
              active
                ? 'border-accent text-ink'
                : 'border-transparent text-ink-muted hover:text-ink',
            )}
          >
            {item.label}
          </button>
        )
      })}
    </div>
  )
}

/** Page title block. One shape for every page, so pages stop looking unrelated. */
export function PageHeader({ eyebrow, title, lede, action, className }) {
  return (
    <header className={cx('flex flex-wrap items-end justify-between gap-6', className)}>
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1 className="mt-2 text-headline">{title}</h1>
        {lede && <p className="measure mt-2.5 text-sm text-ink-muted">{lede}</p>}
      </div>
      {action}
    </header>
  )
}
