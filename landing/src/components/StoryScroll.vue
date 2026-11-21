<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import { copy } from '../i18n.js'

// The landing as one story told in place (Jose, 2026-11-21: "un scroll no convencional, que se quede
// en el centro una cosa, que se vaya iluminando el texto… no este scroll normal para abajo"). A tall
// track holds a stage pinned to the screen; scrolling does not move the page, it moves the story:
//
//   0  the hero: logo, "Learn as a hive.", one line, the button
//   1  "everyone leaves their notes": loose notes from four students come in, one by one
//   2  "every night, the hive…": the notes fly together and become one page of the class
//   3  "ask in your note…": on that page a question is typed, Ctrl+Enter, and the answer is written
//   4  "ask the notes anything": the chat answers from the page, with its source
//
// In each chapter the sentence lights up word by word, then what it says happens in the centre.
// Everything is a function of the scroll, so it plays forward and back. Under reduced motion the
// track is short and every chapter shows its end, one under the other.
const CHAPTERS = 5
const SCREENS_PER_CHAPTER = 1.15 // how much scrolling each chapter takes, in screens

const track = ref(null)
const p = ref(0) // 0…1 over the whole story
let frame = 0
function measure() {
  frame = 0
  const el = track.value
  if (!el) return
  const r = el.getBoundingClientRect()
  const total = el.offsetHeight - innerHeight
  p.value = Math.min(1, Math.max(0, -r.top / total))
}
const onScroll = () => {
  if (!frame) frame = requestAnimationFrame(measure)
}
onMounted(() => {
  measure()
  addEventListener('scroll', onScroll, { passive: true })
  addEventListener('resize', onScroll)
})
onBeforeUnmount(() => {
  removeEventListener('scroll', onScroll)
  removeEventListener('resize', onScroll)
  cancelAnimationFrame(frame)
})

// Where the story is: chapter c and how far into it, t (0…1).
const at = computed(() => {
  const x = p.value * CHAPTERS
  const c = Math.min(CHAPTERS - 1, Math.floor(x))
  return { c, t: Math.min(1, x - c) }
})
// 0…1 as `t` goes from a to b in chapter c; 0 before, 1 after.
function span(c, a, b) {
  const { c: cc, t } = at.value
  if (cc < c) return 0
  if (cc > c) return 1
  return Math.min(1, Math.max(0, (t - a) / (b - a)))
}
const ease = (x) => 1 - Math.pow(1 - x, 3)

// ---- The sentence of each chapter, lit word by word ----
const line = computed(() => {
  const c = at.value.c
  if (c === 0) return null
  return copy.value.story.lines[c - 1]
})
const lineWords = computed(() => (line.value ? line.value.split(' ') : []))
const litCount = computed(() => Math.round(span(at.value.c, 0, 0.45) * lineWords.value.length))
// The sentence fades in at the start of its chapter and out at the end.
const lineOpacity = computed(() => {
  const { c, t } = at.value
  if (c === 0) return 0
  return Math.min(1, t / 0.08, (1 - t) / 0.08)
})

// ---- Chapter 0: the hero ----
const heroOut = computed(() => ease(span(0, 0.35, 0.9)))
// The honey stays behind the whole story, softer once the hero has gone.
const auroraOpacity = computed(() => 1 - 0.65 * heroOut.value)

// ---- Chapters 1-2: the notes, then the page ----
const SPOTS = [
  { x: -30, y: -16, r: -6, kind: 'sticky' },
  { x: 28, y: -20, r: 4, kind: 'card' },
  { x: -26, y: 18, r: 3, kind: 'card' },
  { x: 30, y: 16, r: -4, kind: 'sticky' },
]
function note(i) {
  const shown = ease(span(1, 0.4 + i * 0.12, 0.55 + i * 0.12))
  const gather = ease(span(2, 0.35, 0.75))
  const s = SPOTS[i]
  return {
    opacity: shown * (1 - gather) * (at.value.c <= 2 ? 1 : 0),
    transform: `translate(calc(-50% + ${s.x * (1 - gather)}vw), calc(-50% + ${s.y * (1 - gather) + (1 - shown) * 3}vh)) rotate(${s.r * (1 - gather)}deg) scale(${0.96 + 0.04 * shown - 0.5 * gather})`,
  }
}
const pageIn = computed(() => ease(span(2, 0.6, 0.95)))
// The page leaves for the chat.
const pageOut = computed(() => ease(span(4, 0.1, 0.4)))

// ---- Chapter 3: a question in the page, Ctrl+Enter, the answer ----
const ask = computed(() => copy.value.story.ask)
const typed = computed(() => {
  const n = Math.round(span(3, 0.45, 0.62) * ask.value.question.length)
  return ask.value.question.slice(0, n)
})
const keys = computed(() => {
  const k = span(3, 0.64, 0.7)
  return k > 0 && k < 1
})
const answered = computed(() => span(3, 0.7, 0.72) >= 1)
const answerWords = computed(() => ask.value.line.split(' '))
const answerLit = computed(() => Math.round(span(3, 0.72, 0.92) * answerWords.value.length))
const flowIn = computed(() => ease(span(3, 0.9, 0.98)))

