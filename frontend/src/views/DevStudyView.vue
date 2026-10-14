<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Button,
  Card,
  CardContent,
  Carousel,
  CarouselItem,
  CodeBlock,
  Diagram,
  DiagramArea,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  LogoList,
  LogoListItem,
  Status,
  Textarea,
  ThemeToggle,
  ToggleGroup,
  ToggleGroupItem,
} from 'elastic-ui'
import {
  ArrowUpRight,
  Ban,
  Check,
  Equal,
  Lock,
  ChevronRight,
  Clock,
  Play,
  RefreshCw,
  RotateCcw,
  Undo2,
  SquareTerminal,
  Repeat,
  Square,
  Braces,
  Box,
  X,
} from '@lucide/vue'
import { logoFor } from '../lib/openui/logos.js'

// Development only (/dev/study): four ways a study page could look, on one topic ("var, let and
// const"), with the library's parts and fake local data. Nothing is fetched until a click.

// A. Logos
const stack = ['JavaScript', 'Node.js', 'Chrome', 'ESLint', 'Vue']

// B. Playground: editable code, run in a closed frame (scripts only, no network, no access to the
// page). The code goes in as its own inline script so a syntax error cannot break the capture.
const tries = [
  { id: 'before', label: 'Too early', icon: Clock, code: 'console.log(a)\nlet a = 1' },
  { id: 'const', label: 'Reassign', icon: Lock, code: 'const a = 1\na = 2\nconsole.log(a)' },
  { id: 'block', label: 'Block scope', icon: Square, code: 'if (true) {\n  var a = 1\n  let b = 2\n}\nconsole.log(a)\nconsole.log(b)' },
]
const start = 'var a = 1\nvar a = 2\nconsole.log(a)'
const code = ref(start)
// What "reset" restores: the starting code, or the variation last picked.
const base = ref(start)
// What the person had before a chip or "reset" replaced the text, kept one level deep for "back".
const previous = ref(null)
function replaceCode(next) {
  if (next === code.value) return
  previous.value = code.value
  code.value = next
}
const picked = computed({
  get: () => tries.find((t) => t.code === code.value)?.id ?? '',
  set: (id) => {
    const t = tries.find((x) => x.id === id)
    if (!t) return
    base.value = t.code
    replaceCode(t.code)
  },
})
function back() {
  if (previous.value === null) return
  const mine = previous.value
  previous.value = code.value
  code.value = mine
  runNow()
}
const lineNumbers = computed(() => Array.from({ length: code.value.split('\n').length }, (_, i) => i + 1).join('\n'))

// The code runs by itself 600 ms after the last key (Ctrl or Cmd+Enter runs at once), in a closed
// frame (scripts only, no network, no access to the page) that nobody sees; what it prints comes
// back by postMessage and is drawn here, in the console. The last output stays on screen while a
// new run collects, so half-written code never flashes an error. The code goes in as its own
// inline script so a syntax error cannot break the capture. A watchdog drops the frame if it does
// not report "done" in 2 s, and the output is capped.
const MAX_LINES = 200
const MAX_CHARS = 10000
const ran = ref('')
const runId = ref(0)
const lines = ref([])
let pending = []
let chars = 0
let finished = true
let timer
let watchdog
function schedule() {
  clearTimeout(timer)
  timer = setTimeout(runNow, 600)
}
function runNow() {
  clearTimeout(timer)
  clearTimeout(watchdog)
  pending = []
  chars = 0
  finished = false
  ran.value = code.value
  runId.value++
  watchdog = setTimeout(() => {
    runId.value = 0 // the frame goes away
    finished = true
    lines.value = [...pending, { text: 'stopped: it took too long', quiet: true }]
  }, 2000)
}
watch(code, schedule)
runNow()
onBeforeUnmount(() => {
  clearTimeout(timer)
  clearTimeout(watchdog)
})

