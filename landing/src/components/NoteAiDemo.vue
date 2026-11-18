<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ArrowLeft, Globe, Maximize2, Radio, RotateCcw, Sparkles } from '@lucide/vue'
import {
  Button,
  Diagram,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  IconMorph,
  Prose,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TextMorph,
} from 'elastic-ui'
import RichText from './RichText.vue'
import { libraryLabels } from '../i18n.js'

// The AI in a note, played back as a short scripted scene, the way the How section plays a
// pass with AgentReplay: the note editor as the app draws it and a student writing in class.
// A question typed in the middle and Ctrl+Enter: notes on it take its place, with a table. A
// rough line of their own and Ctrl+Enter: it stays, and a diagram goes under it. On the side, a
// note for each moment and the controls (play or pause, back, forward, start again). It starts
// once it is in view, pauses when it leaves, and ends on its conclusion. Under reduced motion it
// shows the end and steps through still frames instead of typing. The scene is made up; `demo`
// holds its texts, in each language.
const props = defineProps({
  demo: { type: Object, required: true },
})

// The figure's colours, from the app's figure palette (violet and green).
const COLORS = { character: '#7c3aed', planet: 'var(--color-success)' }

// ---- The scene's state: what the note shows at any moment ----
function initial() {
  return {
    l0: '', // the student's first lines, typed
    l1: '',
    q: '', // the question, typed
    qGone: false, // replaced by the notes on it
    heading: 0, // words of the heading shown
    line: 0, // words of the line under it
    rows: -1, // -1 no table yet, 0 its header, n its rows
    r: '', // the rough line, typed
    figure: false,
    keys: null, // where Ctrl+Enter shows: 'q' or 'r'
    pressed: false,
    caret: 'l0', // 'l0', 'l1', 'q', 'r', 'after' or null
  }
}
const s = reactive(initial())

const words = (text) => text.split(' ')
const headingWords = computed(() => words(props.demo.answer.heading))
const lineWords = computed(() => words(props.demo.answer.line))

// Each moment: its note, what plays, and the state once it has played.
const steps = computed(() => {
  const d = props.demo
  return [
    { note: d.notes[1], run: typeLines, end: { l0: d.lines[0], l1: d.lines[1], caret: 'l1' }, hold: 1600 },
    { note: d.notes[2], run: ask, end: { q: d.question, keys: null, caret: null }, hold: 300 },
    {
      note: d.notes[3],
      run: answer,
      end: { qGone: true, heading: headingWords.value.length, line: lineWords.value.length, rows: d.answer.rows.length },
      hold: 3200,
    },
    { note: d.notes[4], run: rough, end: { r: d.rough, keys: null, caret: null }, hold: 300 },
    { note: d.notes[5], run: complete, end: { figure: true }, hold: 3600 },
    { note: d.notes[6], run: carryOn, end: { caret: 'after' }, hold: 0 },
  ]
})

// The state at the end of moment `i` (0 is the note at rest, before anything).
function stateAt(i) {
  const next = initial()
  for (const step of steps.value.slice(0, i)) Object.assign(next, step.end)
  return next
}

// ---- Playing ----
const index = ref(0)
const playing = ref(false)
const finished = ref(false)
let run = 0
let active = false
const reduced = ref(false)

class Cancelled extends Error {}

// Waits `ms` of playing time: paused, the clock stops; cancelled, it throws.
function wait(ms) {
  const mine = run
  return new Promise((resolve, reject) => {
    let left = ms
    let last = performance.now()
    const tick = (now) => {
      if (mine !== run) return reject(new Cancelled())
      if (playing.value) left -= now - last
      last = now
      if (left <= 0) resolve()
      else requestAnimationFrame(tick)
    }
    requestAnimationFrame(tick)
  })
}

// Types like a person: an uneven pace, a pause after a word now and then, and a typed "->"
// turned into an arrow, as the editor does.
async function type(key, text) {
  s.caret = key
  await nextTick()
  reveal(key)
  for (const ch of text) {
    if (ch === '→') {
      s[key] += '-'
      await wait(70)
      s[key] += '>'
      await wait(160)
      s[key] = s[key].slice(0, -2) + '→'
    } else {
      s[key] += ch
    }
    await wait(ch === ' ' ? 70 + Math.random() * 90 : 38 + Math.random() * 45)
  }
}

async function typeLines() {
  await wait(300)
  await type('l0', props.demo.lines[0])
  await wait(450)
  await type('l1', props.demo.lines[1])
}

// Ctrl+Enter on a line: the keys show beside it and are pressed (a change of tone).
async function press(key) {
  s.keys = key
  await wait(700)
  s.pressed = true
  await wait(220)
  s.pressed = false
  await wait(380)
  s.keys = null
  s.caret = null
  // The model takes a moment before its first words.
  await wait(600)
}

