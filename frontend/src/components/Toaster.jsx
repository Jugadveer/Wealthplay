/**
 * Notifications and achievement popups.
 *
 * One mount point for everything the app wants to announce. Achievements get a
 * card with the trophy and the XP; everything else is a single line, because a
 * confirmation that takes two lines is a confirmation nobody reads.
 */
import { useEffect, useState } from 'react'
import { AlertTriangle, Check, Info, Trophy, X } from 'lucide-react'

import { dismiss, subscribe } from '../lib/notify'
import { cx } from '../ui'

const TONES = {
  achievement: { icon: Trophy, ring: 'border-play/50', wash: 'bg-play/10', mark: 'text-play' },
  success: { icon: Check, ring: 'border-up/40', wash: 'bg-up/10', mark: 'text-up' },
  error: { icon: AlertTriangle, ring: 'border-down/40', wash: 'bg-down/10', mark: 'text-down' },
  info: { icon: Info, ring: 'border-rule-strong', wash: 'bg-paper-sunken', mark: 'text-ink-muted' },
}

export default function Toaster() {
  const [items, setItems] = useState([])

  useEffect(() => subscribe(setItems), [])

  if (!items.length) return null

  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4 sm:items-end sm:pr-5"
      aria-live="polite"
      aria-relevant="additions"
    >
      {items.map((item) => (
        <Toast key={item.id} item={item} />
      ))}
    </div>
  )
}

function Toast({ item }) {
  const tone = TONES[item.tone] ?? TONES.info
  const Icon = tone.icon
  const celebratory = item.tone === 'achievement'

  return (
    <article
      className={cx(
        'toast-in pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border bg-paper-raised p-3.5 shadow-float',
        tone.ring,
      )}
    >
      <span
        className={cx(
          'grid shrink-0 place-items-center rounded',
          tone.wash,
          tone.mark,
          celebratory ? 'h-9 w-9' : 'h-7 w-7',
        )}
      >
        <Icon size={celebratory ? 18 : 14} />
      </span>

      <div className="min-w-0 flex-1">
        {celebratory && <p className="eyebrow">Achievement unlocked</p>}
        <p className={cx('text-sm text-ink', celebratory && 'font-display text-title')}>
          {item.title}
        </p>
        {item.body && (
          <p className={cx('text-xs text-ink-muted', celebratory ? 'num mt-0.5' : 'mt-0.5')}>
            {item.body}
          </p>
        )}
      </div>

      <button
        type="button"
        onClick={() => dismiss(item.id)}
        aria-label="Dismiss"
        className="-m-1 shrink-0 rounded p-1 text-ink-faint transition-colors hover:text-ink"
      >
        <X size={13} />
      </button>
    </article>
  )
}
