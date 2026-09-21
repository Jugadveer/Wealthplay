/**
 * Nex, the mentor.
 *
 * One component for the whole app. There used to be two — a floating one and a
 * lesson one — with separate prompts, separate histories and separate
 * greetings, one of which called the mentor "Next".
 *
 * On a lesson route it picks up the course and module from the URL and the
 * answers are grounded in that module.
 */
import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { MessageSquare, Send, X } from 'lucide-react'

import { api } from '../lib/api'
import { Button, cx } from '../ui'

/** Read `/learn/:courseId/:moduleId` out of the current path. */
function lessonContext(pathname) {
  const match = pathname.match(/^\/learn\/([^/]+)\/([^/]+)/)
  return match ? { course_id: match[1], module_id: match[2] } : {}
}

export default function Mentor() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const endRef = useRef(null)

  const context = lessonContext(pathname)
  const scoped = Boolean(context.course_id)

  // Load persisted history when opening on a lesson, so the conversation
  // survives a reload.
  useEffect(() => {
    if (!open || !scoped) return

    let cancelled = false
    api
      .mentorHistory(context.course_id, context.module_id)
      .then((data) => !cancelled && data.messages.length && setMessages(data.messages))
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [open, scoped, context.course_id, context.module_id])

  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  async function send(event) {
    event.preventDefault()
    const question = draft.trim()
    if (!question || busy) return

    setMessages((current) => [...current, { role: 'user', text: question }])
    setDraft('')
    setBusy(true)

    try {
      const { reply, available } = await api.askMentor({ question, ...context })
      setMessages((current) => [...current, { role: 'assistant', text: reply, degraded: !available }])
    } catch (error) {
      setMessages((current) => [...current, { role: 'assistant', text: error.message, degraded: true }])
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-5 right-5 z-40 flex h-12 w-12 items-center justify-center rounded-lg border border-rule bg-paper-raised text-ink shadow-float transition-transform hover:scale-105 active:scale-95"
        aria-label="Ask Nex"
      >
        <MessageSquare size={18} />
      </button>
    )
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex h-[520px] w-[min(380px,calc(100vw-2.5rem))] flex-col rounded-lg border border-rule bg-paper-raised shadow-float rise">
      <header className="flex items-center justify-between border-b border-rule px-4 py-3">
        <div>
          <p className="font-display text-base leading-none text-ink">Nex</p>
          <p className="mt-1 text-[11px] text-ink-faint">
            {scoped ? 'Answering from this lesson' : 'Ask about money or markets'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded p-1.5 text-ink-muted transition-colors hover:text-ink"
          aria-label="Close"
        >
          <X size={16} />
        </button>
      </header>

      <div
        className="flex-1 space-y-3 overflow-y-auto overscroll-contain p-4"
        aria-live="polite"
        aria-atomic="false"
      >
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-sm text-ink-muted">
              {scoped
                ? 'Ask anything about this module and I will answer from it.'
                : 'Ask me about a term, a number, or a decision you are weighing.'}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {(scoped
                ? ['Explain this simply', 'Give me an example', 'Why does this matter?']
                : ['What is an index fund?', 'How much emergency fund?', 'Explain SIP vs lump sum']
              ).map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setDraft(prompt)}
                  className="rounded-sm border border-rule px-2 py-1 text-[11px] text-ink-muted transition-colors hover:border-ink-faint hover:text-ink"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={cx('flex', message.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            <p
              className={cx(
                'max-w-[85%] whitespace-pre-wrap rounded px-3 py-2 text-sm leading-relaxed',
                message.role === 'user'
                  ? 'bg-accent text-accent-on'
                  : message.degraded
                    ? 'border border-rule bg-paper-sunken text-ink-muted'
                    : 'bg-paper-sunken text-ink',
              )}
            >
              {message.text}
            </p>
          </div>
        ))}

        {busy && (
          <div className="flex gap-1 px-1" aria-label="Nex is thinking">
            {[0, 1, 2].map((dot) => (
              <span
                key={dot}
                className="h-1.5 w-1.5 animate-pulse rounded-full bg-ink-faint"
                style={{ animationDelay: `${dot * 150}ms` }}
              />
            ))}
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form onSubmit={send} className="flex gap-2 border-t border-rule p-3">
        <input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          // Submitting on Enter explicitly rather than relying on implicit form
          // submission, which does not fire reliably across browsers when the
          // form holds a single input.
          onKeyDown={(event) => event.key === 'Enter' && send(event)}
          placeholder="Ask a question…"
          aria-label="Your question"
          autoComplete="off"
          className="h-9 flex-1 rounded border border-rule-strong bg-paper px-3 text-sm text-ink outline-none transition-colors focus:border-accent"
        />
        <Button type="submit" size="sm" disabled={!draft.trim() || busy} aria-label="Send">
          <Send size={14} />
        </Button>
      </form>
    </div>
  )
}
