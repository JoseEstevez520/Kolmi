<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { Code, Server } from '@lucide/vue'
import {
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

// The AI in a note, played back as one scene with what the app really returned (2026-11-21): just
// the note, no app around it. A student asks "What is an API?" and presses Ctrl+Enter (a key press
// in a floating pill); the line dims while the AI thinks and the answer takes its place: a heading,
// a definition in ink, a figure of a request and its response, an analogy. Then the student asks
// "GraphQL vs REST API" and gets a comparison table, row by row, and a summary. Nothing moves the
// view, so each answer is seen as it is generated. It starts once in view, pauses when it leaves,
// and plays again by itself after a pause. Under reduced motion it shows the end, still.
// `demo` holds the texts, in each language.
const props = defineProps({
  demo: { type: Object, required: true },
})

// The figure's colours, from the app's figure palette: violet for your app, green for the service.
const COLORS = { app: '#7c3aed', service: 'var(--color-success)' }

// A line as words that keep their bold, italics and code. The whole line is laid out from its first
// word, and the words not written yet are only invisible, so nothing moves or rewraps while the
// answer streams in.
function tokens(text) {
  const out = []
  for (const part of text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/).filter(Boolean)) {
    let tag = null
    let body = part
    if (part.startsWith('**')) (tag = 'strong'), (body = part.slice(2, -2))
    else if (part.startsWith('`')) (tag = 'code'), (body = part.slice(1, -1))
    else if (part.startsWith('*') && part.length > 2) (tag = 'em'), (body = part.slice(1, -1))
    for (const piece of body.split(/(\s+)/)) {
      if (!piece) continue
      if (/^\s+$/.test(piece)) out.push({ space: true, text: piece })
      else out.push({ tag, text: piece })
    }
  }
  return out
}
const words = (text) => tokens(text).filter((t) => !t.space)

// ---- What the note shows at any moment ----
function step() {
  return {
    q: '', // the question, typed
    asked: false, // sent: the line dims while the AI thinks
    gone: false, // the answer, in its place
    heading: 0, // words of the heading shown
    line: 0, // words of the line under it
    figure: false, // the figure, there
    rows: -1, // -1 no table yet, 0 its header, n its rows
    after: 0, // words of the closing line shown
  }
}
function initial() {
  return {
    steps: props.demo.steps.map(step),
    ink: -1, // the step whose answer is being written in ink
    keys: false, // Ctrl+Enter on show
    pressed: null, // null, 'ctrl' or 'both'
    caret: null, // { step, at: 'q' } or 'end'
    lit: -1, // the step whose line the keys go on
  }
}
const s = reactive(initial())

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

// Types like a person: an uneven pace, a pause after a word now and then.
async function type(i, text) {
  s.caret = { step: i }
  for (const ch of text) {
    s.steps[i].q += ch
    await wait(ch === ' ' ? 70 + Math.random() * 90 : 38 + Math.random() * 45)
  }
}

// Ctrl+Enter, as a product demo shows a key press: a pill near the bottom of the note, its keys
// going down one after the other, the line they go on lit while it shows, then the pill out.
async function ctrlEnter(i) {
  s.caret = null
  s.lit = i
  s.keys = true
  await wait(640)
  s.pressed = 'ctrl'
  await wait(110)
  s.pressed = 'both'
  await wait(150)
  s.pressed = null
  await wait(240)
  s.keys = false
  s.lit = -1
  await wait(240)
}

// Shows a line word by word, at the pace the app writes.
async function write(i, key, text, pace = 55) {
  const n = words(text).length
  for (let k = 1; k <= n; k++) {
    s.steps[i][key] = k
    await wait(pace)
  }
}

async function ask(i) {
  const d = props.demo.steps[i]
  const st = s.steps[i]
  if (i > 0) await makeRoom(i)
  await type(i, d.question)
  await wait(500)
  await ctrlEnter(i)
  // The question stays, dimmed, while the AI thinks; then the answer takes its place, in ink.
  st.asked = true
  await wait(800)
  st.gone = true
  st.asked = false
  s.ink = i
  await nextTick()
  await write(i, 'heading', d.heading, 90)
  if (d.line) await write(i, 'line', d.line, 45)
  if (d.figure) {
    await wait(300)
    st.figure = true
    await wait(900)
  }
  if (d.rows) {
    await wait(200)
    for (let k = 0; k <= d.rows.length; k++) {
      st.rows = k
      await wait(380)
    }
  }
  if (d.after) {
    await wait(200)
    await write(i, 'after', d.after, 45)
  }
  // The answer is written: the ink dries into the note's own colour, as it does in the app.
  await wait(500)
  s.ink = -1
}