async function ask() {
  await wait(500)
  await type('q', props.demo.question)
  await wait(500)
  await press('q')
}

// A question: its line goes, and the notes on it stream into its place.
async function answer() {
  s.qGone = true
  await wait(200)
  for (let i = 1; i <= headingWords.value.length; i++) {
    s.heading = i
    await wait(90)
  }
  for (let i = 1; i <= lineWords.value.length; i++) {
    s.line = i
    await wait(70)
  }
  await wait(300)
  for (let i = 0; i <= props.demo.answer.rows.length; i++) {
    s.rows = i
    await nextTick()
    reveal('table')
    await wait(450)
  }
}

async function rough() {
  await wait(400)
  await type('r', props.demo.rough)
  await wait(500)
  await press('r')
}

// The student's own line stays, and the figure goes under it.
async function complete() {
  s.figure = true
  await nextTick()
  reveal('figure')
  await wait(1200)
}

async function carryOn() {
  s.caret = 'after'
  await nextTick()
  reveal('after')
  await wait(300)
}

async function play() {
  if (active) {
    playing.value = true
    return
  }
  if (finished.value) restart()
  playing.value = true
  active = true
  const mine = ++run
  try {
    // A moment cut short by a pause resumes where it was; stepping set it to its end.
    while (index.value < steps.value.length) {
      const step = steps.value[index.value]
      index.value++
      if (reduced.value) {
        Object.assign(s, step.end)
        await nextTick()
        revealFocus()
        await wait(Math.max(step.hold, 2600))
      } else {
        await step.run()
        Object.assign(s, step.end)
        if (step.hold) await wait(step.hold)
      }
    }
    if (mine === run) {
      playing.value = false
      finished.value = true
    }
  } catch (e) {
    if (!(e instanceof Cancelled)) throw e
  } finally {
    if (mine === run) active = false
  }
}

function pause() {
  playing.value = false
}

// Jumping to a moment shows it as it ends, paused.
function goTo(i) {
  run++
  active = false
  playing.value = false
  index.value = Math.max(0, Math.min(steps.value.length, i))
  Object.assign(s, stateAt(index.value))
  finished.value = index.value === steps.value.length
  nextTick(revealFocus)
}

function restart() {
  run++
  active = false
  index.value = 0
  finished.value = false
  Object.assign(s, initial())
  screen.value?.scrollTo({ top: 0 })
}

function startAgain() {
  restart()
  play()
}

// ---- Keeping what moves in view, inside the note's own scroll ----
const screen = ref(null)
const refs = {}
function setRef(name) {
  return (el) => (refs[name] = el?.$el ?? el)
}

function reveal(name) {
  const box = screen.value
  const el = refs[name]
  if (!box || !el) return
  const b = box.getBoundingClientRect()
  const r = el.getBoundingClientRect()
  const margin = 28
  let top = box.scrollTop
  if (r.bottom > b.bottom - margin) top += r.bottom - b.bottom + margin
  if (r.top - (top - box.scrollTop) < b.top + margin) top = box.scrollTop + r.top - b.top - margin
  box.scrollTo({ top, behavior: reduced.value ? 'auto' : 'smooth' })
}

function revealFocus() {
  const i = index.value
  reveal(i >= 6 ? 'after' : i >= 5 ? 'figure' : i >= 4 ? 'r' : i >= 3 ? 'table' : i >= 2 ? 'l1' : 'l0')
}

// ---- Starting where it is looked at ----
const root = ref(null)
let observer = null
let startTimer = null
let pausedByScroll = false

onMounted(() => {
  reduced.value =
    document.documentElement.dataset.motion === 'none' ||
    (document.documentElement.dataset.motion !== 'full' && matchMedia('(prefers-reduced-motion: reduce)').matches)
  // Reduced motion: the scene shows its end, and plays only when asked, in still frames.
  if (reduced.value) {
    goTo(steps.value.length)
    return
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      const seen = entry.intersectionRect.height
      const whole = Math.min(entry.boundingClientRect.height, window.innerHeight)
      const inView = seen >= whole * 0.85
      if (inView && !playing.value && (index.value === 0 || pausedByScroll) && !finished.value) {
        clearTimeout(startTimer)
        startTimer = setTimeout(() => {
          pausedByScroll = false
          play()
        }, 400)
      } else if (!inView) {
        clearTimeout(startTimer)
      }
      if (seen < whole * 0.3 && playing.value) {
        pausedByScroll = true
        pause()
      }
    },
    { threshold: [0, 0.3, 0.6, 0.85, 1] },
  )
  observer.observe(root.value)
})

