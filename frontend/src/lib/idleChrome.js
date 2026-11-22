import { onBeforeUnmount, ref, watch } from 'vue'

// The controls around a note, out of the way while it is written. They fade out as soon as you
// type, and come back when the pointer reaches for them: near them (the top of the page, where they
// sit), not at any move, so a nudge of the mouse while writing doesn't bring them back. While `idle`
// is on (zen mode) they also leave again once the pointer goes away from there. A touch (no pointer
// to reach with) or the Tab key brings them back too. Writing in the controls themselves (a search
// box) doesn't hide them, nor does resting the pointer on them, nor focus inside them: a keyboard
// user is never left with controls they can't see. The same pattern as Dabble's auto-hide toolbar,
// Ulysses' minimal mode and Novlr.
const NEAR_PX = 40
const LEAVE_MS = 400

export function useIdleChrome(active, chrome, idle = ref(false)) {
  const hidden = ref(false)
  let timer = null
  // Whether reaching near them counts: not right after zen mode hid them under the pointer that
  // turned it on, until that pointer has gone away from there once.
  let armed = true

  const inside = (target) => Boolean(chrome.value && target instanceof Node && chrome.value.contains(target))
  const busy = () => Boolean(chrome.value && (chrome.value.matches(':hover') || chrome.value.contains(document.activeElement)))
  // Within reach: down to a little under the controls' bottom edge.
  const near = (y) => Boolean(chrome.value && y <= chrome.value.getBoundingClientRect().bottom + NEAR_PX)

  function show() {
    clearTimeout(timer)
    timer = null
    hidden.value = false
  }

  function hide() {
    clearTimeout(timer)
    timer = null
    hidden.value = true
  }

  // In zen mode, the pointer gone from near them: they leave a moment later, unless in use.
  function leave() {
    if (hidden.value || timer) return
    timer = setTimeout(() => {
      timer = null
      if (active.value && idle.value && !busy()) hidden.value = true
    }, LEAVE_MS)
  }

  function onMove(event) {
    if (!active.value) return
    if (!near(event.clientY)) {
      armed = true
      if (idle.value) leave()
    } else if (armed) show()
  }

  function onTouch(event) {
    if (event.pointerType !== 'mouse') show()
  }

  function onKey(event) {
    if (!active.value) return
    if (event.key === 'Tab') return show()
    const typing = event.key.length === 1 || ['Backspace', 'Delete', 'Enter'].includes(event.key)
    if (typing && !event.ctrlKey && !event.metaKey && !event.altKey && !inside(event.target)) hide()
  }

  // Text arriving without a key (a phone's keyboard, a paste, dictation) is writing too.
  function onInput(event) {
    if (active.value && !inside(event.target)) hide()
  }

  window.addEventListener('mousemove', onMove, { passive: true })
  window.addEventListener('pointerdown', onTouch, { passive: true })
  window.addEventListener('keydown', onKey)
  window.addEventListener('input', onInput, true)
  onBeforeUnmount(() => {
    clearTimeout(timer)
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('pointerdown', onTouch)
    window.removeEventListener('keydown', onKey)
    window.removeEventListener('input', onInput, true)
  })

  // Entering zen mode hides them at once, with the rest of the app's chrome, even under the pointer
  // that just turned it on; reaching for them again brings them back. Leaving it brings them back.
  watch(idle, (on) => {
    armed = !on
    on ? hide() : show()
  })

  watch(active, show)

  return { hidden }
}