// ---- Chapter 4: the chat ----
const chat = computed(() => copy.value.story.chat)
const chatIn = computed(() => ease(span(4, 0.3, 0.5)))
const chatAnswer = computed(() => ease(span(4, 0.6, 0.85)))
</script>

<template>
  <div ref="track" class="track" :style="{ height: `${CHAPTERS * SCREENS_PER_CHAPTER * 100 + 100}vh` }">
    <div class="stage">
      <Aurora class="absolute inset-0 -z-10" :style="{ opacity: auroraOpacity }" />

      <!-- 0: the hero -->
      <div
        class="hero"
        :style="{ opacity: 1 - heroOut, transform: `translate(-50%, calc(-50% - ${heroOut * 8}vh)) scale(${1 - heroOut * 0.06})` }"
      >
        <img src="/logo.svg" alt="" width="64" height="64" class="size-16" />
        <h1 class="text-6xl leading-[0.95] font-semibold tracking-tight text-balance text-fg sm:text-8xl">{{ copy.hero.slogan }}</h1>
        <p class="max-w-xl text-lg leading-relaxed text-pretty text-fg-secondary sm:text-xl">{{ copy.short.lead }}</p>
        <Button size="lg" :href="copy.links.repo" :tabindex="heroOut > 0.5 ? -1 : 0">
          <Logo :icon="siGithub" mono alt="" />
          {{ copy.hero.primary }}
        </Button>
        <p class="hint" :style="{ opacity: 1 - span(0, 0, 0.15) }">{{ copy.story.scroll }} ↓</p>
      </div>

      <!-- The sentence of the chapter, lit word by word -->
      <p v-if="line" class="line" :style="{ opacity: lineOpacity }">
        <template v-for="(word, i) in lineWords" :key="`${at.c}-${i}`"><span :class="{ lit: i < litCount }">{{ word }}</span>{{ ' ' }}</template>
      </p>

      <!-- 1-2: loose notes -->
      <div
        v-for="(text, i) in copy.story.notes"
        :key="i"
        class="note"
        :class="SPOTS[i].kind"
        :style="note(i)"
        aria-hidden="true"
      >
        <p class="m-0">{{ text }}</p>
        <p class="by">{{ copy.story.by[i] }}</p>
      </div>

      <!-- 2-3: the page of the class, then a question asked in it -->
      <article
        class="page"
        :style="{ opacity: pageIn * (1 - pageOut), transform: `translate(-50%, calc(-50% + ${(1 - pageIn) * 3 - pageOut * 4}vh)) scale(${0.94 + 0.06 * pageIn})` }"
        aria-hidden="true"
      >
        <p class="page-title">{{ copy.story.page.title }}</p>
        <p class="page-line">{{ copy.story.page.line }}</p>
        <div class="steps">
          <template v-for="(step, i) in copy.story.page.steps" :key="i">
            <span class="chip" :class="`chip-${i}`">{{ step }}</span>
            <span v-if="i < copy.story.page.steps.length - 1" class="arrow">→</span>
          </template>
        </div>

        <!-- 3: the question, typed with the scroll, and the answer in its place -->
        <div class="ask">
          <p v-if="!answered && (typed || at.c === 3)" class="q" :class="{ sent: keys }">{{ typed }}<span v-if="at.c === 3 && !keys" class="caret" /></p>
          <template v-if="answered">
            <p class="a-heading">{{ ask.heading }}</p>
            <p class="a-line">
              <template v-for="(word, i) in answerWords" :key="i"><span class="w" :class="{ on: i < answerLit }">{{ word }}</span>{{ ' ' }}</template>
            </p>
            <div class="steps" :style="{ opacity: flowIn, transform: `translateY(${(1 - flowIn) * 6}px)` }">
              <template v-for="(step, i) in ask.flow" :key="i">
                <span class="chip" :class="`chip-${i + 1}`">{{ step }}</span>
                <span v-if="i < ask.flow.length - 1" class="arrow">→</span>
              </template>
            </div>
          </template>
        </div>
        <p class="page-foot">{{ copy.story.page.foot }}</p>
      </article>

      <Transition name="keys">
        <div v-if="keys" class="keys" aria-hidden="true">
          <kbd><span>⌃</span>{{ copy.noteAi.demo.keys[0] }}</kbd>
          <kbd>{{ copy.noteAi.demo.keys[1] }}<span>↵</span></kbd>
        </div>
      </Transition>

      <!-- 4: the chat, answering from the page -->
      <div class="chat" :style="{ opacity: chatIn, transform: `translate(-50%, calc(-50% + ${(1 - chatIn) * 4}vh))` }" aria-hidden="true">
        <p class="bubble user">{{ chat.question }}</p>
        <div class="reply" :style="{ opacity: chatAnswer, transform: `translateY(${(1 - chatAnswer) * 8}px)` }">
          <p class="bubble">{{ chat.answer }}</p>
          <p class="source">{{ chat.source }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.track {
  position: relative;
  margin-top: -3.5rem; /* under the header, as the hero was */
}
.stage {
  position: sticky;
  top: 0;
  height: 100svh;
  overflow: hidden;
  isolation: isolate;
}
.hero {
  position: absolute;
  left: 50%;
  top: 52%;
  display: flex;
  width: min(48rem, 92vw);
  flex-direction: column;
  align-items: center;
  gap: 1.75rem;
  text-align: center;
}
.hint {
  margin: 1rem 0 0;
  font-size: 0.85rem;
  color: var(--color-fg-muted);
}

/* The chapter's sentence, near the top, its words lighting up as you scroll. */
.line {
  position: absolute;
  left: 50%;
  top: 15vh;
  width: min(44rem, 90vw);
  margin: 0;
  transform: translateX(-50%);
  text-align: center;
  font-size: clamp(1.6rem, 3.6vw, 2.6rem);
  line-height: 1.2;
  font-weight: 600;
  letter-spacing: -0.02em;
  text-wrap: balance;
}
.line span {
  color: color-mix(in oklab, var(--color-fg) 22%, transparent);
  transition: color 220ms ease-out;
}
.line span.lit {
  color: var(--color-fg);
}

.note {
  position: absolute;
  left: 50%;
  top: 58%;
  width: min(16rem, 40vw);
  padding: 0.9rem 1rem 0.75rem;
  border-radius: 0.9rem;
  background: #fff;
  box-shadow: 0 14px 30px -18px rgb(80 50 0 / 0.45);
  font-size: 0.95rem;
  line-height: 1.35;
  color: #3a3a36;
  will-change: transform, opacity;
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

.page {
  position: absolute;
  left: 50%;
  top: 60%;
  width: min(34rem, 90vw);
  padding: 1.5rem 1.6rem 1.25rem;
  border-radius: 1.4rem;
  background: #fff;
  box-shadow: 0 30px 60px -30px rgb(80 50 0 / 0.5);
  will-change: transform, opacity;
}
.page-title {
  margin: 0 0 0.5rem;
  font-size: 1.25rem;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: #1a1a18;
}
.page-line,
.a-line {
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

.ask {
  min-height: 8.5rem;
  margin-top: 1.1rem;
  padding-top: 1rem;
  border-top: 1px solid #efede8;
}
.q {
  margin: 0;
  font-size: 0.95rem;
  color: #3a3a36;
  transition: opacity 200ms;
}
.q.sent {
  opacity: 0.5;
}
.caret {
  display: inline-block;
  width: 1.5px;
  height: 1.05em;
  margin-left: 1px;
  vertical-align: -0.12em;
  background: #e0a43a;
  animation: blink 1.2s ease-in-out infinite;
}
@keyframes blink {
  60%,
  85% {
    opacity: 0.15;
  }
}
.a-heading {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  font-weight: 650;
  color: #1a1a18;
}
.w {
  color: transparent;
  transition: color 200ms;
}
.w.on {
  color: #4a4842;
}

.keys {
  position: absolute;
  left: 50%;
  bottom: 8vh;
  display: flex;
  gap: 0.5rem;
  padding: 0.55rem;
  border-radius: 1.1rem;
  background: rgb(24 24 27 / 0.86);
  transform: translateX(-50%);
}
.keys kbd {
  display: inline-flex;
  gap: 0.4rem;
  padding: 0.5rem 0.8rem;
  border-radius: 0.65rem;
  font: 500 0.95rem var(--font-sans);
  color: #fafafa;
  background: rgb(255 255 255 / 0.12);
}
.keys-enter-active,
.keys-leave-active {
  transition: opacity 200ms, transform 200ms;
}
.keys-enter-from,
.keys-leave-to {
  opacity: 0;
  transform: translate(-50%, 8px);
}

.chat {
  position: absolute;
  left: 50%;
  top: 60%;
  display: flex;
  width: min(36rem, 90vw);
  flex-direction: column;
  gap: 1rem;
}
.bubble {
  margin: 0;
  max-width: 85%;
  padding: 0.75rem 1rem;
  border-radius: 1.1rem;
  background: #fff;
  font-size: 1rem;
  line-height: 1.45;
  color: #2d2b27;
  box-shadow: 0 14px 30px -22px rgb(80 50 0 / 0.4);
}
.bubble.user {
  align-self: flex-end;
  background: #1a1a18;
  color: #fff;
}
.source {
  margin: 0.4rem 0 0 0.25rem;
  font-size: 0.75rem;
  color: #8a867c;
}

@media (prefers-reduced-motion: reduce) {
  .line span,
  .w,
  .q {
    transition: none;
  }
}
</style>
