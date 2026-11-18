<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Pause, Play } from '@lucide/vue'
import {
  Button,
  Diagram,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TextMorph,
  inkFlow,
} from 'elastic-ui'

// The AI in a note, as three short scenes, one idea each, played on a loop: a question becomes
// notes in its place (the student keeps writing under it while they arrive), a rough line of
// their own gets a diagram drawn by hand under it, and a real thing gets a photo. Each answer
// comes in as the app writes it: words in ink drying into the text's colour, a table coming into
// focus, a diagram drawn stroke by stroke. A caption says each scene's idea; the pills on top say
// where it is and jump to a scene. It starts once in view and pauses out of it; under reduced
// motion each scene shows its end. Made up; `reel` holds its texts, in each language.
const props = defineProps({ reel: { type: Object, required: true } })

const scene = ref(0)
const playing = ref(false)
const progress = ref(0) // 0..1 through the current scene
const reduced = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches

// What the note shows at a moment of a scene.
const typed = ref('') // the line being typed
const pressed = ref(false) // Ctrl+Enter, on show
const asked = ref(false) // the line has been sent: it dims, waiting
const status = ref('') // "Looking for an image…"
const words = ref(0) // the answer's words shown
const rows = ref(0) // the table's rows shown
const drawn = ref(false) // the diagram, there
const photo = ref(false) // the photo, there
const after = ref('') // what the student goes on writing, under it

const s = computed(() => props.reel.scenes[scene.value])
const answerWords = computed(() => (s.value.answer ? s.value.answer.split(' ') : []))

let timers = []
let started = 0
let frame = 0
const DURATIONS = [10500, 8000, 9000]
const wait = (ms) => new Promise((resolve) => timers.push(setTimeout(resolve, ms)))

function reset() {
  timers.forEach(clearTimeout)
  timers = []
  typed.value = ''
  pressed.value = false
  asked.value = false
  status.value = ''
  words.value = 0
  rows.value = 0
  drawn.value = false
  photo.value = false
  after.value = ''
}

function showEnd() {
  const sc = s.value
  typed.value = sc.line
  asked.value = sc.kind !== 'complete'
  words.value = answerWords.value.length
  rows.value = sc.table ? sc.table.rows.length : 0
  drawn.value = sc.kind === 'complete'
  photo.value = sc.kind === 'photo'
  after.value = sc.after ?? ''
}

async function type(target, text, speed = 45) {
  for (let i = 1; i <= text.length; i++) {
    target.value = text.slice(0, i)
    await wait(speed + (text[i - 1] === ' ' ? 30 : 0))
  }
}

async function play(index) {
  reset()
  scene.value = index
  started = performance.now()
  if (reduced) {
    showEnd()
    return
  }
  const sc = s.value
  const run = scene.value
  const live = () => run === scene.value && playing.value
  await wait(500)
  await type(typed, sc.line)
  await wait(450)
  pressed.value = true
  await wait(500)
  pressed.value = false
  if (sc.kind !== 'complete') asked.value = true
  if (sc.kind === 'photo') status.value = props.reel.searching
  // The student goes on at once, under it, while the answer comes.
  if (sc.after) type(after, sc.after, 70)
  await wait(sc.kind === 'photo' ? 1300 : 700)
  status.value = ''
  if (!live()) return
  if (sc.kind === 'complete') {
    drawn.value = true
  } else {
    for (let i = 1; i <= answerWords.value.length; i++) {
      words.value = i
      await wait(85)
    }
    if (sc.table) {
      for (let r = 1; r <= sc.table.rows.length; r++) {
        rows.value = r
        await wait(260)
      }
    }
    if (sc.kind === 'photo') photo.value = true
  }
}

function tick() {
  if (playing.value && !reduced) {
    progress.value = Math.min(1, (performance.now() - started) / DURATIONS[scene.value])
    if (progress.value >= 1) play((scene.value + 1) % props.reel.scenes.length)
  }
  frame = requestAnimationFrame(tick)
}

function go(index) {
  progress.value = 0
  play(index)
}

function toggle() {
  playing.value = !playing.value
  if (playing.value) go(scene.value)
}

// It starts once in view and pauses out of it.
const root = ref(null)
let observer
onMounted(() => {
  frame = requestAnimationFrame(tick)
  if (reduced) return showEnd()
  observer = new IntersectionObserver(
    ([entry]) => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.5 && !playing.value) {
        playing.value = true
        go(scene.value)
      } else if (!entry.isIntersecting && playing.value) {
        playing.value = false
      }
    },
    { threshold: [0, 0.5, 1] },
  )
  observer.observe(root.value)
})
onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(frame)
  timers.forEach(clearTimeout)
})
</script>

