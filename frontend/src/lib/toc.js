import { computed, ref } from 'vue'

// How many mounted pages show their table of contents. A count, not a yes or no: on a page
// change the new page can mount before the old one is gone.
const withToc = ref(0)

export const tocShown = computed(() => withToc.value > 0)

// Called by a page that shows one; returns what to call when it stops.
export function showToc() {
  withToc.value++
  return () => withToc.value--
}