onBeforeUnmount(() => {
  run++
  observer?.disconnect()
  clearTimeout(startTimer)
})

// A new language starts the scene over in that language.
watch(
  () => props.demo,
  () => goTo(reduced.value ? steps.value.length : 0),
)

// ---- What the side says ----
const note = computed(() => (index.value === 0 ? props.demo.notes[0] : steps.value[index.value - 1].note))
const isConclusion = computed(() => index.value === steps.value.length)
const counter = computed(() => `${index.value} / ${steps.value.length}`)

// A line's text in pieces, its arrows drawn as the library's arrow icon.
const pieces = (text) => text.split(/(→)/).filter(Boolean)
</script>

<template>
  <div ref="root" class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem] lg:gap-8">
    <!-- The note being written, as the app draws it. Watched, not used: the side tells it. -->
    <div
      class="flex h-[28rem] flex-col overflow-hidden rounded-[var(--agent-replay-radius,1.75rem)] border border-border bg-bg sm:h-[32rem]"
      aria-hidden="true"
      inert
    >
      <div class="flex items-center justify-between gap-3 px-4 pt-4 sm:px-6">
        <Button variant="ghost" size="sm" :icon="ArrowLeft" tabindex="-1">{{ demo.back }}</Button>
        <div class="flex items-center gap-1">
          <Button variant="ghost" size="icon" :icon="Radio" tabindex="-1" :aria-label="demo.live" />
          <Button variant="ghost" size="icon" :icon="Sparkles" class="bg-bg-muted text-fg" tabindex="-1" :aria-label="demo.toggle" />
          <Button variant="ghost" size="icon" :icon="Maximize2" tabindex="-1" :aria-label="demo.zen" />
        </div>
      </div>

      <div ref="screen" class="note-scroll min-h-0 flex-1 overflow-y-auto scrollbar-none px-5 pt-6 pb-10 sm:px-10 sm:pt-8">
        <p class="m-0 mb-6 text-display text-fg">{{ demo.title }}</p>
        <Prose class="note-body">
          <!-- The student's lines, typed as the class goes on. -->
          <template v-for="key in ['l0', 'l1']" :key="key">
            <p v-if="s[key] || s.caret === key" :ref="setRef(key)">
              <template v-for="(part, j) in pieces(s[key])" :key="j">
                <span v-if="part === '→'" class="inline-arrow">→</span><template v-else>{{ part }}</template>
              </template><span v-if="s.caret === key" class="note-caret" :class="playing && 'note-caret--typing'" />
            </p>
          </template>

          <!-- A question, typed; then the notes on it, in its place. -->
          <template v-if="!s.qGone">
            <p v-if="s.q || s.caret === 'q'" :ref="setRef('q')">
              {{ s.q }}<span v-if="s.caret === 'q'" class="note-caret" :class="playing && 'note-caret--typing'" />
              <span v-if="s.keys === 'q'" class="note-keys">
                <kbd :class="s.pressed && 'note-key--pressed'">{{ demo.keys[0] }}</kbd>
                <kbd :class="s.pressed && 'note-key--pressed'">{{ demo.keys[1] }}</kbd>
              </span>
            </p>
          </template>
          <template v-else>
            <h2 v-if="s.heading">
              <span
                v-for="(word, i) in headingWords.slice(0, s.heading)"
                :key="i"
                class="animate-blur-in motion-reduce:animate-none"
              >{{ word + ' ' }}</span>
            </h2>
            <p v-if="s.line">
              <span
                v-for="(word, i) in lineWords.slice(0, s.line)"
                :key="i"
                class="animate-blur-in motion-reduce:animate-none"
              >{{ word + ' ' }}</span>
            </p>
            <div v-if="s.rows >= 0" :ref="setRef('table')" class="not-prose my-4">
              <Table :aria-label="demo.answer.label">
                <TableHeader class="animate-blur-in motion-reduce:animate-none">
                  <TableRow>
                    <TableHead v-for="(head, i) in demo.answer.head" :key="i">{{ head }}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow
                    v-for="row in demo.answer.rows.slice(0, s.rows)"
                    :key="row[0]"
                    class="animate-blur-in motion-reduce:animate-none"
                  >
                    <TableCell class="text-fg"><RichText :text="row[0]" /></TableCell>
                    <TableCell><RichText :text="row[1]" /></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          </template>

          <!-- A rough line of their own: it stays, and the piece that shows it goes under it. -->
          <p v-if="s.r || s.caret === 'r'" :ref="setRef('r')">
            <template v-for="(part, j) in pieces(s.r)" :key="j">
              <span v-if="part === '→'" class="inline-arrow">→</span><template v-else>{{ part }}</template>
            </template><span v-if="s.caret === 'r'" class="note-caret" :class="playing && 'note-caret--typing'" />
            <span v-if="s.keys === 'r'" class="note-keys">
              <kbd :class="s.pressed && 'note-key--pressed'">{{ demo.keys[0] }}</kbd>
              <kbd :class="s.pressed && 'note-key--pressed'">{{ demo.keys[1] }}</kbd>
            </span>
          </p>
          <div v-if="s.figure" :ref="setRef('figure')" class="not-prose my-4">
            <Diagram :label="demo.figure.label" class="rounded-[var(--radius-xl)] bg-bg-subtle p-5 sm:p-6">
              <DiagramGroup layout="row">
                <DiagramGroup layout="column">
                  <DiagramChip v-for="name in demo.figure.characters" :key="name" :color="COLORS.character">{{ name }}</DiagramChip>
                </DiagramGroup>
                <DiagramArrow label="homeworld" />
                <DiagramChip :icon="Globe" :color="COLORS.planet" :note="demo.figure.planetNote">{{ demo.figure.planet }}</DiagramChip>
              </DiagramGroup>
            </Diagram>
          </div>
          <p v-if="s.caret === 'after'" :ref="setRef('after')"><span class="note-caret" /></p>
        </Prose>
      </div>
    </div>

    <!-- What to notice now, and the controls, as AgentReplay has them. -->
    <div class="flex flex-col justify-between gap-3 lg:gap-6 lg:py-4">
      <div aria-live="polite" class="min-h-16 lg:min-h-24">
        <Transition
          mode="out-in"
          enter-active-class="animate-blur-in motion-reduce:animate-none"
          leave-active-class="transition-opacity duration-150"
          leave-to-class="opacity-0"
        >
          <p :key="`${index}-${note}`" class="m-0 text-copy" :class="isConclusion ? 'font-medium text-fg' : 'text-fg-secondary'">
            {{ note }}
          </p>
        </Transition>
      </div>
      <div class="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          class="rounded-full text-fg-muted"
          :aria-label="playing ? libraryLabels.pause : libraryLabels.play"
          @click="playing ? pause() : play()"
        >
          <IconMorph :icon="playing ? 'pause' : 'play'" class="size-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="rounded-full text-fg-muted"
          :aria-label="libraryLabels.previous"
          :disabled="index === 0"
          @click="goTo(index - 1)"
        >
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6" /></svg>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="rounded-full text-fg-muted"
          :aria-label="libraryLabels.next"
          :disabled="finished"
          @click="goTo(playing ? index : index + 1)"
        >
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 18 6-6-6-6" /></svg>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          class="rounded-full text-fg-muted"
          :icon="RotateCcw"
          :aria-label="libraryLabels.restart"
          @click="startAgain"
        />
        <TextMorph class="ml-2 text-meta tabular-nums text-fg-muted" :text="counter" />
      </div>
    </div>
  </div>
