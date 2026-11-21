<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import MomentSection from './MomentSection.vue'

// After the hero, the page stops scrolling down and becomes one stage pinned to the screen (Jose,
// 2026-11-21: normal scroll only from the hero to the first section; then "que se quede en el
// centro"). Each screen of scrolling moves to the next chapter: the one on show leaves, the next
// comes in, and its own animation plays by itself (Jose: "que vayan solas", not tied to the scroll).
// Chapters are mounted when they come on, so their scenes start from the beginning. Dots on the
// side show where you are. Under reduced motion the chapters are simply one under the other.
const props = defineProps({
  // [{ id, title, layout }], one slot per id with the chapter's picture
  chapters: { type: Array, required: true },
})

const SCREENS_PER_CHAPTER = 0.6 // shorter: a chapter changes with less scrolling
const track = ref(null)
const active = ref(0)
const reduced = ref(false)
let frame = 0

function measure() {
  frame = 0
  const el = track.value
  if (!el) return
  const total = el.offsetHeight - innerHeight
  const p = Math.min(0.9999, Math.max(0, -el.getBoundingClientRect().top / total))
  active.value = Math.floor(p * props.chapters.length)
}
const onScroll = () => {
  if (!frame) frame = requestAnimationFrame(measure)
}

onMounted(() => {
  reduced.value = matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduced.value) return
  measure()
  addEventListener('scroll', onScroll, { passive: true })
  addEventListener('resize', onScroll)
})
onBeforeUnmount(() => {
  removeEventListener('scroll', onScroll)
  removeEventListener('resize', onScroll)
  cancelAnimationFrame(frame)
})

// A dot takes you to its chapter.
function go(i) {
  const el = track.value
  const total = el.offsetHeight - innerHeight
  const top = el.getBoundingClientRect().top + scrollY
  scrollTo({ top: top + ((i + 0.5) / props.chapters.length) * total, behavior: 'smooth' })
}
</script>

<template>
  <!-- Reduced motion: no pinning, one chapter under the other. -->
  <div v-if="reduced">
    <MomentSection v-for="c in chapters" :id="c.id" :key="c.id" :title="c.title" :layout="c.layout">
      <slot :name="c.id" />
    </MomentSection>
  </div>

  <div v-else ref="track" class="relative" :style="{ height: `${chapters.length * SCREENS_PER_CHAPTER * 100 + 100}vh` }">
    <span v-for="c in chapters" :id="c.id" :key="`anchor-${c.id}`" class="anchor" />
    <div class="sticky top-0 flex h-svh items-center overflow-hidden">
      <Transition name="chapter" mode="out-in">
        <MomentSection :key="chapters[active].id" class="w-full" :title="chapters[active].title" :layout="chapters[active].layout">
          <slot :name="chapters[active].id" />
        </MomentSection>
      </Transition>

      <nav class="dots" aria-label="Chapters">
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
    </div>
  </div>
</template>

<style scoped>
.anchor {
  position: absolute;
  top: 0;
}
.chapter-enter-active,
.chapter-leave-active {
  transition:
    opacity 260ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 260ms cubic-bezier(0.22, 1, 0.36, 1);
}
.chapter-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.chapter-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
.dots {
  position: absolute;
  right: clamp(0.75rem, 2.5vw, 2rem);
  top: 50%;
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
</style>
