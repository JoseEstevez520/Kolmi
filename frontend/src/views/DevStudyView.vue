<script setup>
import { computed, ref } from 'vue'
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
  Play,
  RefreshCw,
  Repeat,
  Square,
  Braces,
  Box,
  X,
} from '@lucide/vue'
import { logoFor } from '../lib/openui/logos.js'

// Development only (/dev/study): six ways a study page could look, on one topic ("var, let and
// const"), with the library's parts and fake local data. Nothing is fetched until a click.

// A. Logos
const stack = ['JavaScript', 'Node.js', 'Chrome', 'ESLint', 'Vue']

// B. A switch
const kinds = {
  var: {
    output: '2',
    ok: true,
    scope: 'function',
    reassign: true,
    redeclare: true,
  },
  let: {
    output: 'ReferenceError: x is not defined',
    ok: false,
    scope: 'block',
    reassign: true,
    redeclare: false,
  },
  const: {
    output: 'TypeError: Assignment to constant variable.',
    ok: false,
    scope: 'block',
    reassign: false,
    redeclare: false,
  },
}
const kind = ref('var')
const chosen = computed(() => kinds[kind.value])
const sample = computed(() => `if (true) {\n  ${kind.value} x = 1\n  x = 2\n}\nconsole.log(x)`)

// C. What does this print?
const question = `console.log(a)\nvar a = 1`
const answers = [
  { id: 'undefined', text: 'undefined' },
  { id: 'error', text: 'ReferenceError' },
  { id: 'one', text: '1' },
]
const right = 'undefined'
const picked = ref(null)

// D. Cheat sheet
const sheet = [
  { name: 'var', icon: Braces, rules: [[Box, 'Function scope'], [Repeat, 'Can be redeclared'], [RefreshCw, 'Can be reassigned']] },
  { name: 'let', icon: Square, rules: [[Square, 'Block scope'], [Ban, 'No redeclaring'], [RefreshCw, 'Can be reassigned']] },
  { name: 'const', icon: Lock, rules: [[Square, 'Block scope'], [Ban, 'No redeclaring'], [Equal, 'Never reassigned']] },
]

// E. Media carousel (the player and the page only load after a click)
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
      <h2 class="m-0 text-ui font-semibold">B. Compare with a switch</h2>
      <div class="flex flex-col gap-4 rounded-xl bg-bg-muted p-6">
        <ToggleGroup v-model="kind" type="single" aria-label="Keyword" class="self-start">
          <ToggleGroupItem v-for="(_, name) in kinds" :key="name" :value="name">{{ name }}</ToggleGroupItem>
        </ToggleGroup>
        <CodeBlock :code="sample" language="js" />
        <div class="flex items-center gap-2 text-ui">
          <Status compact :state="chosen.ok ? 'done' : 'error'" :label="chosen.ok ? 'Prints' : 'Throws'" />
          <code class="min-w-0 break-words">{{ chosen.output }}</code>
        </div>
        <Diagram :label="`Where x lives with ${kind}`">
          <DiagramGroup layout="row">
            <DiagramArea :title="chosen.scope === 'function' ? 'function' : 'block { }'" layout="row">
              <DiagramChip>x</DiagramChip>
            </DiagramArea>
            <DiagramChip :icon="chosen.reassign ? Check : X" note="reassign">x = 2</DiagramChip>
            <DiagramChip :icon="chosen.redeclare ? Check : X" note="redeclare">{{ kind }} x</DiagramChip>
          </DiagramGroup>
        </Diagram>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">C. What does this print?</h2>
      <div class="flex flex-col gap-4 rounded-xl bg-bg-muted p-6">
        <CodeBlock :code="question" language="js" />
        <div class="flex flex-wrap gap-2">
          <Button
            v-for="a in answers"
            :key="a.id"
            variant="ghost"
            :disabled="picked !== null && picked !== a.id"
            :aria-pressed="picked === a.id"
            :class="picked === a.id && 'bg-bg-muted text-fg'"
            @click="picked = picked === a.id ? null : a.id"
          >{{ a.text }}</Button>
        </div>
        <div v-if="picked" class="flex items-center gap-2 text-ui text-fg-secondary">
          <Status compact :state="picked === right ? 'done' : 'error'" :label="picked === right ? 'Right' : 'Not quite'" />
          The declaration moves up, the value stays behind: a is undefined.
        </div>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">D. Card grid cheat sheet</h2>
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <Card v-for="k in sheet" :key="k.name" size="sm">
          <CardContent class="flex flex-col gap-3">
            <span class="flex items-center gap-2 text-ui font-semibold">
              <component :is="k.icon" class="size-4" :stroke-width="1.5" aria-hidden="true" />
              {{ k.name }}
            </span>
            <ul class="m-0 flex list-none flex-col gap-2 p-0">
              <li v-for="[icon, text] in k.rules" :key="text" class="flex items-center gap-2 text-label text-fg-secondary">
                <component :is="icon" class="size-4 shrink-0" :stroke-width="1.5" aria-hidden="true" />
                {{ text }}
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h2 class="m-0 text-ui font-semibold">E. Media carousel</h2>
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
      <h2 class="m-0 text-ui font-semibold">F. The current style</h2>
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
