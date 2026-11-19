<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ArrowLeft, Cpu, Globe, Maximize2, Monitor, Radio, RotateCcw, Sparkles, User } from '@lucide/vue'
import {
  Button,
  Diagram,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  Prose,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  inkFlow,
} from 'elastic-ui'
import RichText from './RichText.vue'
import { libraryLabels } from '../i18n.js'

// The AI in a note, played back as one scene, the way a product demo shows it: the note editor as
// the app draws it and a student taking notes in class. A question typed in the middle and
// Ctrl+Enter (a key press in a floating pill): the line dims while the AI thinks, and the answer
// takes its place, its heading and line landing in ink, then the figure that walks the answer,
// then the table's rows. It starts once in view, pauses when it leaves, and plays again from the
// button under the note. Under reduced motion it shows the end, still. The scene is made up;
// `demo` holds its texts, in each language.
const props = defineProps({
  demo: { type: Object, required: true },
})

// The figure's colours, from the app's figure palette: blue for what the student does, violet for
// the browser's engine, green for the screen. The network keeps the app's own grey.
const COLORS = { url: '#2563eb', render: '#7c3aed', screen: 'var(--color-success)' }

// ---- What the note shows at any moment ----
function initial() {
  return {
    l0: '', // the student's first lines, typed
    l1: '',
    q: '', // the question, typed
    qGone: false, // the answer, in its place
    asked: false, // sent: the line dims while the AI thinks
    heading: 0, // words of the heading shown
    line: 0, // words of the line under it
    figure: false, // the figure that walks the answer, there
    rows: -1, // -1 no table yet, 0 its header, n its rows
    ink: false, // the answer's words in ink, until it is written
    keys: false, // Ctrl+Enter on show
    pressed: null, // null, 'ctrl' or 'both'
    caret: 'l0', // 'l0', 'l1', 'q', 'after' or null
    lit: null, // the line the keys go on: 'q'
  }
}
const s = reactive(initial())

const words = (text) => text.split(' ')
const headingWords = computed(() => words(props.demo.answer.heading))
const lineWords = computed(() => words(props.demo.answer.line))

// ---- Playing ----
const playing = ref(false)
const finished = ref(false)
const reduced = ref(false)
let run = 0
let started = false

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

// Ctrl+Enter, as a product demo shows a key press: a pill near the bottom of the note, its keys
// going down one after the other, the line they go on lit while it shows, then the pill out.
async function ctrlEnter(key) {
  s.caret = null
  s.lit = key
  s.keys = true
  await wait(640)
  s.pressed = 'ctrl'
  await wait(110)
  s.pressed = 'both'
  await wait(150)
  s.pressed = null
  await wait(240)
  s.keys = false
  s.lit = null
  await wait(240)
}

async function scene() {
  const d = props.demo
  await wait(600)
  await type('l0', d.lines[0])
  await wait(500)
  await type('l1', d.lines[1])
  await wait(800)

  // A question in the middle of the note, and Ctrl+Enter on its line.
  await type('q', d.question)
  await wait(600)
  await ctrlEnter('q')

  // The question stays, dimmed, while the AI thinks; then the answer takes its place: the heading
  // and the line word by word, in ink, then the figure that walks it, then the table's rows.
  s.asked = true
  await wait(700)
  s.qGone = true
  s.asked = false
  s.ink = true
  await nextTick()
  for (let i = 1; i <= headingWords.value.length; i++) {
    s.heading = i
    await wait(85)
  }
  for (let i = 1; i <= lineWords.value.length; i++) {
    s.line = i
    await wait(70)
  }
  await wait(320)
  s.figure = true
  await nextTick()
  revealTop('figure')
  await wait(1000)
  for (let i = 0; i <= d.answer.rows.length; i++) {
    s.rows = i
    await nextTick()
    reveal('table')
    await wait(380)
  }
  // The answer is written: the ink dries into the note's own colour, as it does in the app.
  s.ink = false
  await wait(1400)

  // The student goes on writing under it.
  s.caret = 'after'
  await nextTick()
  reveal('after')
}

function showEnd() {
  const d = props.demo
  Object.assign(s, {
    ...initial(),
    l0: d.lines[0],
    l1: d.lines[1],
    qGone: true,
    heading: headingWords.value.length,
    line: lineWords.value.length,
    figure: true,
    rows: d.answer.rows.length,
    caret: null,
  })
}

async function play() {
  started = true
  if (reduced.value) return showEnd()
  finished.value = false
  playing.value = true
  const mine = ++run
  try {
    await scene()
  } catch (e) {
    if (!(e instanceof Cancelled)) throw e
    return
  }
  if (mine !== run) return
  playing.value = false
  finished.value = true
}

function restart() {
  run++
  playing.value = false
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
  // Room under what just came in, so the note never reads as stuck to the bottom edge.
  const margin = 96
  let top = box.scrollTop
  if (r.bottom > b.bottom - margin) top += r.bottom - b.bottom + margin
  if (r.top - (top - box.scrollTop) < b.top + margin) top = box.scrollTop + r.top - b.top - margin
  box.scrollTo({ top, behavior: reduced.value ? 'auto' : 'smooth' })
}

