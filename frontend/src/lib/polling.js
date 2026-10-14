import { onBeforeUnmount, onMounted } from 'vue'

// Runs `fn` now and then every `ms` while the tab is visible. A hidden tab stops asking; coming
// back runs it at once, so what changed meanwhile shows without waiting a full beat. One call at
// a time: a slow answer is never overlapped by the next beat.
export function usePolling(fn, ms) {
  let timer = null
  let running = false

  async function beat() {
    if (running) return
    running = true
    try {
      await fn()
    } finally {
      running = false
    }
  }

  function start() {
    stop()
    beat()
    timer = setInterval(beat, ms)
  }

  function stop() {
    clearInterval(timer)
    timer = null
  }

  function onVisibility() {
    if (document.visibilityState === 'hidden') stop()
    else start()
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisibility)
    if (document.visibilityState !== 'hidden') start()
  })
  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', onVisibility)
    stop()
  })

  return { refresh: beat }
}