<template>
  <div ref="root" class="flex flex-col gap-5">
    <!-- Where it is: three scenes, the one on show filling as it plays. -->
    <div class="flex items-center gap-2">
      <button
        v-for="(sc, i) in reel.scenes"
        :key="i"
        type="button"
        class="pill relative overflow-hidden rounded-full px-3 py-1.5 text-sm transition-colors"
        :class="i === scene ? 'bg-bg-muted text-fg' : 'text-fg-muted hover:text-fg'"
        :aria-current="i === scene ? 'step' : undefined"
        @click="go(i)"
      >
        <span class="relative z-10">{{ i + 1 }} · {{ sc.pill }}</span>
        <span v-if="i === scene" class="fill absolute inset-y-0 left-0" :style="{ width: `${progress * 100}%` }" />
      </button>
      <Button
        variant="ghost"
        size="icon"
        class="ml-auto"
        :icon="playing ? Pause : Play"
        :aria-label="playing ? reel.pause : reel.play"
        @click="toggle"
      />
    </div>

    <!-- The scene's idea, in a sentence. -->
    <p class="m-0 text-xl font-semibold text-fg"><TextMorph :text="s.caption" /></p>

    <!-- The note. -->
    <div class="note rounded-2xl bg-bg-muted p-6 text-[15px] leading-relaxed text-fg-secondary sm:p-8">
      <p class="m-0 mb-1 text-xs text-fg-muted">{{ reel.noteTitle }}</p>
      <p class="m-0 mb-4 text-lg font-semibold text-fg">{{ s.title }}</p>
      <p class="m-0 mb-3">{{ s.before }}</p>

      <!-- The line typed, and Ctrl+Enter on it. A question waits dimmed, then its notes take its
           place; the student's own line stays. -->
      <p
        v-if="!(s.kind !== 'complete' && words > 0)"
        class="m-0 mb-3 transition-opacity duration-300"
        :class="asked && 'opacity-55'"
      >
        {{ typed }}<span v-if="!asked && !drawn && typed.length < s.line.length + 1 && !pressed" class="caret" />
        <span class="keys" :class="pressed && 'on'" aria-hidden="true"><kbd>Ctrl</kbd><kbd>{{ reel.enter }}</kbd></span>
      </p>
      <p v-if="status" class="m-0 mb-3 text-fg-muted shimmer">{{ status }}</p>

      <!-- The answer, in ink: each word lands in an aurora colour and dries into the text's. -->
      <template v-if="s.kind !== 'complete' && words > 0">
        <p class="m-0 mb-2 mt-4 text-lg font-semibold text-fg">
          <span class="ink" :style="{ '--ink-flow': inkFlow(0) }">{{ s.heading }}</span>
        </p>
        <p class="m-0 mb-3">
          <template v-for="(w, i) in answerWords.slice(0, words)" :key="i">
            <span class="ink" :style="{ '--ink-flow': inkFlow(i + 1) }">{{ w }}</span>{{ ' ' }}
          </template>
        </p>
        <Table v-if="s.table && rows > 0" class="mb-3 appear">
          <TableHeader>
            <TableRow><TableHead v-for="c in s.table.columns" :key="c">{{ c }}</TableHead></TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-for="(r, i) in s.table.rows.slice(0, rows)" :key="i" class="appear">
              <TableCell v-for="(cell, j) in r" :key="j">{{ cell }}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
        <figure v-if="photo" class="m-0 mb-3 appear">
          <img :src="s.photo.src" :alt="s.photo.alt" class="max-h-64 w-auto max-w-full rounded-xl" loading="lazy" />
          <figcaption class="mt-2 text-sm italic text-fg-muted">{{ s.photo.credit }}</figcaption>
        </figure>
      </template>

      <!-- A diagram under the student's own line, drawn by hand, stroke by stroke. -->
      <Diagram v-if="drawn" ink :label="s.figure.label" class="mb-3">
        <DiagramGroup>
          <DiagramGroup layout="column">
            <DiagramChip v-for="c in s.figure.many" :key="c" color="#7c3aed">{{ c }}</DiagramChip>
          </DiagramGroup>
          <DiagramArrow :label="s.figure.arrow" />
          <DiagramChip color="var(--color-success)" :note="s.figure.note">{{ s.figure.one }}</DiagramChip>
        </DiagramGroup>
      </Diagram>

      <!-- The student goes on, under it. -->
      <p v-if="after" class="m-0 mt-3 text-fg">{{ after }}<span class="caret" /></p>
    </div>
  </div>
</template>

<style scoped>
.caret {
  display: inline-block;
  width: 1.5px;
  height: 1.1em;
  margin-left: 1px;
  vertical-align: -0.2em;
  background: var(--color-fg);
  animation: blink 1s steps(1) infinite;
}
@keyframes blink {
  50% {
    opacity: 0;
  }
}

.keys {
  display: inline-flex;
  gap: 4px;
  margin-left: 10px;
  vertical-align: 0.1em;
  opacity: 0;
  transform: translateY(4px) scale(0.9);
  transition:
    opacity 200ms ease,
    transform 200ms ease;
}
.keys.on {
  opacity: 1;
  transform: none;
}
.keys kbd {
  padding: 2px 7px;
  border-radius: 6px;
  font: 600 12px/1.4 var(--font-sans);
  background: var(--color-surface-raised, var(--color-bg));
  color: var(--color-fg);
  box-shadow: inset 0 -2px 0 color-mix(in oklab, var(--color-fg) 15%, transparent);
}
.keys.on kbd {
  animation: press 450ms ease;
}
@keyframes press {
  40% {
    transform: translateY(2px);
    box-shadow: none;
  }
}

/* The words land in ink and dry, as the app writes them (elastic-ui's ink-wave). */
.ink {
  display: inline-block;
  animation: ink-wave 1700ms cubic-bezier(0.4, 0, 0.2, 1) both;
}
.appear {
  animation: blur-in 700ms ease-out both;
}
.shimmer {
  animation: breathe 1.4s ease-in-out infinite;
}
@keyframes breathe {
  50% {
    opacity: 0.45;
  }
}
.fill {
  background: color-mix(in oklab, var(--color-fg) 9%, transparent);
  transition: width 120ms linear;
}

@media (prefers-reduced-motion: reduce) {
  .ink,
  .appear,
  .shimmer,
  .caret,
  .keys.on kbd {
    animation: none;
  }
}
</style>
