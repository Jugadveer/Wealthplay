/**
 * A tiny data cache for the app.
 *
 * Why not just useEffect + fetch: the dashboard used to issue 44 requests on a
 * single mount. `/api/users/portfolio/` alone was requested six times because
 * four components each fetched it independently and StrictMode double-invoked
 * every effect. A context tried to fix this by caching to localStorage, but it
 * never invalidated, so a user could buy a stock and still see an empty
 * portfolio.
 *
 * What this does instead:
 *   - one in-flight request per key, shared by every caller (dedupe)
 *   - cached results served immediately, revalidated in the background (SWR)
 *   - mutations invalidate by key prefix, and any mounted query on an
 *     invalidated key refetches straight away
 *
 * Around 120 lines, no dependency, and it does exactly what this app needs.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

const cache = new Map() // key -> { data, at }
const inflight = new Map() // key -> Promise
const subscribers = new Map() // key -> Set<(opts) => void>

const DEFAULT_TTL = 30_000

function notify(key, { refetch = false } = {}) {
  subscribers.get(key)?.forEach((fn) => fn({ refetch }))
}

/**
 * Drop cached entries whose key starts with any given prefix.
 *
 * Mounted queries on those keys refetch immediately. Without that a mutation
 * would clear the cache and leave the component showing a skeleton forever,
 * because its effect has no reason to re-run.
 *
 * `invalidate('')` matches every key — used on sign-in and sign-out.
 */
export function invalidate(...prefixes) {
  for (const key of [...cache.keys(), ...subscribers.keys()]) {
    if (prefixes.some((prefix) => key.startsWith(prefix))) {
      cache.delete(key)
      notify(key, { refetch: true })
    }
  }
}

/** Seed the cache directly, for when a mutation already returned fresh state. */
export function setCached(key, data) {
  cache.set(key, { data, at: Date.now() })
  notify(key)
}

async function load(key, fetcher) {
  // A second caller while a request is open waits on the same promise rather
  // than starting another.
  if (inflight.has(key)) return inflight.get(key)

  const promise = fetcher()
    .then((data) => {
      cache.set(key, { data, at: Date.now() })
      return data
    })
    .finally(() => {
      inflight.delete(key)
      notify(key)
    })

  inflight.set(key, promise)
  return promise
}

/**
 * Subscribe a component to a cache key.
 *
 * @param {string|null} key  null disables the query, e.g. while signed out
 * @param {() => Promise<any>} fetcher
 * @param {object} [options]
 * @param {number} [options.ttl]  ms before cached data counts as stale
 * @returns {{data, error, loading, refetch}}
 */
export function useQuery(key, fetcher, { ttl = DEFAULT_TTL } = {}) {
  const [, rerender] = useState(0)
  const [error, setError] = useState(null)

  // Held in a ref so an inline fetcher does not retrigger the effect.
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const run = useCallback(
    async (force = false) => {
      if (!key) return

      const cached = cache.get(key)
      if (!force && cached && Date.now() - cached.at < ttl) return

      try {
        await load(key, fetcherRef.current)
        setError(null)
      } catch (err) {
        setError(err)
      }
    },
    [key, ttl],
  )

  useEffect(() => {
    if (!key) return undefined

    const onChange = ({ refetch } = {}) => {
      rerender((n) => n + 1)
      if (refetch) run(true)
    }

    if (!subscribers.has(key)) subscribers.set(key, new Set())
    subscribers.get(key).add(onChange)

    run()

    return () => {
      const set = subscribers.get(key)
      set?.delete(onChange)
      if (set && set.size === 0) subscribers.delete(key)
    }
  }, [key, run])

  const entry = key ? cache.get(key) : null

  return {
    data: entry?.data,
    error,
    // Stale data is still data: show it while the refresh happens rather than
    // flashing a skeleton the reader has already seen.
    loading: Boolean(key) && !entry && !error,
    refetch: () => run(true),
  }
}
