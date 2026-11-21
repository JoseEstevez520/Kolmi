<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import MomentSection from './MomentSection.vue'

// After the hero, the chapters (Jose, 2026-11-21: the pinned stage driven by script was "muy
// confuso"). Following the usual advice for this kind of page, the scroll is the browser's own, not
// taken over: each chapter fills one screen and the page snaps to it (CSS scroll-snap, `proximity`
// in style.css, so the hero and the footer scroll freely), the way it moves is always the same, and
// keys and trackpads behave as everywhere else. Each chapter's animation plays by itself when it
// arrives (MomentSection). Dots on the side show where you are and take you to a chapter; they show
// only while the chapters are on screen.
defineProps({
  // [{ id, title, layout }], one slot per id with the chapter's picture
  chapters: { type: Array, required: true },
})

const root = ref(null)
const active = ref(0)
const inView = ref(false)
let watchChapters = null
let watchRegion = null

onMounted(() => {
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
/* One chapter, one screen, and the page snaps to its centre. */
.chapter {
  display: flex;
  min-height: 100svh;
  align-items: center;
  scroll-snap-align: center;
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
