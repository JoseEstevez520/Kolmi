<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { copy } from '../i18n.js'

// What the night pass does, flat and in order (Jose, 2026-11-21: the earlier scenes were "slop",
// with shadows that are not his style and everything piled up). Two columns, no shadows, no
// borders, surfaces in the page's own greys: on the left the loose notes of four students, one under
// the other; on the right the page of the class. One note at a time lights up, and the part of the
// page that comes from it appears, so you see each note become part of the page. It holds, clears,
// rests and plays again; it starts when reached. Under reduced motion it shows the end, still.
const STEP_MS = 1100 // between one note and the next
const HOLD_MS = 4200 // the finished page, before it clears
const REST_MS = 1400 // empty, before it plays again

const active = ref(-1) // the note lighting up now
const shown = ref(0) // how many parts of the page are on
const root = ref(null)
let timers = []
let observer = null

function later(ms, fn) {
  timers.push(setTimeout(fn, ms))
}
function play() {
  timers.forEach(clearTimeout)
  timers = []
  active.value = -1
  shown.value = 0
  const n = copy.value.hive.notes.length
  for (let i = 0; i < n; i++) {
    later(400 + i * STEP_MS, () => (active.value = i))
    later(400 + i * STEP_MS + 350, () => (shown.value = i + 1))
  }
  const end = 400 + n * STEP_MS
  later(end, () => (active.value = -1))
  later(end + HOLD_MS, () => (shown.value = 0))
  later(end + HOLD_MS + REST_MS, play)
}

onMounted(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    shown.value = copy.value.hive.notes.length
    return
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        play()
        observer.disconnect()
      }
    },
    { rootMargin: '-35% 0px -35% 0px' },
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  timers.forEach(clearTimeout)
  observer?.disconnect()
})
</script>

<template>
  <figure ref="root" class="scene m-0" :aria-label="copy.hive.label">
    <div class="grid gap-4 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] md:gap-6" aria-hidden="true">
      <!-- The notes, as each student left it. -->
      <ul class="m-0 flex list-none flex-col gap-2.5 p-0">
        <li v-for="(text, i) in copy.hive.notes" :key="i" class="note" :class="{ on: active === i, used: i < shown && active !== i }">
          <span class="who">{{ copy.hive.by[i] }}</span>
          <span class="text">{{ text }}</span>
        </li>
      </ul>

      <!-- The page they become, part by part. -->
      <article class="page">
        <p class="part title" :class="{ in: shown >= 1 }">{{ copy.hive.page.title }}</p>
        <p class="part line" :class="{ in: shown >= 2 }">{{ copy.hive.page.line }}</p>
        <div class="part steps" :class="{ in: shown >= 3 }">
          <template v-for="(step, i) in copy.hive.page.steps" :key="i">
            <span class="chip" :class="`chip-${i}`">{{ step }}</span>
            <span v-if="i < copy.hive.page.steps.length - 1" class="arrow">→</span>
          </template>
        </div>
        <p class="part rollback" :class="{ in: shown >= 4 }">{{ copy.hive.page.rollback }}</p>
        <p class="part foot" :class="{ in: shown >= 4 }">{{ copy.hive.page.foot }}</p>
      </article>
    </div>
  </figure>
</template>

<style scoped>
/* A note: the page's muted grey, no shadow, no border. Lit, it turns honey; used, it rests. */
.note {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.85rem 1rem;
  border-radius: 1rem;
  background: var(--color-bg-muted);
  transition:
    background-color 350ms ease,
    opacity 350ms ease;
}
.note.on {
  background: #fbe7bf;
}
.note.used {
  opacity: 0.55;
}
.who {
  font-size: 0.75rem;
  font-weight: 550;
  color: var(--color-fg-muted);
}
.text {
  font-size: 0.95rem;
  line-height: 1.4;
  color: var(--color-fg);
}

/* The page: one flat surface, a step lighter than the notes. */
.page {
  min-height: 100%;
  padding: 1.6rem 1.7rem;
  border-radius: 1.4rem;
  background: var(--color-bg-subtle);
  text-align: left;
}
.part {
  opacity: 0;
  transform: translateY(8px);
  filter: blur(4px);
  transition:
    opacity 500ms ease,
    transform 600ms cubic-bezier(0.22, 1, 0.36, 1),
    filter 500ms ease;
}
.part.in {
  opacity: 1;
  transform: none;
  filter: none;
}
.title {
  margin: 0 0 0.6rem;
  font-size: 1.35rem;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: var(--color-fg);
}
.line,
.rollback {
  margin: 0 0 1rem;
  font-size: 1rem;
  line-height: 1.55;
  color: var(--color-fg-secondary);
}
.rollback {
  margin: 1rem 0 0;
}
.foot {
  margin: 1.1rem 0 0;
  font-size: 0.75rem;
  color: var(--color-fg-muted);
}
.steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}
.chip {
  padding: 0.3rem 0.65rem;
  border-radius: 0.6rem;
  font-size: 0.85rem;
  font-weight: 550;
  background: var(--color-bg-muted);
  color: var(--color-fg);
}
.chip-1 {
  background: #efe9fe;
  color: #5b3fd6;
}
.chip-2 {
  background: #e7f0ff;
  color: #2563eb;
}
.chip-3 {
  background: #e6f6ec;
  color: #1c7c45;
}
.arrow {
  color: var(--color-fg-muted);
  font-size: 0.85rem;
}

@media (prefers-reduced-motion: reduce) {
  .note,
  .part {
    transition: none;
  }
}
</style>
