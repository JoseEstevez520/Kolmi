<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { copy } from '../i18n.js'

// What the night pass does, as one physical gesture (Jose, 2026-11-21: the first version, notes
// flying into a glowing logo, was "muy slop"). Loose notes from four students slide in one by one
// and land on a pile in the centre, each a little askew; the pile presses together, and the page of
// the class unfolds out of it, its lines coming in one after the other. It holds, folds back into
// the pile, and after a rest the notes slide out and it all starts again (a loop with a pause, as
// Jose asked). The timeline is a list of steps in milliseconds, so it reads and changes easily.
// Under reduced motion it shows the page, still.

// Where each note comes from, and how it sits on the pile.
const NOTES = [
  { from: '-60vw', lean: -5, kind: 'sticky' },
  { from: '60vw', lean: 3, kind: 'card' },
  { from: '-60vw', lean: 6, kind: 'card' },
  { from: '60vw', lean: -3, kind: 'sticky' },
]
// The scene's timeline (ms): when each state starts.
const STEPS = [
  [400, 'note0'],
  [800, 'note1'],
  [1200, 'note2'],
  [1600, 'note3'],
  [2500, 'press'],
  [3000, 'page'],
  [3300, 'line0'],
  [3600, 'line1'],
  [3900, 'line2'],
  [4200, 'line3'],
  [8200, 'fold'],
  [8900, 'leave'],
  [11000, 'restart'], // the rest before it plays again
]

const landed = ref(0) // how many notes are on the pile
const pressed = ref(false)
const page = ref(false)
const lines = ref(0)
const folding = ref(false)
const leaving = ref(false)
const reduced = ref(false)
const root = ref(null)
let timers = []
let observer = null

function reset() {
  landed.value = 0
  pressed.value = false
  page.value = false
  lines.value = 0
  folding.value = false
  leaving.value = false
}
function play() {
  reset()
  timers = STEPS.map(([ms, step]) =>
    setTimeout(() => {
      if (step.startsWith('note')) landed.value = Number(step.slice(4)) + 1
      else if (step === 'press') pressed.value = true
      else if (step === 'page') page.value = true
      else if (step.startsWith('line')) lines.value = Number(step.slice(4)) + 1
      else if (step === 'fold') folding.value = true
      else if (step === 'leave') leaving.value = true
      else if (step === 'restart') play()
    }, ms),
  )
}

onMounted(() => {
  reduced.value = matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduced.value) {
    page.value = true
    lines.value = 4
    return
  }
  // It starts when it is reached, from the beginning.
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting) {
        play()
        observer.disconnect()
      }
    },
    { threshold: 0.5 },
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  timers.forEach(clearTimeout)
  observer?.disconnect()
})

function noteStyle(i) {
  const n = NOTES[i]
  const on = i < landed.value && !leaving.value
  const stackY = (i - 1.5) * -6
  return {
    transform: on
      ? `translate(-50%, calc(-50% + ${pressed.value ? 0 : stackY}px)) rotate(${pressed.value ? n.lean / 3 : n.lean}deg) scale(${pressed.value ? 0.92 : 1})`
      : `translate(calc(-50% + ${n.from}), -50%) rotate(${n.lean * 2}deg)`,
    opacity: on && !(page.value && !folding.value) ? 1 : 0,
    zIndex: i,
  }
}
</script>

<template>
  <figure ref="root" class="scene m-0" :aria-label="copy.hive.label">
    <div class="stage" aria-hidden="true">
      <div v-for="(text, i) in copy.hive.notes" :key="i" class="note" :class="NOTES[i].kind" :style="noteStyle(i)">
        <p class="m-0">{{ text }}</p>
        <p class="by">{{ copy.hive.by[i] }}</p>
      </div>

      <article class="page" :class="{ open: page && !folding }">
        <p class="page-title" :class="{ on: lines >= 1 }">{{ copy.hive.page.title }}</p>
        <p class="page-line" :class="{ on: lines >= 2 }">{{ copy.hive.page.line }}</p>
        <div class="steps" :class="{ on: lines >= 3 }">
          <template v-for="(step, i) in copy.hive.page.steps" :key="i">
            <span class="chip" :class="`chip-${i}`">{{ step }}</span>
            <span v-if="i < copy.hive.page.steps.length - 1" class="arrow">→</span>
          </template>
        </div>
        <p class="page-foot" :class="{ on: lines >= 4 }">{{ copy.hive.page.foot }}</p>
      </article>
    </div>
  </figure>
</template>

<style scoped>
.stage {
  position: relative;
  width: 100%;
  height: clamp(20rem, 50vh, 26rem);
}

/* A note: it slides in from its side and lands on the pile with a little give. */
.note {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(19rem, 80vw);
  padding: 0.95rem 1.05rem 0.8rem;
  border-radius: 0.9rem;
  background: #fff;
  box-shadow: 0 10px 24px -16px rgb(60 40 0 / 0.35), 0 0 0 1px rgb(0 0 0 / 0.04);
  font-size: 0.95rem;
  line-height: 1.4;
  color: #3a3a36;
  text-align: left;
  transition:
    transform 700ms cubic-bezier(0.34, 1.3, 0.64, 1),
    opacity 380ms ease;
}
.note.sticky {
  background: #fff3b8;
  border-radius: 0.35rem;
}
.by {
  margin: 0.45rem 0 0;
  font-size: 0.75rem;
  color: #8a867c;
}

/* The page: it unfolds out of the pile (from its size to its own), then its lines come in. */
.page {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(34rem, 94%);
  padding: 1.5rem 1.6rem 1.25rem;
  border-radius: 1.2rem;
  background: #fff;
  box-shadow: 0 30px 60px -32px rgb(60 40 0 / 0.4), 0 0 0 1px rgb(0 0 0 / 0.04);
  text-align: left;
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.56, 0.4);
  transition:
    transform 650ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 250ms ease;
}
.page.open {
  opacity: 1;
  transform: translate(-50%, -50%);
}
.page > * {
  opacity: 0;
  transform: translateY(6px);
  transition:
    opacity 450ms ease,
    transform 450ms cubic-bezier(0.22, 1, 0.36, 1);
}
.page > .on {
  opacity: 1;
  transform: none;
}
.page-title {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: #1a1a18;
}
.page-line {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #4a4842;
}
.page-foot {
  margin: 1rem 0 0;
  font-size: 0.75rem;
  color: #8a867c;
}
.steps {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
}
.chip {
  padding: 0.3rem 0.6rem;
  border-radius: 0.55rem;
  font-size: 0.82rem;
  font-weight: 550;
  background: #f1f0ec;
  color: #2d2b27;
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
  color: #a19d92;
  font-size: 0.85rem;
}

@media (prefers-reduced-motion: reduce) {
  .note,
  .page,
  .page > * {
    transition: none;
  }
}
</style>
