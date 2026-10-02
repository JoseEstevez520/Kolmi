import { onScopeDispose, ref, watch } from 'vue'

// A loading flag that only turns on once the wait is long enough to notice. An answer that
// comes quickly shows no "Loading…" at all, instead of a flash of it.
export function useDelayed(source, delay = 300) {
  const shown = ref(false)
  let timer = null

  watch(
    source,
    (on) => {
      clearTimeout(timer)
      if (!on) shown.value = false
      else timer = setTimeout(() => (shown.value = true), delay)
    },
    { immediate: true },
  )
  onScopeDispose(() => clearTimeout(timer))

  return shown
}
