import { ref } from 'vue'
import { setDiagramInk } from 'elastic-ui'

// Diagrams by hand (Settings): a Figure's chips, areas and arrows drawn in ink, wherever they show
// (notes, the chat, the pages). Off by default, kept in this browser like the animations, and
// handed to elastic-ui, whose Diagram draws them with Rough.js.
const KEY = 'kolmi.ink'

function saved() {
  try {
    return localStorage.getItem(KEY) === 'on'
  } catch {
    return false
  }
}

export const inkOn = ref(saved())

setDiagramInk(inkOn.value)

export function setInkOn(value) {
  inkOn.value = value
  setDiagramInk(value)
  try {
    if (value) localStorage.setItem(KEY, 'on')
    else localStorage.removeItem(KEY)
  } catch {
    // Blocked storage: the choice lasts until the tab closes.
  }
}
