<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { copy } from '../i18n.js'
import PipelineArtifact from './PipelineArtifact.vue'

// What the night pass does (Jose, 2026-11-21): notes from two students, more of them and not neatly
// laid out, as people really leave them; and beside them the joint page, the crafted thing: rounded,
// well set, with its flow and its points. The page is not built note by note (that is not how it
// works): the notes come in, a beat, and the page appears whole and writes itself in, part after
// part, with an artifact in it: the pipeline the notes describe, to try (PipelineArtifact). Flat, no shadows. It plays once, when reached, and stays. Under
// reduced motion it shows the end, still.

// Each note sits a little off: a nudge sideways and a slight lean, so the column looks left by hand.
const LOOSE = [
  { x: 0, r: -1.5, w: 92 },
  { x: 14, r: 1.2, w: 84 },
  { x: 4, r: 0.6, w: 70 },
  { x: 22, r: -1, w: 80 },
  { x: 2, r: 1.8, w: 88 },
  { x: 16, r: -0.8, w: 86 },
]
const NOTE_MS = 280 // between two notes coming in
const PAGE_AT = 2600 // the page appears
const PART_MS = 380 // between two parts of the page

const notes = computed(() => copy.value.hive.notes)
const shownNotes = ref(0)
const pageOn = ref(false)
const parts = ref(0) // title, line, flow, points, foot
const root = ref(null)
let timers = []
let observer = null

const later = (ms, fn) => timers.push(setTimeout(fn, ms))
function play() {
  timers.forEach(clearTimeout)
  timers = []
  shownNotes.value = 0
  pageOn.value = false
  parts.value = 0
  notes.value.forEach((_, i) => later(300 + i * NOTE_MS, () => (shownNotes.value = i + 1)))
  later(PAGE_AT, () => (pageOn.value = true))
  for (let k = 1; k <= 5; k++) later(PAGE_AT + 200 + k * PART_MS, () => (parts.value = k))
  // Once written, it stays: the notes and the page remain on the page (Jose, 2026-11-21: "que se
  // quede ahí, no aparecer y desaparecer").
}

onMounted(() => {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) {
    shownNotes.value = notes.value.length
    pageOn.value = true
    parts.value = 5
    return
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        play()
        observer.disconnect()
      }
    },
    { rootMargin: '-30% 0px -30% 0px' },
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  timers.forEach(clearTimeout)
  observer?.disconnect()
})
</script>

<template>
  <figure ref="root" class="m-0" :aria-label="copy.hive.label">
    <div class="grid items-center gap-6 md:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] md:gap-8" aria-hidden="true">
      <!-- The notes, as two people left them: not quite in line. -->
      <div class="notes">
        <p
          v-for="(n, i) in notes"
          :key="i"
          class="note"
          :class="[n.by === notes[0].by ? 'a' : 'b', { in: i < shownNotes }]"
          :style="{ '--x': `${LOOSE[i].x}px`, '--r': `${LOOSE[i].r}deg`, width: `${LOOSE[i].w}%` }"
        >
          <span class="who">{{ n.by }}</span>{{ n.text }}
        </p>
      </div>

      <!-- The joint page: rounded, set with care, written in part after part. -->
      <article class="page" :class="{ on: pageOn }">
        <div class="part" :class="{ in: parts >= 1 }">
          <p class="kicker">
            <span class="face a">{{ notes[0].by[0] }}</span><span class="face b">{{ notes[1].by[0] }}</span>
            {{ copy.hive.page.foot }}
          </p>
          <p class="title">{{ copy.hive.page.title }}</p>
        </div>
        <p class="part line" :class="{ in: parts >= 2 }">{{ copy.hive.page.line }}</p>
        <!-- The artifact: the pipeline the notes describe, to try. -->
        <div class="part" :class="{ in: parts >= 3 }">
          <PipelineArtifact v-if="parts >= 3" />
        </div>
        <ul class="part points" :class="{ in: parts >= 4 }">
          <li v-for="(p, i) in copy.hive.page.points" :key="i">{{ p }}</li>
        </ul>
      </article>
    </div>
  </figure>
</template>

<style scoped>
/* Notes: flat, in the page's grey, each a little off its line. Two people, two tints. */
.notes {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}
.note {
  margin: 0;
  padding: 0.7rem 0.95rem;
  border-radius: 0.95rem;
  font-size: 0.92rem;
  line-height: 1.4;
  color: var(--color-fg);
  opacity: 0;
  transform: translate(calc(var(--x) - 12px), 8px) rotate(var(--r));
  transition:
    opacity 380ms ease,
    transform 520ms cubic-bezier(0.34, 1.35, 0.64, 1);
}
.note.in {
  opacity: 1;
  transform: translate(var(--x), 0) rotate(var(--r));
}
.note.a {
  background: #fdf0cf;
}
.note.b {
  background: var(--color-bg-muted);
}
.who {
  margin-right: 0.45rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-fg-muted);
}

/* The joint page: one rounded surface, generous, the crafted piece. */
.page {
  padding: 1.9rem 2rem 1.8rem;
  border-radius: 1.8rem;
  background: var(--color-bg-subtle);
  text-align: left;
  opacity: 0;
  transform: scale(0.97);
  transition:
    opacity 450ms ease,
    transform 600ms cubic-bezier(0.22, 1, 0.36, 1);
}
.page.on {
  opacity: 1;
  transform: none;
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
.kicker {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  margin: 0 0 0.9rem;
  font-size: 0.78rem;
  color: var(--color-fg-muted);
}
.face {
  display: inline-grid;
  width: 1.35rem;
  height: 1.35rem;
  place-items: center;
  border-radius: 999px;
  font-size: 0.68rem;
  font-weight: 650;
  color: #3a2c12;
}
.face.a {
  background: #f6d896;
}
.face.b {
  margin: 0 0.45rem 0 -0.35rem;
  background: #ddd9d0;
  outline: 2px solid var(--color-bg-subtle);
}
.title {
  margin: 0;
  font-size: 1.55rem;
  line-height: 1.2;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--color-fg);
}
.line {
  margin: 0.8rem 0 1.2rem;
  font-size: 1rem;
  line-height: 1.6;
  color: var(--color-fg-secondary);
}
.flow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.45rem;
  padding: 0.8rem;
  border-radius: 1.1rem;
  background: var(--color-bg);
}
.chip {
  padding: 0.35rem 0.7rem;
  border-radius: 0.7rem;
  font-size: 0.85rem;
  font-weight: 550;
  background: var(--color-bg-muted);
  color: var(--color-fg);
}
.c1 {
  background: #efe9fe;
  color: #5b3fd6;
}
.c2 {
  background: #e7f0ff;
  color: #2563eb;
}
.c3 {
  background: #e6f6ec;
  color: #1c7c45;
}
.arrow {
  width: 1.1rem;
  color: var(--color-fg-muted);
}
.points {
  display: grid;
  gap: 0.45rem;
  margin: 1.2rem 0 0;
  padding: 0;
  list-style: none;
}
.points li {
  position: relative;
  padding-left: 1.1rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--color-fg-secondary);
}
.points li::before {
  content: '';
  position: absolute;
  left: 0.15rem;
  top: 0.62em;
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 999px;
  background: #f0aa3c;
}

@media (prefers-reduced-motion: reduce) {
  .note,
  .page,
  .part {
    transition: none;
  }
}
</style>
