<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowDown } from '@lucide/vue'
import { copy } from '../i18n.js'
import PipelineArtifact from './PipelineArtifact.vue'

// What the night pass does (Jose, 2026-11-21): notes from two students, more of them and not neatly
// laid out, as people really leave them; and beside them the joint page, the crafted thing: rounded,
// well set, with its flow, its points and an artifact in it: the pipeline the notes describe, to try
// (PipelineArtifact). Flat, no shadows. It is there from the start, already composed (Jose: the
// entrance "tarda demasiado"); only the artifact starts running once the scene is reached.

// Each note sits a little off: a nudge sideways and a slight lean, so the column looks left by hand.
const LOOSE = [
  { x: 0, r: -1.5, w: 92 },
  { x: 14, r: 1.2, w: 84 },
  { x: 4, r: 0.6, w: 70 },
  { x: 22, r: -1, w: 80 },
  { x: 2, r: 1.8, w: 88 },
  { x: 16, r: -0.8, w: 86 },
]

const notes = computed(() => copy.value.hive.notes)
const shownNotes = computed(() => notes.value.length)
const pageOn = true
const parts = 5 // title, line, flow, points, foot: all shown
const seen = ref(false) // the artifact runs once the scene is in view
const root = ref(null)
let observer = null

onMounted(() => {
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        seen.value = true
        observer.disconnect()
      }
    },
    { rootMargin: '-20% 0px -20% 0px' },
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => observer?.disconnect())
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

      <!-- On phones the two columns stack, so the link between them is said out loud (Jose,
           2026-11-22: on mobile the scene "quizás no se entiende"). -->
      <p class="join md:hidden"><ArrowDown class="size-4" />{{ copy.hive.join }}</p>

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
          <PipelineArtifact :active="seen" />
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

/* Phones: the notes become a small pile (three of them, overlapping a little) so the page is
   reached at once, with the line that joins them in between. */
.join {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  margin: -0.25rem 0;
  font-size: 0.85rem;
  font-weight: 550;
  color: var(--color-fg-muted);
}
@media (max-width: 767px) {
  .notes {
    gap: 0;
  }
  .note:nth-child(n + 4) {
    display: none;
  }
  .note + .note {
    margin-top: -0.35rem;
  }
  .note.a {
    position: relative;
    z-index: 1;
  }
  .page {
    padding: 1.5rem 1.35rem 1.4rem;
    border-radius: 1.5rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .note,
  .page,
  .part {
    transition: none;
  }
}
</style>