function capture(id) {
  return `(() => {
  const ID = ${id}
  let n = 0
  const show = (v) => typeof v === 'string' ? v : v === undefined ? 'undefined'
    : v instanceof Error ? v.name + ': ' + v.message
    : typeof v === 'object' && v !== null ? (() => { try { return JSON.stringify(v) } catch { return String(v) } })()
    : String(v)
  const send = (text, bad) => { if (n++ < ${MAX_LINES + 1}) parent.postMessage({ kolmiConsole: true, id: ID, text, bad }, '*') }
  for (const k of ['log', 'info', 'warn', 'error']) console[k] = (...a) => send(a.map(show).join(' '), k === 'error')
  addEventListener('error', (e) => send(e.error ? show(e.error) : String(e.message).replace(/^Uncaught /, ''), true))
  window.__done = () => parent.postMessage({ kolmiConsole: true, id: ID, done: true }, '*')
})()`
}
function frameDoc(source, id) {
  const safe = source.replace(/<\/(script)/gi, '<\\/$1').replace(/<!--/g, '<\\!--')
  return `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'"><script>${capture(id)}<\/script><script>${safe}<\/script><script>__done()<\/script>`
}
const frame = computed(() => (runId.value ? frameDoc(ran.value, runId.value) : ''))
const sandbox = ref(null)
function add(line) {
  if (finished) lines.value = [...lines.value, line]
  else pending.push(line)
}
function onMessage(e) {
  const d = e.data
  if (!sandbox.value || e.source !== sandbox.value.contentWindow) return
  if (!d || d.kolmiConsole !== true || d.id !== runId.value) return
  if (d.done) {
    clearTimeout(watchdog)
    finished = true
    lines.value = pending
    return
  }
  const total = finished ? lines.value.length : pending.length
  if (total > MAX_LINES) return
  const text = String(d.text)
  chars += text.length
  if (total === MAX_LINES || chars > MAX_CHARS) {
    chars = Infinity
    if (!(finished ? lines.value : pending).some((l) => l.cut)) add({ text: 'output cut', quiet: true, cut: true })
    return
  }
  if (chars !== Infinity) add({ text: text.slice(0, 500), bad: d.bad === true })
}
onMounted(() => window.addEventListener('message', onMessage))
onBeforeUnmount(() => window.removeEventListener('message', onMessage))