async function scene() {
  await wait(700)
  for (let i = 0; i < props.demo.steps.length; i++) {
    await ask(i)
    await wait(1100)
  }
  s.caret = 'end'
}

function showEnd() {
  Object.assign(s, initial())
  s.steps = props.demo.steps.map((d) => ({
    q: d.question,
    asked: false,
    gone: true,
    heading: words(d.heading).length,
    line: d.line ? words(d.line).length : 0,
    figure: !!d.figure,
    rows: d.rows ? d.rows.length : -1,
    after: d.after ? words(d.after).length : 0,
  }))
}

async function play() {
  started = true
  if (reduced.value) return showEnd()
  finished.value = false
  playing.value = true
  const mine = ++run
  try {
    await scene()
    // The note stays a moment, finished, and the scene starts again by itself (no replay button).
    await wait(3500)
  } catch (e) {
    if (!(e instanceof Cancelled)) throw e
    return
  }
  if (mine !== run) return
  startAgain()
}

function restart() {
  run++
  playing.value = false
  finished.value = false
  Object.assign(s, initial())
  anchor = 0
  scroller.value?.scrollTo({ top: 0 })
}

function startAgain() {
  restart()
  play()
}

// ---- Keeping the newest line in view ----
// The note has a fixed height and scrolls inside, so it never takes half the page: as the answer
// grows, the note follows its end.
// The scroll looks ahead: before a new question is typed, the note glides so that line sits near the
// top, with room under it, so the answer grows into empty space instead of pushing the note up word
// by word. Only if an answer gets longer than that room does the note follow its end. One eased
// loop does the moving: each frame closes a part of the distance, so it glides and never jumps.
const scroller = ref(null)
const spacer = ref(null)
const FOLLOW = 0.07 // share of the distance covered per frame
const ROOM = 40 // px kept under the last line when following the end
const AHEAD = 28 // px left above a new question when the note makes room for it
let anchor = 0
let following = 0
function follow() {
  const el = scroller.value
  if (el && playing.value) {
    const end = el.scrollHeight - (spacer.value?.offsetHeight ?? 0) + ROOM - el.clientHeight
    const target = Math.min(Math.max(anchor, end), el.scrollHeight - el.clientHeight)
    const gap = target - el.scrollTop
    if (Math.abs(gap) > 0.5) el.scrollTop += gap * FOLLOW
  }
  following = requestAnimationFrame(follow)
}

// Makes room for step i's question: its line goes near the top of the note.
async function makeRoom(i) {
  const el = scroller.value
  if (!el) return
  s.caret = { step: i }
  await nextTick()
  const line = el.querySelector(`[data-q="${i}"]`)
  if (!line) return
  anchor = Math.max(0, line.getBoundingClientRect().top - el.getBoundingClientRect().top + el.scrollTop - AHEAD)
  await wait(900)
}

// ---- Starting where it is looked at ----
const root = ref(null)
let observer = null

