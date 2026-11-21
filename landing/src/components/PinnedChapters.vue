<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import MomentSection from './MomentSection.vue'

// After the hero, the chapters (Jose, 2026-11-21: the pinned stage driven by script was "muy
// confuso"; he wants it "más satisfactorio y sencillo"). The scroll stays the browser's own, so keys,
// trackpads and scrolling up behave as everywhere else; each chapter fills one screen, and when the
// scroll comes to rest near the chapters, the page finishes the move by itself and settles on the
// chapter it was heading to, up or down. (CSS scroll-snap was tried: `mandatory` sent a small turn
// of the wheel back to where it started.) Each chapter's animation plays by itself when it
// arrives (MomentSection). Dots on the side show where you are and take you to a chapter; they show
// only while the chapters are on screen.
defineProps({
  // [{ id, title, layout }], one slot per id with the chapter's picture
  chapters: { type: Array, required: true },
})

const root = ref(null)
const active = ref(0)

// ---- Settling on a chapter when the scroll rests ----
const SETTLE_MS = 140 // the scroll counts as at rest after this long without moving
let lastY = 0
let direction = 0
let settling = false
let restTimer = 0
function onScroll() {
  const y = scrollY
  if (y !== lastY) direction = Math.sign(y - lastY)
  lastY = y
  clearTimeout(restTimer)
  restTimer = setTimeout(settle, SETTLE_MS)
}
function settle() {
  if (settling) {
    settling = false
    return
  }
  const chapters = [...root.value.querySelectorAll('[data-chapter]')]
  const mid = innerHeight / 2
  // Only between the middle of the first chapter's screen and the last one's: the hero and the
  // footer scroll freely.
  const first = chapters[0].getBoundingClientRect()
  const last = chapters.at(-1).getBoundingClientRect()
  if (first.top > mid || last.bottom < mid) return
  // Leaving the chapters: going up past the first one's centre, or down past the last one's, the
  // page is let go towards the hero or the footer.
  if (direction < 0 && first.top + first.height / 2 > mid) return
  if (direction > 0 && last.top + last.height / 2 < mid) return
  // The chapter whose centre is nearest the screen's, nudged towards the way the scroll was going.
  let best = 0
  let bestGap = Infinity
  chapters.forEach((el, i) => {
    const r = el.getBoundingClientRect()
    const gap = r.top + r.height / 2 - mid
    const score = Math.abs(gap) - (Math.sign(gap) === direction ? innerHeight * 0.25 : 0)
    if (score < bestGap) (bestGap = score), (best = i)
  })
  const r = chapters[best].getBoundingClientRect()
  const target = scrollY + r.top + r.height / 2 - mid
  if (Math.abs(target - scrollY) < 2) return
  settling = true
  scrollTo({ top: target, behavior: 'smooth' })
}
const inView = ref(false)
let watchChapters = null
let watchRegion = null

onMounted(() => {
  lastY = scrollY
  addEventListener('scroll', onScroll, { passive: true })
  const sections = [...root.value.querySelectorAll('[data-chapter]')]
  watchChapters = new IntersectionObserver(
    (entries) => {
      for (const e of entries) if (e.isIntersecting) active.value = Number(e.target.dataset.chapter)
    },
    { rootMargin: '-45% 0px -45% 0px' },
  )
  sections.forEach((s) => watchChapters.observe(s))
  watchRegion = new IntersectionObserver(([e]) => (inView.value = e.isIntersecting), { rootMargin: '-40% 0px -40% 0px' })
  watchRegion.observe(root.value)
})
onBeforeUnmount(() => {
  removeEventListener('scroll', onScroll)
  clearTimeout(restTimer)
  watchChapters?.disconnect()
  watchRegion?.disconnect()
})

function go(i) {
  root.value.querySelector(`[data-chapter="${i}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <div ref="root">
    <div v-for="(c, i) in chapters" :key="c.id" :data-chapter="i" class="chapter">
      <MomentSection :id="c.id" class="w-full" :title="c.title" :layout="c.layout">
        <slot :name="c.id" />
      </MomentSection>
    </div>

    <Transition name="dots">
      <nav v-if="inView" class="dots" aria-label="Chapters">
        <button
          v-for="(c, i) in chapters"
          :key="c.id"
          type="button"
          :class="{ on: i === active }"
          :aria-label="c.title"
          :aria-current="i === active ? 'step' : undefined"
          @click="go(i)"
        />
      </nav>
    </Transition>
  </div>
</template>

<style scoped>
/* One chapter, one screen. */
.chapter {
  display: flex;
  min-height: 100svh;
  align-items: center;
}
.dots {
  position: fixed;
  right: clamp(0.75rem, 2.5vw, 2rem);
  top: 50%;
  z-index: 20;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  transform: translateY(-50%);
}
.dots button {
  width: 0.5rem;
  height: 0.5rem;
  border: 0;
  border-radius: 999px;
  padding: 0;
  background: color-mix(in oklab, var(--color-fg) 20%, transparent);
  cursor: pointer;
  transition:
    height 300ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color 300ms;
}
.dots button.on {
  height: 1.4rem;
  background: var(--color-fg);
}
.dots-enter-active,
.dots-leave-active {
  transition: opacity 250ms;
}
.dots-enter-from,
.dots-leave-to {
  opacity: 0;
}
</style>
