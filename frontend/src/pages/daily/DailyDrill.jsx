/**
 * Daily Drill — spaced repetition over completed modules.
 *
 * Cards are scheduled per learner by SM-2, so the same question does not recur
 * two days running and the material a learner keeps missing comes back sooner.
 * The pool grows with every module finished, which is what keeps this from
 * exhausting the way a fixed question bank does.
 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Check, X } from 'lucide-react'

import { api } from '../../lib/api'
import { Button, EmptyState, Panel, Meter, cx } from '../../ui'

export default function DailyDrill({ onFinish }) {
  const [cards, setCards] = useState(null)
  const [emptyReason, setEmptyReason] = useState('')
  const [index, setIndex] = useState(0)
  const [result, setResult] = useState(null)
  const [chosen, setChosen] = useState(null)
  const [correctCount, setCorrectCount] = useState(0)

  useEffect(() => {
    api
      .drill()
      .then((data) => {
        setCards(data.cards)
        setEmptyReason(data.empty_reason || '')
      })
      .catch(() => setCards([]))
  }, [])

  if (cards === null) return <Panel className="h-64 animate-pulse" />

  if (!cards.length) {
    return (
      <Panel>
        <EmptyState
          title="Nothing to review yet"
          body={emptyReason || 'Finish a module and its questions start appearing here.'}
          action={<Button to="/learn">Browse courses</Button>}
        />
      </Panel>
    )
  }

  const card = cards[index]
  const done = index >= cards.length

  if (done) {
    return (
      <Panel className="p-6 text-center">
        <p className="eyebrow">Drill complete</p>
        <p className="num mt-2 text-display text-ink">
          {correctCount}/{cards.length}
        </p>
        <p className="mt-2 text-sm text-ink-muted">
          {correctCount === cards.length
            ? 'All correct. These move further out in your queue.'
            : 'The ones you missed come back sooner.'}
        </p>
        <Button className="mt-5" onClick={onFinish}>
          Back to today
        </Button>
      </Panel>
    )
  }

  async function choose(choice) {
    if (result) return
    setChosen(choice)
    const outcome = await api.answerDrill({ card_id: card.id, choice })
    setResult(outcome)
    if (outcome.correct) setCorrectCount((count) => count + 1)
  }

  function next() {
    setResult(null)
    setChosen(null)
    setIndex((current) => current + 1)
  }

  return (
    <Panel className="p-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="eyebrow">Puzzle four</p>
          <h2 className="mt-1 text-headline">Daily Drill</h2>
        </div>
        <span className="num text-sm text-ink-muted">
          {index + 1} / {cards.length}
        </span>
      </div>

      <Meter value={index} max={cards.length} className="mt-4" />

      <p className="measure mt-6 text-base leading-relaxed text-ink">{card.question}</p>

      <div className="mt-5 space-y-2">
        {card.options.map((option, optionIndex) => {
          const picked = optionIndex === chosen
          const isAnswer = result && optionIndex === result.correct_index
          const wrongPick = result && !result.correct && picked

          return (
            <button
              key={option}
              type="button"
              disabled={Boolean(result)}
              onClick={() => choose(optionIndex)}
              className={cx(
                'flex w-full items-start gap-3 rounded border px-4 py-3 text-left text-sm transition-colors',
                isAnswer
                  ? 'border-up bg-up/5 text-ink'
                  : wrongPick
                    ? 'border-down bg-down/5 text-ink'
                    : 'border-rule text-ink-muted',
                !result && 'hover:border-ink-faint hover:text-ink',
              )}
            >
              <span className="num mt-0.5 shrink-0 text-xs text-ink-faint">
                {String.fromCharCode(65 + optionIndex)}
              </span>
              <span className="flex-1">{option}</span>
              {isAnswer && <Check size={16} className="shrink-0 text-up" />}
              {wrongPick && <X size={16} className="shrink-0 text-down" />}
            </button>
          )
        })}
      </div>

      {result && (
        <div className="mt-5 border-t border-rule pt-4">
          {result.explanation && (
            <p className="measure text-sm leading-relaxed text-ink-muted">{result.explanation}</p>
          )}
          <div className="mt-4 flex items-center justify-between gap-4">
            <span className="text-xs text-ink-faint">
              Back in {result.next_review_in_days} day{result.next_review_in_days === 1 ? '' : 's'}
            </span>
            <Button size="sm" onClick={next}>
              {index + 1 === cards.length ? 'Finish' : 'Next'}
            </Button>
          </div>
        </div>
      )}
    </Panel>
  )
}