// A piece taller than the note's own screen (the figure on a phone): its first part comes to the
// top, so the flow is read from where it starts.
function revealTop(name) {
  const box = screen.value
  const el = refs[name]
  if (!box || !el) return
  const b = box.getBoundingClientRect()
  const r = el.getBoundingClientRect()
  box.scrollTo({ top: box.scrollTop + r.top - b.top - 28, behavior: reduced.value ? 'auto' : 'smooth' })
}

// ---- Starting where it is looked at ----
const root = ref(null)
let observer = null

onMounted(() => {
  reduced.value =
    document.documentElement.dataset.motion === 'none' ||
    (document.documentElement.dataset.motion !== 'full' && matchMedia('(prefers-reduced-motion: reduce)').matches)
  // Reduced motion: the scene shows its end, and plays only when asked.
  if (reduced.value) {
    showEnd()
    return
  }
  observer = new IntersectionObserver(
    ([entry]) => {
      const seen = entry.intersectionRect.height
      const whole = Math.min(entry.boundingClientRect.height, window.innerHeight)
      if (seen >= whole * 0.6 && !finished.value) {
        if (!started) play()
        else playing.value = true
      } else if (seen < whole * 0.25 && playing.value) {
        playing.value = false
      }
    },
    { threshold: [0, 0.25, 0.6, 1] },
  )
  observer.observe(root.value)
})

onBeforeUnmount(() => {
  run++
  observer?.disconnect()
})

// A new language starts the scene over in that language.
watch(
  () => props.demo,
  () => {
    if (reduced.value) return showEnd()
    if (started) startAgain()
    else restart()
  },
)

// A line's text in pieces, its arrows drawn as the library's arrow icon.
const pieces = (text) => text.split(/(→)/).filter(Boolean)
</script>

<template>
  <div ref="root" class="mx-auto flex w-full max-w-[54rem] flex-col items-center gap-3">
    <!-- One note on a calm surface, as the app draws it. Watched, not used: it plays by itself. -->
    <div class="w-full rounded-[2rem] bg-bg-muted/50 p-3 sm:p-5">
      <div
        class="relative flex h-[28rem] flex-col overflow-hidden rounded-[1.75rem] border border-border bg-bg shadow-[0_18px_40px_-24px_rgb(0_0_0/0.35)] sm:h-[36rem]"
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

        <div ref="screen" class="note-scroll min-h-0 flex-1 overflow-y-auto scrollbar-none px-6 pt-8 pb-40 sm:px-10 sm:pt-10">
          <p class="m-0 mb-8 text-display text-fg">{{ demo.title }}</p>
          <Prose class="note-body">
            <!-- The student's lines, typed as the class goes on. -->
            <template v-for="key in ['l0', 'l1']" :key="key">
              <p v-if="s[key] || s.caret === key" :ref="setRef(key)">
                <template v-for="(part, j) in pieces(s[key])" :key="j">
                  <span v-if="part === '→'" class="inline-arrow">→</span><template v-else>{{ part }}</template>
                </template><span v-if="s.caret === key" class="note-caret" :class="playing && 'note-caret--typing'" />
              </p>
            </template>

            <!-- A question, typed; sent, it dims while the AI thinks and the answer takes its
                 place. -->
            <template v-if="!s.qGone">
              <p
                v-if="s.q || s.caret === 'q'"
                :ref="setRef('q')"
                class="note-line"
                :class="{ 'note-line--lit': s.lit === 'q', 'note-line--asked': s.asked }"
              >{{ s.q }}<span v-if="s.caret === 'q'" class="note-caret" :class="playing && 'note-caret--typing'" /></p>
            </template>
            <template v-else>
              <h2 v-if="s.heading"><template v-for="(word, i) in headingWords.slice(0, s.heading)" :key="i"><span :class="{ ink: s.ink }" :style="{ '--ink-flow': inkFlow(i) }">{{ word }}</span>{{ ' ' }}</template></h2>
              <p v-if="s.line"><template v-for="(word, i) in lineWords.slice(0, s.line)" :key="i"><span :class="{ ink: s.ink }" :style="{ '--ink-flow': inkFlow(i) }">{{ word }}</span>{{ ' ' }}</template></p>
              <div v-if="s.figure" :ref="setRef('figure')" class="not-prose my-6" :class="!reduced && 'animate-blur-in'">
                <Diagram :label="demo.answer.figure.label" class="w-full">
                  <p class="figure-title">{{ demo.answer.figure.title }}</p>
                  <DiagramGroup layout="row" class="w-full justify-between">
                    <DiagramChip :icon="User" :color="COLORS.url"><span class="whitespace-nowrap">{{ demo.answer.figure.you }}</span></DiagramChip>
                    <DiagramArrow :label="demo.answer.figure.arrows[0]" />
                    <DiagramChip :icon="Globe"><span class="whitespace-nowrap">{{ demo.answer.figure.network }}</span></DiagramChip>
                    <DiagramArrow :label="demo.answer.figure.arrows[1]" />
                    <DiagramChip :icon="Cpu" :color="COLORS.render"><span class="whitespace-nowrap">{{ demo.answer.figure.render }}</span></DiagramChip>
                    <DiagramArrow :label="demo.answer.figure.arrows[2]" />
                    <DiagramChip :icon="Monitor" :color="COLORS.screen"><span class="whitespace-nowrap">{{ demo.answer.figure.screen }}</span></DiagramChip>
                  </DiagramGroup>
                </Diagram>
              </div>
              <div v-if="s.rows >= 0" :ref="setRef('table')" class="not-prose my-5">
                <Table :aria-label="demo.answer.label">
                  <TableHeader :class="!reduced && 'animate-blur-in'">
                    <TableRow>
                      <TableHead v-for="(head, i) in demo.answer.head" :key="i">{{ head }}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow
                      v-for="row in demo.answer.rows.slice(0, s.rows)"
                      :key="row[0]"
                      :class="!reduced && 'animate-blur-in'"
                    >
                      <TableCell class="text-fg"><RichText :text="row[0]" /></TableCell>
                      <TableCell><RichText :text="row[1]" /></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </template>

            <p v-if="s.caret === 'after'" :ref="setRef('after')"><span class="note-caret" /></p>
          </Prose>
        </div>

        <!-- Ctrl+Enter, as product demos show a key press. -->
        <Transition name="keys">
          <div v-if="s.keys" class="keys">
            <kbd :class="{ 'key--down': s.pressed === 'ctrl' || s.pressed === 'both' }"><span aria-hidden="true">⌃</span>{{ demo.keys[0] }}</kbd>
            <kbd :class="{ 'key--down': s.pressed === 'both' }">{{ demo.keys[1] }}<span aria-hidden="true">↵</span></kbd>
          </div>
        </Transition>
      </div>
    </div>

    <Button
      variant="ghost"
      size="icon"
      class="rounded-full text-fg-muted"
      :icon="RotateCcw"
      :aria-label="libraryLabels.restart"
      @click="startAgain"
    />
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

