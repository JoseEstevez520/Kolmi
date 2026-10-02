import { ref } from 'vue'
import { setMotionPreference } from 'elastic-ui'

// Whether the app animates even when the system asks for reduced motion (Settings). On by
// default, so the transitions that explain each change stay; turned off, the app follows the
// system setting. Kept in this browser and applied where the preference is read:
// setMotionPreference (the library's JS animations and `data-motion` on <html>, which
// tokens.css and the `motion-reduce:` variant check) and MotionConfig in App.vue (motion-v).
const KEY = 'kolmi.motion'

function saved() {
  try {
    // On unless it was turned off by hand ('auto' is stored then).
    return localStorage.getItem(KEY) !== 'auto'
  } catch {
    return true
  }
}

export const forceMotion = ref(saved())

setMotionPreference(forceMotion.value ? 'full' : 'auto')

export function setForceMotion(value) {
  forceMotion.value = value
  setMotionPreference(value ? 'full' : 'auto')
  try {
    localStorage.setItem(KEY, value ? 'full' : 'auto')
  } catch {
    // Blocked storage: the choice lasts until the tab closes.
  }
}
