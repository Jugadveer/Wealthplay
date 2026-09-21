/**
 * Market headlines.
 *
 * Real stories from the quote provider, aggregated across the tracked universe
 * rather than pulled from one listing — a single symbol's feed goes quiet for
 * days and the wire showed the same four stories all week. Which listings lead
 * rotates daily, so the mix turns over on its own.
 *
 * Shared by the landing page and the signed-in home. When the provider has
 * nothing the block renders nothing, rather than an empty heading over a gap.
 */
import { useEffect, useState } from 'react'
import { ArrowUpRight } from 'lucide-react'

import { api } from '../lib/api'
import { cx } from '../ui'

export default function Wire({ limit = 5, heading = 'On the wire', className }) {
  const [stories, setStories] = useState([])

  useEffect(() => {
    let cancelled = false
    api
      .marketNews(limit)
      .then((data) => !cancelled && setStories(data.news || []))
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [limit])

  if (!stories.length) return null

  return (
    <section className={className}>
      <div className="flex items-baseline justify-between border-b border-rule pb-3">
        <h2 className="text-title">{heading}</h2>
        <p className="eyebrow">Live headlines</p>
      </div>

      <ul className="stagger mt-1 divide-y divide-rule">
        {stories.map((story, index) => (
          <li key={story.link || story.title} style={{ animationDelay: `${index * 70}ms` }}>
            <a
              href={story.link}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex flex-col gap-1 py-4"
            >
              <p className="flex items-start gap-1.5 text-sm font-medium text-ink transition-colors group-hover:text-accent">
                {story.title}
                <ArrowUpRight
                  size={13}
                  className="mt-0.5 shrink-0 text-ink-faint transition-colors group-hover:text-accent"
                />
              </p>
              {story.summary && (
                <p className={cx('measure line-clamp-2 text-xs leading-relaxed text-ink-muted')}>
                  {story.summary}
                </p>
              )}
              <p className="eyebrow mt-0.5">
                {story.symbol ? `${story.symbol} · ` : ''}
                {story.publisher || 'Wire'}
              </p>
            </a>
          </li>
        ))}
      </ul>
    </section>
  )
}