onMounted(() => {
  following = requestAnimationFrame(follow)
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
  cancelAnimationFrame(following)
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

// A line while it is written: every word in place, the first `n` shown, each landing in ink.
function laid(text, n) {
  let k = 0
  return tokens(text).map((t) => (t.space ? t : { ...t, k, on: k++ < n }))
}
</script>

<template>
  <div ref="root" class="mx-auto flex w-full max-w-[46rem] flex-col items-center gap-3">
    <!-- Just the note, on a calm sheet. Watched, not used: it plays by itself. -->
    <div class="sheet w-full overflow-hidden rounded-[2rem] bg-bg" aria-hidden="true" inert>
      <div ref="scroller" class="note-scroll h-[26rem] overflow-y-auto scrollbar-none px-7 pt-8 pb-24 sm:h-[30rem] sm:px-12 sm:pt-10">
        <p class="m-0 mb-8 text-display text-fg">{{ demo.title }}</p>
        <Prose class="note-body">
          <template v-for="(d, i) in demo.steps" :key="i">
            <!-- The question, typed; sent, it dims while the AI thinks and the answer takes its
                 place. -->
            <p
              v-if="!s.steps[i].gone && (s.steps[i].q || s.caret?.step === i)"
              :data-q="i"
              class="note-line"
              :class="{ 'note-line--lit': s.lit === i, 'note-line--asked': s.steps[i].asked }"
            >{{ s.steps[i].q }}<span v-if="s.caret?.step === i" class="note-caret" :class="playing && 'note-caret--typing'" /></p>

            <template v-if="s.steps[i].gone">
              <h2 v-if="s.steps[i].heading">
                <template v-for="(t, j) in laid(d.heading, s.steps[i].heading)" :key="j"><template v-if="t.space">{{ t.text }}</template><span v-else class="word" :class="{ off: !t.on, ink: t.on && s.ink === i }" :style="{ '--ink-flow': inkFlow(t.k) }">{{ t.text }}</span></template>
              </h2>
              <p v-if="d.line && s.steps[i].line">
                <template v-for="(t, j) in laid(d.line, s.steps[i].line)" :key="j"><template v-if="t.space">{{ t.text }}</template><component :is="t.tag === 'code' ? 'code' : t.tag || 'span'" v-else class="word" :class="{ off: !t.on, ink: t.on && s.ink === i, 'inline-code': t.tag === 'code' }" :style="{ '--ink-flow': inkFlow(t.k) }">{{ t.text }}</component></template>
              </p>
              <div v-if="d.figure && s.steps[i].figure" class="not-prose my-6" :class="!reduced && 'animate-blur-in'">
                <Diagram :label="d.figure.label" class="w-full">
                  <DiagramGroup layout="row" class="w-full flex-wrap justify-start gap-y-2">
                    <DiagramChip :icon="Code" :color="COLORS.app"><span class="whitespace-nowrap"><strong>{{ d.figure.app }}</strong> · {{ d.figure.appNote }}</span></DiagramChip>
                    <DiagramArrow :label="d.figure.arrow" />
                    <DiagramChip :icon="Server" :color="COLORS.service"><span class="whitespace-nowrap"><strong>{{ d.figure.service }}</strong> · {{ d.figure.serviceNote }}</span></DiagramChip>
                  </DiagramGroup>
                </Diagram>
              </div>
              <div v-if="d.rows && s.steps[i].rows >= 0" class="not-prose my-5">
                <Table :aria-label="d.label">
                  <TableHeader :class="!reduced && 'animate-blur-in'">
                    <TableRow>
                      <TableHead v-for="(head, k) in d.head" :key="k">{{ head }}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow v-for="row in d.rows.slice(0, s.steps[i].rows)" :key="row[0]" :class="!reduced && 'animate-blur-in'">
                      <TableCell class="text-fg"><RichText :text="row[0]" /></TableCell>
                      <TableCell><RichText :text="row[1]" /></TableCell>
                      <TableCell><RichText :text="row[2]" /></TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
              <p v-if="d.after && s.steps[i].after">
                <template v-for="(t, j) in laid(d.after, s.steps[i].after)" :key="j"><template v-if="t.space">{{ t.text }}</template><component :is="t.tag === 'code' ? 'code' : t.tag || 'span'" v-else class="word" :class="{ off: !t.on, ink: t.on && s.ink === i, 'inline-code': t.tag === 'code' }" :style="{ '--ink-flow': inkFlow(t.k) }">{{ t.text }}</component></template>
              </p>
            </template>
          </template>

          <p v-if="s.caret === 'end'"><span class="note-caret" /></p>
        </Prose>
        <!-- Empty room under the note, so a new question can be brought near the top. -->
        <div ref="spacer" class="h-[22rem] sm:h-[26rem]" />
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
</template>

<style scoped>
/* The note's own scroll fades at its top and bottom edges. */
.note-scroll {
  mask-image: linear-gradient(to bottom, transparent, #000 1.5rem, #000 calc(100% - 3rem), transparent);
}

/* The sheet the note sits on: no app around it, only a soft edge. */
.sheet {
  position: relative;
  box-shadow: 0 0 0 1px var(--color-border);
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
  width: 1.5px;
  height: 1.05em;
  margin-left: 1px;
  border-radius: 1px;
  vertical-align: -0.12em;
  background: var(--caret, #e0a43a);
  animation: note-blink 1.2s ease-in-out infinite;
}
.note-caret--typing {
  animation: none;
}
@keyframes note-blink {
  0%,
  45% {
    opacity: 1;
  }
  60%,
  85% {
    opacity: 0.15;
  }
}

/* Every word is its own box from the start and keeps it: written or not, in ink or dry, the line
   never rewraps. Words not written yet only hide. */
.word {
  display: inline-block;
}
.word.off {
  visibility: hidden;
}
.inline-code {
  border-radius: 0.25rem;
  background: var(--color-bg-muted);
  padding: 0.15em 0.35em;
  font-family: var(--font-mono);
  font-size: 0.875em;
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