/* The figure's title, above what it walks. */
.figure-title {
  margin: 0 0 1rem;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-fg);
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

/* The AI's words land in ink and dry into the text's colour, as the app writes them (elastic-ui's
   ink-wave, and the class off once the answer is written, as the app does). */
.ink {
  display: inline-block;
  animation: ink-wave 1700ms cubic-bezier(0.4, 0, 0.2, 1) both;
}

/* The line Ctrl+Enter goes on is lit while the pill shows; a question, sent, dims while the AI
   thinks. A soft band, the text where it was: no shift. */
.note-line {
  margin-inline: -0.5rem;
  padding-inline: 0.5rem;
  border-radius: 0.5rem;
  transition:
    background-color 260ms var(--ease-soft),
    opacity 300ms var(--ease-soft);
}
.note-line--lit {
  background-color: color-mix(in oklab, var(--color-fg) 5%, transparent);
}
.note-line--asked {
  opacity: 0.55;
}

/* Ctrl+Enter, as a product demo shows a key press: a dark pill floating near the bottom of the
   note, its keys going down in turn. */
.keys {
  position: absolute;
  left: 50%;
  bottom: 1.5rem;
  display: flex;
  gap: 0.5rem;
  padding: 0.55rem;
  border-radius: 1.1rem;
  background: rgb(24 24 27 / 0.86);
  box-shadow:
    0 12px 32px -12px rgb(0 0 0 / 0.55),
    inset 0 1px 0 rgb(255 255 255 / 0.08);
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
  transform: translateX(-50%);
  pointer-events: none;
}
.keys kbd {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-width: 3rem;
  padding: 0.5rem 0.8rem;
  border-radius: 0.65rem;
  font-family: var(--font-sans);
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  color: #fafafa;
  background: rgb(255 255 255 / 0.1);
  box-shadow:
    inset 0 -2px 0 rgb(0 0 0 / 0.25),
    inset 0 1px 0 rgb(255 255 255 / 0.14);
  transition:
    transform 100ms var(--ease-soft),
    background-color 100ms var(--ease-soft),
    box-shadow 100ms var(--ease-soft);
}
.keys kbd.key--down {
  transform: translateY(1px) scale(0.96);
  background: rgb(255 255 255 / 0.2);
  box-shadow: inset 0 1px 3px rgb(0 0 0 / 0.45);
}
.keys-enter-active {
  animation: keys-in 240ms cubic-bezier(0.2, 0.7, 0.3, 1) both;
}
.keys-leave-active {
  transition:
    opacity 220ms var(--ease-soft),
    transform 220ms var(--ease-soft);
}
.keys-leave-to {
  opacity: 0;
  transform: translate(-50%, 6px) scale(0.98);
}
@keyframes keys-in {
  from {
    opacity: 0;
    transform: translate(-50%, 10px) scale(0.94);
  }
}

@media (prefers-reduced-motion: reduce) {
  .note-caret,
  .ink,
  .keys-enter-active {
    animation: none;
  }
  .note-line {
    transition: none;
  }
}
</style>
