<script setup>
import { ref } from 'vue'
import { TextMorph } from 'elastic-ui'
import { useLoop } from './useLoop.js'

// A: a hurried note turns into the page's clean text, letter by letter (elastic-ui's TextMorph).
const LINES = [
  ['ci/cd = github actions pasa los tests en cada push', 'CI/CD con GitHub Actions y Docker'],
  ['si pasan → construye la imagen docker y va al registry', 'Cada push pasa los tests, construye una imagen y la sube a un registry.'],
  ['rollback: desplegar la imagen anterior y listo!!', 'Si algo falla, se despliega la imagen anterior.'],
]
const done = ref([false, false, false])
const set = (i, v) => () => (done.value = done.value.map((d, k) => (k === i ? v : d)))
useLoop(
  [
    [1600, set(0, true)],
    [2700, set(1, true)],
    [3800, set(2, true)],
    [9000, () => (done.value = [false, false, false])],
  ],
  11000,
)
</script>

<template>
  <div class="morph">
    <p class="who">{{ done[0] ? 'Página de la clase · anoche' : 'Nota de Leo · clase de despliegue' }}</p>
    <p v-for="(l, i) in LINES" :key="i" :class="['line', `l${i}`, { clean: done[i] }]"><TextMorph :text="done[i] ? l[1] : l[0]" /></p>
  </div>
</template>

<style scoped>
.morph {
  display: flex;
  max-width: 46rem;
  flex-direction: column;
  gap: 0.9rem;
  text-align: left;
}
.who {
  margin: 0 0 0.4rem;
  font-size: 0.85rem;
  color: var(--color-fg-muted);
}
.line {
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.35;
  color: var(--color-fg-secondary);
  transition: color 500ms, font-size 500ms;
}
.line.l0.clean {
  font-size: 2.2rem;
  font-weight: 650;
  letter-spacing: -0.02em;
  color: var(--color-fg);
}
.line.clean {
  color: var(--color-fg);
}
</style>