</template>

<style scoped>
/* The note's own scroll fades at the edges it runs under (USAGE 13). */
.note-scroll {
  mask-image: linear-gradient(to bottom, transparent, #000 1.25rem, #000 calc(100% - 2.5rem), transparent);
}

/* The heading the AI writes reads as a heading of the note, above its line. */
.note-body :deep(h2) {
  margin: 1.75rem 0 0.5rem;
  font-size: 1.3rem;
  line-height: 1.3;
  font-weight: 600;
  letter-spacing: -0.01em;
}

/* The editor's caret: still while typing, blinking when it waits. */
.note-caret {
  display: inline-block;
  width: 2px;
  height: 1.15em;
  margin-left: 1px;
  vertical-align: text-bottom;
  background: var(--color-fg);
  animation: note-blink 1.1s steps(1) infinite;
}
.note-caret--typing {
  animation: none;
}
@keyframes note-blink {
  50% {
    opacity: 0;
  }
}

/* Ctrl+Enter, shown beside the line it is pressed on; a press is a change of tone. */
.note-keys {
  display: inline-flex;
  gap: 0.25rem;
  margin-left: 0.75rem;
  vertical-align: middle;
  animation: var(--animate-blur-in);
}
.note-keys kbd {
  border-radius: var(--radius-sm);
  background: var(--color-bg-muted);
  padding: 0.1rem 0.45rem;
  font-family: var(--font-sans);
  font-size: var(--text-meta, 0.8125rem);
  color: var(--color-fg-secondary);
  transition: background-color 120ms var(--ease-soft), color 120ms var(--ease-soft);
}
.note-keys kbd.note-key--pressed {
  background: var(--color-fg);
  color: var(--color-bg);
}

@media (prefers-reduced-motion: reduce) {
  .note-caret,
  .note-keys {
    animation: none;
  }
}
</style>
