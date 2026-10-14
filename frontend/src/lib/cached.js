import { computed, ref, watch } from 'vue'
import { api } from './api.js'
import { isWaiting, profile, ready, session } from './auth.js'

// Stale-while-revalidate for the list screens. The last answer per key is kept in memory (so
// leaving a screen and coming back finds it) and in sessionStorage (so a reload does too, a new
// tab starts clean). A screen with an answer to show draws it at once and the request that
// refreshes it runs silently; only a screen with nothing yet has a "loading" state.
// The answers are kept per signed-in person and dropped on sign-out or another sign-in.

const PREFIX = 'kolmi.cache.'

// What the app warms in the background (`prefetch`), by key.
const sources = {
  notes: () => api.myNotes(),
  live: () => api.liveNotes(),
  schedule: async () => {
    const [settings, events] = await Promise.all([api.settings(), api.scheduleEvents()])
    return { settings, events }
  },
  // An admin's lists. Never warmed in the background (prefetch below): only the screen asks.
  adminUsers: () => api.users(),
  adminReports: async () => {
    const list = await api.adminBugReports()
    return Array.isArray(list) ? list : []
  },
}

// What the app warms by itself: what everyone opens.
const WARM = ['notes', 'live', 'schedule']

const entries = new Map()
let owner = null

// Storage can be blocked or full: the cache works the same without it.
function readStored(key) {
  try {
    const stored = JSON.parse(sessionStorage.getItem(PREFIX + key))
    return stored && stored.owner === owner ? stored.data : null
  } catch {
    return null
  }
}

function writeStored(key, data) {
  try {
    sessionStorage.setItem(PREFIX + key, JSON.stringify({ owner, data }))
  } catch {
    // ignore
  }
}

function entry(key) {
  let found = entries.get(key)
  if (!found) {
    found = { data: ref(readStored(key)), error: ref(''), flight: null, again: false }
    entries.set(key, found)
  }
  return found
}

function put(key, data) {
  const e = entry(key)
  e.data.value = data
  e.error.value = ''
  writeStored(key, data)
}

// Fetches `key` now. One request per key at a time; a request asked for while one is running
// shares it, unless it is `fresh` (after a change of the person's own), which runs once more as
// soon as the running one ends so the answer is never older than the change. Never throws.
function run(key, fetcher, fresh = false) {
  const e = entry(key)
  if (e.flight) {
    if (fresh) e.again = true
    return e.flight
  }
  const who = owner
  e.flight = (async () => {
    try {
      const data = await fetcher()
      if (who === owner) put(key, data)
    } catch (err) {
      if (who === owner) e.error.value = err?.message || ' '
    } finally {
      e.flight = null
    }
    if (e.again) {
      e.again = false
      await run(key, fetcher)
    }
    return e.data.value
  })()
  return e.flight
}

// The screen's side: `data` is the cached answer or null, `loading` is true only while there is
// none, and `error` shows only when there is nothing to show. `refresh` fetches again quietly.
export function useCached(key, fetcher = sources[key]) {
  const e = entry(key)
  const loading = computed(() => e.data.value === null && !e.error.value)
  const error = computed(() => (e.data.value === null ? e.error.value : ''))
  const refresh = () => run(key, fetcher)
  return { data: e.data, loading, error, refresh }
}

// The person changed something this list shows: fetch it again now. The old answer stays on
// screen until the new one lands.
export function invalidate(key) {
  return run(key, sources[key], true)
}

// Fetch `key` now through the shared request and give back what is cached for it.
export function refreshCached(key) {
  return run(key, sources[key])
}

// Warm the lists after a short idle moment, so a first visit is instant too. Silent.
export function prefetch(keys = WARM) {
  const go = () => keys.forEach((key) => run(key, sources[key]))
  if (typeof requestIdleCallback === 'function') requestIdleCallback(go, { timeout: 3000 })
  else setTimeout(go, 1500)
}

// Whoever is signed in owns the cache: another person, or nobody, starts empty.
watch(
  () => (ready.value ? (session.value?.user?.id ?? null) : undefined),
  (id) => {
    if (id === undefined || id === owner) return
    owner = id
    for (const [key, e] of entries) {
      e.data.value = readStored(key)
      e.error.value = ''
      e.again = false
    }
    if (id === null) {
      try {
        Object.keys(sessionStorage)
          .filter((k) => k.startsWith(PREFIX))
          .forEach((k) => sessionStorage.removeItem(k))
      } catch {
        // ignore
      }
    }
  },
  { immediate: true },
)

// Once the person is let in, warm the lists (called from the app shell).
export function usePrefetch() {
  watch(
    () => Boolean(session.value && profile.value && !isWaiting(profile.value)),
    (letIn) => letIn && prefetch(),
    { immediate: true },
  )
}
