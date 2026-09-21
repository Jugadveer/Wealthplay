/**
 * Nex, the mentor.
 *
 * One component for the whole app. There used to be two — a floating one and a
 * lesson one — with separate prompts, separate histories and separate
 * greetings, one of which called the mentor "Next".
 *
 * On a lesson route it picks up the course and module from the URL and the
 * answers are grounded in that module. Everywhere else it sends the section
 * name, which widens the search without restricting it.
 *
 * Two things are shown that were not before, and both are about trust rather
 * than decoration. Where an answer came from — the glossary, a named module, or
 * the model writing from retrieved passages — is printed under it, because the
 * three are not equally reliable and the reader deserves to know which they
 * have. And the model runs on this machine, which is worth saying to somebody
 * about to type their income into a chat box.
 */
import { useEffect, useRef, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { BookOpen, Cpu, HelpCircle, MessageSquare, Send, X } from 'lucide-react'

import { api } from '../lib/api'
import { Button, cx } from '../ui'

/** Read `/learn/:courseId/:moduleId` out of the current path. */
function lessonContext(pathname) {
  const match = pathname.match(/^\/learn\/([^/]+)\/([^/]+)/)
  return match ? { course_id: match[1], module_id: match[2] } : {}
}

/** The section of the app, which the backend uses to bias its search. */
function zoneOf(pathname) {
  const root = pathname.split('/')[1] || ''
  return ['today', 'learn', 'markets', 'play', 'goals', 'progress'].includes(root) ? root : ''
}

const OPENERS = {
  markets: ['What is a P/E ratio?', 'How much of one stock is too much?', 'What is a stop loss?'],
  goals: ['What is a SIP?', 'How big should an emergency fund be?', 'What is an EMI?'],
  play: ['Why do I panic sell?', 'What is loss aversion?', 'What is recency bias?'],
  progress: ['What is compounding?', 'How do I read my accuracy?', 'What is calibration?'],
  today: ['What is an index fund?', 'What is inflation?', 'Explain SIP vs lump sum'],
  learn: ['Explain this simply', 'Give me an example', 'Why does this matter?'],
}

const LESSON_OPENERS = ['Explain this simply', 'Give me an example', 'Why does this matter?']

export default function Mentor() {
  const { pathname } = useLocation()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState(null)
  const endRef = useRef(null)

  const context = lessonContext(pathname)
  const zone = zoneOf(pathname)
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
    if (!open || status) return
    api.aiStatus().then(setStatus).catch(() => {})
  }, [open, status])

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
      const answer = await api.askMentor({ question, zone, ...context })
      setMessages((current) => [
        ...current,
        {
          role: 'assistant',
          text: answer.reply,
          degraded: !answer.available,
          source: answer.source,
          sources: answer.sources || [],
        },
      ])
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

  const prompts = scoped ? LESSON_OPENERS : OPENERS[zone] || OPENERS.today

  return (
    <div className="fixed bottom-5 right-5 z-40 flex h-[520px] w-[min(380px,calc(100vw-2.5rem))] flex-col rounded-lg border border-rule bg-paper-raised shadow-float rise">
      <header className="flex items-center justify-between border-b border-rule px-4 py-3">
        <div>
          <p className="font-display text-base leading-none text-ink">Nex</p>
          <p className="mt-1 flex items-center gap-1 text-[11px] text-ink-faint">
            {scoped ? (
              'Answering from this lesson'
            ) : status?.local ? (
              <>
                <Cpu size={10} />
                Running on your machine
              </>
            ) : (
              'Ask about money or markets'
            )}
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
              {prompts.map((prompt) => (
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
          <Message key={index} message={message} onClose={() => setOpen(false)} />
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

function Message({ message, onClose }) {
  const mine = message.role === 'user'

  return (
    <div className={cx('flex flex-col', mine ? 'items-end' : 'items-start')}>
      <p
        className={cx(
          'max-w-[85%] whitespace-pre-wrap rounded px-3 py-2 text-sm leading-relaxed',
          mine
            ? 'bg-accent text-accent-on'
            : message.degraded
              ? 'border border-rule bg-paper-sunken text-ink-muted'
              : 'bg-paper-sunken text-ink',
        )}
      >
        {message.text}
      </p>

      {!mine && !message.degraded && <Provenance message={message} onClose={onClose} />}
    </div>
  )
}

/**
 * Where the answer came from.
 *
 * An answer taken from the glossary or quoted from a module is a different
 * thing from one the model wrote, and only the reader can decide how much that
 * matters to them. Linking the module also turns a question into a way back
 * into the course, which is where the answer is explained properly.
 */
function Provenance({ message, onClose }) {
  const sources = message.sources || []

  if (message.source === 'glossary') {
    return (
      <span className="mt-1 flex items-center gap-1 pl-1 text-[10px] text-ink-faint">
        <BookOpen size={9} />
        Definition from the glossary
      </span>
    )
  }

  if (message.source === 'lesson' || sources.length > 0) {
    return (
      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 pl-1">
        <span className="flex items-center gap-1 text-[10px] text-ink-faint">
          <BookOpen size={9} />
          From the course
        </span>
        {sources.slice(0, 2).map((source, index) => (
          <Link
            key={index}
            to={`/learn/${source.course_id}/${source.module_id}`}
            onClick={onClose}
            className="text-[10px] text-accent underline-offset-2 hover:underline"
          >
            {source.where || source.title}
          </Link>
        ))}
      </div>
    )
  }

  return (
    <span className="mt-1 flex items-center gap-1 pl-1 text-[10px] text-ink-faint">
      <HelpCircle size={9} />
      Written from the course notes — check the module if it matters
    </span>
  )
}
