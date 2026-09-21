/**
 * The small slice of Markdown that lesson content actually uses.
 *
 * Course theory is written with **bold** emphasis and the odd `code` span. It
 * used to be rendered as plain text, so learners read literal asterisks around
 * words like "Inflation".
 *
 * Deliberately not a Markdown library: the content is authored in-repo and uses
 * four constructs. Parsing only those keeps the surface small and means no
 * arbitrary HTML is ever produced — the output is React elements, never
 * dangerouslySetInnerHTML.
 */
import { cx } from './index'

// Order matters: bold before italic, so ** is not eaten as two singles.
const TOKEN = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g

function inline(text) {
  return text.split(TOKEN).map((chunk, index) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      return (
        <strong key={index} className="font-semibold text-ink">
          {chunk.slice(2, -2)}
        </strong>
      )
    }
    if (chunk.startsWith('`') && chunk.endsWith('`')) {
      return (
        <code key={index} className="num rounded-sm bg-paper-sunken px-1 py-0.5 text-[0.9em]">
          {chunk.slice(1, -1)}
        </code>
      )
    }
    if (chunk.startsWith('*') && chunk.endsWith('*') && chunk.length > 2) {
      return <em key={index}>{chunk.slice(1, -1)}</em>
    }
    return chunk
  })
}

/** Render text with inline emphasis, split into paragraphs on blank lines. */
export function Markdown({ text, className }) {
  if (!text) return null

  const paragraphs = text.split(/\n\s*\n/).filter(Boolean)

  return (
    <div className={cx('measure space-y-3 text-ink-muted', className)}>
      {paragraphs.map((paragraph, index) => (
        <p key={index} className="leading-relaxed">
          {inline(paragraph.trim())}
        </p>
      ))}
    </div>
  )
}

export default Markdown
