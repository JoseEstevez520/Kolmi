import { ref } from 'vue'
import { setMotionPreference } from 'elastic-ui'

// Animations on or off (Settings), whatever the computer's own setting says. On by default, so
// the transitions that explain each change stay. Kept in this browser and handed to elastic-ui,
// whose parts, CSS and `motion-reduce:` variant follow it; App.vue's MotionConfig too.
const KEY = 'kolmi.motion'

function saved() {
  try {
    // On unless it was turned off by hand ('none' is stored then; 'auto', from before, is on).
    return localStorage.getItem(KEY) !== 'none'
  } catch {
    return true
  }
}

export const motionOn = ref(saved())

setMotionPreference(motionOn.value ? 'full' : 'none')

export function setMotionOn(value) {
  motionOn.value = value
  setMotionPreference(value ? 'full' : 'none')
  try {
    localStorage.setItem(KEY, value ? 'full' : 'none')
  } catch {
    // Blocked storage: the choice lasts until the tab closes.
  }
}
