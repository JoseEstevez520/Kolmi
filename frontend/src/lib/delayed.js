import { onBeforeUnmount, ref } from 'vue'

// True once the component has lived `ms` milliseconds. A skeleton uses it so a fast answer never
// flashes one: under about 300 ms the region stays empty, past that the shape appears.
export function useAfter(ms = 300) {
  const passed = ref(ms <= 0)
  if (!passed.value) {
    const timer = setTimeout(() => (passed.value = true), ms)
    onBeforeUnmount(() => clearTimeout(timer))
  }
  return passed
}
