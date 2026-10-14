import { onBeforeUnmount, ref, watch } from 'vue'

// The controls around a note, out of the way while it is written. They fade out as soon as you type
// (always) or, while `idle` is on (zen mode), also when the pointer rests, and come back with the
// next pointer move, a touch or the Tab key. Writing in the controls themselves (a search box) doesn't hide them, nor
// does resting the pointer on them, nor does focus inside them: a keyboard user is never left with
// controls they can't see. The same pattern as Ulysses' minimal mode, Novlr and FocusWriter.
const IDLE_MS = 2500
const MOVE_PX = 4

export function useIdleChrome(active, chrome, idle = ref(false)) {
  const hidden = ref(false)
  let timer = null
  let last = null

  const inside = (target) => Boolean(chrome.value && target instanceof Node && chrome.value.contains(target))
  const busy = () => Boolean(chrome.value && (chrome.value.matches(':hover') || chrome.value.contains(document.activeElement)))

  function show() {
    hidden.value = false
    arm()
  }

  function arm() {
    clearTimeout(timer)
    if (!active.value || !idle.value) return
    timer = setTimeout(() => {
      if (active.value && !busy()) hidden.value = true
      else arm()
    }, IDLE_MS)
  }

  function hide() {
    clearTimeout(timer)
    hidden.value = true
  }

  function onMove(event) {
    // A move this small is the hand resting, not the person reaching for a control.
    if (last && Math.hypot(event.clientX - last.x, event.clientY - last.y) < MOVE_PX) return
    last = { x: event.clientX, y: event.clientY }
    show()
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
  window.addEventListener('pointerdown', show, { passive: true })
  window.addEventListener('keydown', onKey)
  window.addEventListener('input', onInput, true)
  onBeforeUnmount(() => {
    clearTimeout(timer)
    window.removeEventListener('mousemove', onMove)
    window.removeEventListener('pointerdown', show)
    window.removeEventListener('keydown', onKey)
    window.removeEventListener('input', onInput, true)
  })

  // Leaving zen mode stops the resting timer, and brings the controls back.
  watch(idle, (on) => (on ? show() : (clearTimeout(timer), (hidden.value = false))))

  watch(active, (on) => {
    if (on) show()
    else {
      clearTimeout(timer)
      hidden.value = false
    }
  })

  return { hidden }
}
