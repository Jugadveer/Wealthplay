/**
 * The notification bus.
 *
 * Anything in the app can announce something happened; one component renders
 * it. Kept as a module-level store rather than a context because notifications
 * are fired from event handlers and API callers, not from render, and a context
 * would force every caller to be inside the provider tree.
 */

let items = []
let nextId = 1
const listeners = new Set()

const TTL = { achievement: 7000, success: 4000, info: 4000, error: 6000 }

function emit() {
  for (const listener of listeners) listener(items)
}

export function subscribe(listener) {
  listeners.add(listener)
  listener(items)
  return () => listeners.delete(listener)
}

export function dismiss(id) {
  items = items.filter((item) => item.id !== id)
  emit()
}

/**
 * Show a notification. `tone` picks the treatment: achievements get the
 * celebratory card, everything else gets a line of text.
 */
export function notify({ tone = 'info', title, body, icon }) {
  const id = nextId++
  items = [...items, { id, tone, title, body, icon }]
  emit()

  setTimeout(() => dismiss(id), TTL[tone] ?? TTL.info)
  return id
}

export const notifySuccess = (title, body) => notify({ tone: 'success', title, body })
export const notifyError = (title, body) => notify({ tone: 'error', title, body })

/**
 * Announce achievements returned by a mutation.
 *
 * Every endpoint that can unlock one returns `newly_unlocked_achievements`, so
 * callers hand the whole response here and forget about it.
 */
export function announceUnlocks(response) {
  const unlocked = response?.newly_unlocked_achievements ?? []

  unlocked.forEach((achievement, index) => {
    // Staggered so two unlocks at once read as two events, not one blur.
    setTimeout(() => {
      notify({
        tone: 'achievement',
        title: achievement.name,
        body: achievement.xp_reward ? `+${achievement.xp_reward} XP` : 'Unlocked',
      })
    }, index * 700)
  })

  return unlocked.length
}
