/**
 * A module: read it, recall it, answer it, finish it.
 *
 * Three things this fixes from the old lesson page:
 *
 * 1. Flashcards are two-sided. They previously rendered the answer face-up
 *    under the heading "EXPERT ANSWER", showing text identical to the theory
 *    block directly above — nothing to recall.
 * 2. Theory renders its Markdown, so `**Inflation**` is bold rather than
 *    literal asterisks.
 * 3. The page ends in a completion step. It used to stop at the FAQ with no
 *    button, no XP, and no way to the next module.
 */
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowRight, Check, RotateCcw, X } from 'lucide-react'

import { api } from '../lib/api'
import { announceUnlocks } from '../lib/notify'
import { invalidate, useQuery } from '../lib/query'
import { Badge, Button, Meter, Panel, Skeleton, cx } from '../ui'
import Markdown from '../ui/Markdown'

export default function Lesson() {
  const { courseId, moduleId } = useParams()
  const key = `module:${courseId}:${moduleId}`
  const { data, loading } = useQuery(key, () => api.module(courseId, moduleId), { ttl: 60_000 })

  const [reviewed, setReviewed] = useState(() => new Set())
  const [answers, setAnswers] = useState({})

  if (loading && !data) return <LessonSkeleton />
  if (!data) return null

  const answeredCount = Object.values(answers).filter((a) => a.correct).length
  const progress = reviewed.size + answeredCount
  const total = data.cards.length + data.questions.length

  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <nav className="flex items-center gap-2 text-xs text-ink-faint">
        <Link to="/learn" className="hover:text-ink">
          Courses
        </Link>
        <span>/</span>
        <Link to={`/learn/${courseId}`} className="hover:text-ink">
          {data.course.title}
        </Link>
      </nav>

      <header className="mt-5 border-t border-rule pt-5">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <h1 className="text-headline">{data.title}</h1>
          <span className="num text-xs text-ink-faint">
            {data.estimated_minutes} min · {data.xp_reward} XP
          </span>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <Meter value={progress} max={total} className="max-w-xs" />
          <span className="num text-xs text-ink-muted">
            {progress}/{total}
          </span>
        </div>
      </header>

      <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,1fr)_260px]">
        <div className="min-w-0 space-y-12">
          <Theory text={data.theory} />

          {data.cards.length > 0 && (
            <Recall
              cards={data.cards}
              reviewed={reviewed}
              onReview={(id) => setReviewed((current) => new Set(current).add(id))}
            />
          )}

          {data.questions.length > 0 && (
            <Questions
              questions={data.questions}
              answers={answers}
              onAnswer={async (questionId, choice) => {
                const result = await api.answerQuestion({
                  course_id: courseId,
                  module_id: moduleId,
                  question_id: questionId,
                  choice,
                })
                setAnswers((current) => ({ ...current, [questionId]: { ...result, choice } }))
                if (result.xp_awarded) invalidate('profile')
              }}
            />
          )}

          {data.qna.length > 0 && <CommonQuestions items={data.qna} />}

          <Finish module={data} courseId={courseId} moduleId={moduleId} cacheKey={key} />
        </div>

        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Panel className="p-4">
            <p className="eyebrow">In this module</p>
            <ul className="mt-3 space-y-2 text-sm text-ink-muted">
              <li>{data.cards.length} recall cards</li>
              <li>{data.questions.length} questions</li>
              <li>{data.qna.length} common questions</li>
            </ul>
          </Panel>

          <Panel className="p-4">
            <p className="eyebrow">Stuck?</p>
            <p className="mt-2 text-sm text-ink-muted">
              Open Nex, bottom right. It answers from this module.
            </p>
          </Panel>
        </aside>
      </div>
    </div>
  )
}

function Theory({ text }) {
  return (
    <section>
      <h2 className="eyebrow">The idea</h2>
      <Markdown text={text} className="mt-3 text-[15px]" />
    </section>
  )
}

/**
 * Two-sided recall cards with a self-rating.
 *
 * The rating is what makes this recall rather than reading: you commit to
 * knowing it before the answer appears, then say whether you did.
 */
function Recall({ cards, reviewed, onReview }) {
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)

  const card = cards[index]
  const isLast = index === cards.length - 1

  function rate(knewIt) {
    onReview(card.id)
    setFlipped(false)
    if (!isLast) setIndex(index + 1)
    // Cards rated "not yet" go to the back of the stack for another pass.
    else if (!knewIt) setIndex(0)
  }

  return (
    <section>
      <div className="flex items-baseline justify-between">
        <h2 className="eyebrow">Recall</h2>
        <span className="num text-xs text-ink-faint">
          {index + 1} / {cards.length}
        </span>
      </div>

      <Panel className="mt-3 p-6">
        <p className="eyebrow">{card.term}</p>
        <p className="measure mt-2 font-display text-title text-ink">{card.prompt}</p>

        {flipped ? (
          <>
            <div className="mt-5 border-t border-rule pt-5">
              <Markdown text={card.answer} className="text-[15px]" />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <Button size="sm" variant="secondary" onClick={() => rate(false)}>
                <RotateCcw size={13} />
                Not yet
              </Button>
              <Button size="sm" onClick={() => rate(true)}>
                <Check size={13} />
                Knew it
              </Button>
            </div>
          </>
        ) : (
          <div className="mt-5 flex items-center gap-3">
            <Button size="sm" variant="secondary" onClick={() => setFlipped(true)}>
              Show the answer
            </Button>
            <span className="text-xs text-ink-faint">Try to answer it first.</span>
          </div>
        )}
      </Panel>

      <div className="mt-3 flex gap-1.5">
        {cards.map((item, position) => (
          <button
            key={item.id}
            type="button"
            onClick={() => {
              setIndex(position)
              setFlipped(false)
            }}
            aria-label={`Card ${position + 1}`}
            className={cx(
              'h-1 flex-1 rounded-sm transition-colors',
              reviewed.has(item.id)
                ? 'bg-up'
                : position === index
                  ? 'bg-accent'
                  : 'bg-paper-sunken',
            )}
          />
        ))}
      </div>
    </section>
  )
}

