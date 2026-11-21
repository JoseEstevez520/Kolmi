import { onBeforeUnmount, onMounted } from 'vue'

// Runs `steps` ([ms, fn]) from the start, then again after `restMs`, for as long as the part lives.
export function useLoop(steps, total) {
  let timers = []
  function play() {
    timers.forEach(clearTimeout)
    timers = steps.map(([ms, fn]) => setTimeout(fn, ms))
    timers.push(setTimeout(play, total))
  }
  onMounted(play)
  onBeforeUnmount(() => timers.forEach(clearTimeout))
}
