import { ref } from 'vue'

// Zen mode: only the note on screen. The app hides its sidebar and header while it is on.
export const zen = ref(false)

export function exitZen() {
  zen.value = false
}

export function toggleZen() {
  zen.value = !zen.value
}