function Questions({ questions, answers, onAnswer }) {
  return (
    <section>
      <h2 className="eyebrow">Check yourself</h2>

      <div className="mt-3 space-y-4">
        {questions.map((question) => (
          <Question
            key={question.id}
            question={question}
            answer={answers[question.id]}
            onAnswer={(choice) => onAnswer(question.id, choice)}
          />
        ))}
      </div>
    </section>
  )
}

function Question({ question, answer, onAnswer }) {
  return (
    <Panel className="p-5">
      <p className="measure text-[15px] text-ink">{question.question}</p>

      <div className="mt-4 space-y-2">
        {question.options.map((option, index) => {
          const isAnswer = answer && index === answer.correct_index
          const wrongPick = answer && !answer.correct && index === answer.choice

          return (
            <button
              key={option}
              type="button"
              disabled={Boolean(answer)}
              onClick={() => onAnswer(index)}
              className={cx(
                'flex w-full items-start gap-3 rounded border px-3.5 py-2.5 text-left text-sm transition-colors',
                isAnswer
                  ? 'border-up bg-up/5 text-ink'
                  : wrongPick
                    ? 'border-down bg-down/5 text-ink'
                    : 'border-rule text-ink-muted',
                !answer && 'hover:border-ink-faint hover:text-ink',
              )}
            >
              <span className="num mt-0.5 shrink-0 text-xs text-ink-faint">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="flex-1">{option}</span>
              {isAnswer && <Check size={15} className="shrink-0 text-up" />}
              {wrongPick && <X size={15} className="shrink-0 text-down" />}
            </button>
          )
        })}
      </div>

      {answer?.explanation && (
        <p className="measure mt-4 border-t border-rule pt-3 text-sm leading-relaxed text-ink-muted">
          {answer.explanation}
        </p>
      )}
      {answer?.xp_awarded > 0 && (
        <Badge tone="play" className="mt-3">
          +{answer.xp_awarded} XP
        </Badge>
      )}
    </Panel>
  )
}

function CommonQuestions({ items }) {
  return (
    <section>
      <h2 className="eyebrow">Common questions</h2>
      <dl className="mt-3 divide-y divide-rule border-y border-rule">
        {items.map((item) => (
          <div key={item.question} className="py-4">
            <dt className="text-sm font-medium text-ink">{item.question}</dt>
            <dd className="measure mt-1.5 text-sm leading-relaxed text-ink-muted">{item.answer}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

/** The completion step. The lesson used to have no ending at all. */
function Finish({ module, courseId, moduleId, cacheKey }) {
  const navigate = useNavigate()
  const [state, setState] = useState(module.status === 'completed' ? 'done' : 'idle')
  const [unlocked, setUnlocked] = useState([])

  async function complete() {
    setState('saving')
    const result = await api.completeModule({ course_id: courseId, module_id: moduleId })
    setUnlocked(result.newly_unlocked_achievements || [])
    announceUnlocks(result)
    setState('done')
    invalidate('profile', 'courses', 'course:', 'daily:', cacheKey)
  }

  return (
    <section className="border-t border-rule pt-6">
      {state === 'done' ? (
        <>
          <div className="flex items-center gap-2 text-up">
            <Check size={18} />
            <p className="font-display text-title">Module complete</p>
          </div>
          <p className="measure mt-2 text-sm text-ink-muted">
            These questions now join your daily drill. They will come back in a day, then four,
            then further out each time you get them right.
          </p>

          {unlocked.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {unlocked.map((achievement) => (
                <Badge key={achievement.id} tone="play">
                  {achievement.name} · +{achievement.xp_reward} XP
                </Badge>
              ))}
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-3">
            {module.next ? (
              <Button onClick={() => navigate(`/learn/${courseId}/${module.next.id}`)}>
                Next: {module.next.title}
                <ArrowRight size={15} />
              </Button>
            ) : (
              <Button to={`/learn/${courseId}`}>Back to the course</Button>
            )}
            <Button variant="ghost" to="/today">
              Today&rsquo;s set
            </Button>
          </div>
        </>
      ) : (
        <>
          <h2 className="text-title">Done with this one?</h2>
          <p className="measure mt-2 text-sm text-ink-muted">
            Marking it complete awards {module.xp_reward} XP and adds its questions to your
            spaced-repetition queue.
          </p>
          <Button className="mt-4" size="lg" disabled={state === 'saving'} onClick={complete}>
            {state === 'saving' ? 'Saving…' : 'Mark complete'}
          </Button>
        </>
      )}
    </section>
  )
}

function LessonSkeleton() {
  return (
    <div className="mx-auto max-w-page px-4 py-8">
      <Skeleton className="h-4 w-48" />
      <Skeleton className="mt-5 h-10 w-96" />
      <Skeleton className="mt-8 h-40" />
      <Skeleton className="mt-8 h-48" />
    </div>
  )
}