// C. Media carousel (the player and the page only load after a click)
const slides = [
  { kind: 'video', title: 'Scope in five minutes', id: 'VIDEO_ID_1' },
  { kind: 'site', title: 'MDN: let', host: 'developer.mozilla.org', href: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/let' },
  { kind: 'video', title: 'Hoisting, explained', id: 'VIDEO_ID_2' },
  { kind: 'site', title: 'MDN: const', host: 'developer.mozilla.org', href: 'https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/const' },
]
const slide = ref(0)
const playing = ref({})
</script>

<template>
  <main class="mx-auto flex max-w-2xl flex-col gap-16 px-4 py-10">
    <div class="flex items-center text-meta text-fg-muted">
      Study page options
      <ThemeToggle class="ml-auto" />
    </div>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">A. Logos</h2>
      <div class="flex flex-col gap-4 rounded-xl bg-bg-muted p-6">
        <LogoList bare>
          <LogoListItem v-for="name in stack" :key="name" :icon="logoFor(name)" mono>{{ name }}</LogoListItem>
        </LogoList>
        <p class="m-0 text-copy text-fg-secondary">Three keywords declare a variable, and they differ in scope and in whether the value can change.</p>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">B. Playground</h2>
      <div class="flex flex-col gap-3 rounded-xl bg-bg-muted p-6">
        <ToggleGroup v-model="picked" type="single" aria-label="Try this" class="flex-wrap self-start">
          <ToggleGroupItem v-for="t in tries" :key="t.id" :value="t.id" class="gap-1.5">
            <component :is="t.icon" class="size-3.5" :stroke-width="1.5" aria-hidden="true" />
            {{ t.label }}
          </ToggleGroupItem>
        </ToggleGroup>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="group/editor flex min-w-0 flex-col rounded-lg bg-bg-inset transition-colors duration-150 focus-within:bg-surface-raised focus-within:ring-2 focus-within:ring-accent/25 motion-reduce:transition-none">
            <div class="flex h-9 items-center justify-between pr-1 pl-4 text-meta text-fg-muted">
              <span class="font-mono">js</span>
              <span class="flex items-center">
              <Button
                variant="ghost"
                size="icon"
                class="size-7"
                :icon="Undo2"
                :disabled="previous === null"
                aria-label="Back to what I had"
                title="Back to what I had"
                @click="back"
              />
              <Button
                variant="ghost"
                size="icon"
                class="size-7"
                :icon="RotateCcw"
                :disabled="code === base"
                aria-label="Reset"
                title="Reset"
                @click="replaceCode(base); runNow()"
              />
              </span>
            </div>
            <div class="flex min-h-40 flex-1 items-start gap-3 overflow-x-hidden px-4 pb-3 font-mono text-base leading-6 md:text-ui">
              <pre aria-hidden="true" class="m-0 w-5 shrink-0 select-none text-right font-[inherit] text-fg-faint">{{ lineNumbers }}</pre>
              <Textarea
                v-model="code"
                bare
                aria-label="Code"
                spellcheck="false"
                autocapitalize="off"
                autocomplete="off"
                wrap="off"
                @keydown.enter.exact.meta.prevent="runNow"
                @keydown.ctrl.enter.prevent="runNow"
                class="min-h-0 max-h-none flex-1 overflow-x-auto overflow-y-hidden whitespace-pre py-0 font-mono text-base leading-6 md:text-ui scrollbar-subtle"
              />
            </div>
          </div>
          <div class="flex min-w-0 flex-col rounded-lg bg-surface-sunk">
            <div class="flex h-9 items-center pl-4 text-fg-muted">
              <SquareTerminal class="size-3.5" :stroke-width="1.5" aria-hidden="true" />
              <span class="sr-only">Console</span>
            </div>
            <div role="log" aria-label="Console" aria-live="polite" class="flex max-h-60 min-h-40 flex-1 flex-col gap-1 overflow-y-auto overscroll-contain px-4 pb-3 font-mono text-ui leading-6 scrollbar-subtle focus-visible:outline-2 focus-visible:outline-accent/40" tabindex="0">
              <div
                v-for="(l, i) in lines"
                :key="i"
                :class="['flex items-start gap-2', l.bad ? 'text-danger' : l.quiet ? 'pl-5 text-fg-faint' : 'text-fg']"
              >
                <ChevronRight v-if="!l.quiet" class="mt-1.5 size-3 shrink-0 text-fg-faint" :stroke-width="1.5" aria-hidden="true" />
                <span class="min-w-0 whitespace-pre-wrap break-words">{{ l.text }}</span>
              </div>
            </div>
          </div>
        </div>
        <iframe
          v-if="frame"
          :key="runId"
          ref="sandbox"
          title="Runner"
          aria-hidden="true"
          tabindex="-1"
          sandbox="allow-scripts"
          referrerpolicy="no-referrer"
          :srcdoc="frame"
          class="pointer-events-none absolute size-0 border-0"
        />
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">C. Media carousel</h2>
      <Carousel v-model="slide" label="Further reading" class="max-w-sm">
        <CarouselItem v-for="(s, i) in slides" :key="i">
          <Card size="sm" class="mx-1">
            <CardContent class="flex flex-col gap-3">
              <div class="aspect-video overflow-hidden rounded-lg bg-surface-sunk">
                <template v-if="s.kind === 'video'">
                  <iframe
                    v-if="playing[i]"
                    class="size-full border-0"
                    :src="`https://www.youtube-nocookie.com/embed/${s.id}?autoplay=1`"
                    :title="`${s.title} (demo video)`"
                    sandbox="allow-scripts allow-same-origin allow-presentation"
                    allow="autoplay; encrypted-media; picture-in-picture"
                    referrerpolicy="strict-origin-when-cross-origin"
                  />
                  <Button
                    v-else
                    variant="ghost"
                    class="size-full rounded-none"
                    :aria-label="`Play: ${s.title} (demo video)`"
                    :title="`Play: ${s.title} (demo video)`"
                    @click="playing[i] = true"
                  >
                    <Play class="size-8" :stroke-width="1.5" aria-hidden="true" />
                  </Button>
                </template>
                <template v-else>
                  <div class="flex h-8 items-center gap-2 bg-surface-raised px-3">
                    <DiagramChip class="max-w-full truncate !py-0 text-meta">{{ s.host }}</DiagramChip>
                  </div>
                  <div class="flex flex-col gap-2 p-4" aria-hidden="true">
                    <div class="h-3 w-1/2 rounded-full bg-surface-raised" />
                    <div class="h-2 w-full rounded-full bg-surface-raised" />
                    <div class="h-2 w-5/6 rounded-full bg-surface-raised" />
                  </div>
                </template>
              </div>
              <div class="flex items-center justify-between gap-2">
                <span class="min-w-0 truncate text-ui font-semibold">{{ s.title }}</span>
                <Button
                  v-if="s.kind === 'site'"
                  variant="ghost"
                  size="icon"
                  :href="s.href"
                  target="_blank"
                  rel="noopener noreferrer"
                  :icon="ArrowUpRight"
                  :aria-label="`Open ${s.title}`"
                  :title="`Open ${s.title}`"
                />
              </div>
            </CardContent>
          </Card>
        </CarouselItem>
      </Carousel>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">D. The current style</h2>
      <div class="rounded-xl bg-bg-muted p-6">
        <Diagram label="var is function scoped, let and const are block scoped">
          <DiagramGroup layout="row">
            <DiagramArea title="Declaration" layout="row">
              <DiagramChip>var</DiagramChip>
              <DiagramChip>let</DiagramChip>
              <DiagramChip>const</DiagramChip>
            </DiagramArea>
            <DiagramArrow label="lives in" />
            <DiagramArea title="Scope" layout="column">
              <DiagramChip>function</DiagramChip>
              <DiagramChip>block</DiagramChip>
            </DiagramArea>
          </DiagramGroup>
        </Diagram>
      </div>
    </section>
  </main>
</template>
