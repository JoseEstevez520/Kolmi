import { ref } from 'vue'
import { isWaiting, profile, session } from './auth.js'
import { refreshCached } from './cached.js'
import { usePolling } from './polling.js'

// How many live notes are being written by someone else right now: the number on the Notes tab.
// The author needs no alert for their own session, so their notes (`mine`) don't count.
export const liveCount = ref(0)

export function setLiveCount(notes) {
  liveCount.value = notes.filter((n) => n.live && !n.mine).length
}

// Silent: a failed request leaves the count as it was.
export async function refreshLiveCount() {
  if (!session.value || !profile.value || isWaiting(profile.value)) return
  try {
    const answer = await refreshCached('live')
    if (answer) setLiveCount(answer.notes)
  } catch {
    /* keep the last count */
  }
}

// Called once from the app shell; polls while the tab is visible (usePolling). Someone not signed
// in, or still waiting to be let in, is skipped by `refreshLiveCount`.
export function useLiveCount() {
  usePolling(refreshLiveCount, 30000)
}
