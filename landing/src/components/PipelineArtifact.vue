<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { copy } from '../i18n.js'

// A small artifact inside the joint page (Jose, 2026-11-21: "cúrratelo más interfaz… con hasta
// artefacto"): the CI/CD pipeline the notes describe, as something you can try. A switch says
// whether the tests pass; the run goes step by step and either reaches the deploy or stops at the
// tests and greys out the rest. It plays a passing run, then a failing one, by itself; touching the
// switch takes over. Under reduced motion it shows the result at once.
const STEP_MS = 420

// It is always laid out (so the page around it keeps its size) and starts running when `active`.
const props = defineProps({ active: { type: Boolean, default: true } })

const a = computed(() => copy.value.hive.artifact)
const failing = ref(false)
const at = ref(-1) // the last step reached
const done = ref(false)
const reduced = ref(false)
let timer = 0
let demo = []

function run() {
  clearInterval(timer)
  at.value = -1
  done.value = false
  if (reduced.value) {
    at.value = failing.value ? 1 : a.value.steps.length - 1
    done.value = true
    return
  }
  timer = setInterval(() => {
    at.value++
    const stopAt = failing.value ? 1 : a.value.steps.length - 1
    if (at.value >= stopAt) {
      clearInterval(timer)
      done.value = true
    }
  }, STEP_MS)
}
function choose(fail) {
  demo.forEach(clearTimeout)
  demo = []
  failing.value = fail
  run()
}

function state(i) {
  if (i > at.value) return failing.value && done.value ? 'skipped' : 'pending'
  if (failing.value && i === 1) return 'failed'
  return 'ok'
}
const result = computed(() => (done.value ? (failing.value ? a.value.stop : a.value.ok) : ''))

function start() {
  run()
  if (!reduced.value) demo = [setTimeout(() => ((failing.value = true), run()), 4200)]
}
onMounted(() => {
  reduced.value = matchMedia('(prefers-reduced-motion: reduce)').matches
  if (props.active) start()
})
watch(
  () => props.active,
  (on) => on && start(),
)
onBeforeUnmount(() => {
  clearInterval(timer)
  demo.forEach(clearTimeout)
})
</script>

<template>
  <div class="artifact">
    <div class="head">
      <p class="name">{{ a.title }}</p>
      <div class="switch" role="radiogroup" :aria-label="a.title">
        <button
          v-for="(label, i) in a.toggle"
          :key="i"
          type="button"
          role="radio"
          :aria-checked="failing === (i === 1)"
          :class="{ on: failing === (i === 1), bad: i === 1 }"
          @click="choose(i === 1)"
        >
          {{ label }}
        </button>
      </div>
    </div>

    <ol class="steps">
      <li v-for="(step, i) in a.steps" :key="step" :class="state(i)">
        <span class="dot">
          <svg v-if="state(i) === 'ok'" viewBox="0 0 12 12"><path d="M2.5 6.2 5 8.6l4.5-5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" /></svg>
          <svg v-else-if="state(i) === 'failed'" viewBox="0 0 12 12"><path d="m3.2 3.2 5.6 5.6m0-5.6L3.2 8.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" /></svg>
        </span>
        <span class="label">{{ step }}</span>
      </li>
    </ol>

    <p class="result" :class="{ show: done, bad: failing }">{{ result || '·' }}</p>
  </div>
</template>

<style scoped>
.artifact {
  padding: 1rem 1.1rem 0.9rem;
  border-radius: 1.2rem;
  background: var(--color-bg);
}
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.6rem;
  margin-bottom: 1rem;
}
.name {
  margin: 0;
  flex: 1;
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--color-fg);
}
.switch {
  display: inline-flex;
  padding: 0.2rem;
  border-radius: 999px;
  background: var(--color-bg-muted);
}
.switch button {
  border: 0;
  border-radius: 999px;
  padding: 0.3rem 0.7rem;
  font: 500 0.78rem var(--font-sans);
  color: var(--color-fg-secondary);
  background: transparent;
  cursor: pointer;
  transition:
    background-color 250ms,
    color 250ms;
}
.switch button.on {
  background: #fff;
  color: #1c7c45;
}
.switch button.on.bad {
  color: #c0392b;
}

.steps {
  position: relative;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  margin: 0;
  padding: 0;
  list-style: none;
}
.steps li {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}
/* the line between two steps */
.steps li + li::before {
  content: '';
  position: absolute;
  top: 0.7rem;
  right: 50%;
  width: 100%;
  height: 2px;
  margin-right: 0.75rem;
  border-radius: 2px;
  background: var(--color-bg-muted);
  transition: background-color 300ms;
}
.steps li.ok + li.ok::before,
.steps li.ok + li.failed::before {
  background: #9fd9b4;
}
.dot {
  position: relative;
  z-index: 1;
  display: grid;
  width: 1.4rem;
  height: 1.4rem;
  place-items: center;
  border-radius: 999px;
  background: var(--color-bg-muted);
  transition:
    background-color 300ms,
    transform 300ms cubic-bezier(0.34, 1.5, 0.64, 1);
}
.dot svg {
  width: 0.8rem;
}
.ok .dot {
  background: #dff3e6;
  color: #1c7c45;
  transform: scale(1.08);
}
.failed .dot {
  background: #fbe0dc;
  color: #c0392b;
  transform: scale(1.08);
}
.label {
  font-size: 0.75rem;
  color: var(--color-fg-secondary);
  transition: opacity 300ms;
}
.skipped {
  opacity: 0.35;
}
.result {
  margin: 0.9rem 0 0;
  font-size: 0.82rem;
  color: #1c7c45;
  opacity: 0;
  transform: translateY(4px);
  transition:
    opacity 300ms,
    transform 300ms;
}
.result.bad {
  color: #c0392b;
}
.result.show {
  opacity: 1;
  transform: none;
}
</style>
