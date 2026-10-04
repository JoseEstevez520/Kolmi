import { ref } from 'vue'

// Whether the guided tour has already run, kept in this browser (as the language or the
// animation setting are): a new one starts it once, from Settings it can be asked for again.
const KEY = 'kolmi.tour.seen'

function seen() {
  try {
    return localStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

function markSeen() {
  try {
    localStorage.setItem(KEY, '1')
  } catch {
    // Private mode or blocked storage: it may show again next time, which is harmless.
  }
}

export const tourOpen = ref(false)

/** Called once the home page has something to show; does nothing if already seen. */
export function offerTour() {
  if (!seen()) tourOpen.value = true
}

/** Settings' "Show it again": clears the flag and starts it at once. */
export function replayTour() {
  tourOpen.value = true
}

/** The tour finished or was skipped either way: it does not show again on its own. */
export function closeTour() {
  tourOpen.value = false
  markSeen()
}
