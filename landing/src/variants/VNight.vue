<script setup>
import { computed, ref } from 'vue'
import { useLoop } from './useLoop.js'

// B: a day in one strip. During the day notes drop in and a counter goes up; night falls and the
// hive reads them; in the morning the page is there.
const phase = ref('day') // day | night | morning
const count = ref(0)
const steps = []
for (let i = 1; i <= 12; i++) steps.push([300 + i * 180, () => (count.value = i)])
useLoop(
  [
    [0, () => ((phase.value = 'day'), (count.value = 0))],
    ...steps,
    [3200, () => (phase.value = 'night')],
    [5400, () => (phase.value = 'morning')],
  ],
  11000,
)
const label = computed(() => ({ day: `Hoy · ${count.value} notas de la clase`, night: 'Esta noche · la colmena las lee', morning: 'Por la mañana · la página está lista' })[phase.value])
</script>

<template>
  <div class="strip" :class="phase">
    <p class="label">{{ label }}</p>
    <div class="dots">
      <span v-for="i in 12" :key="i" class="dot" :class="{ on: i <= count, gone: phase !== 'day' }" />
    </div>
    <div class="moon" />
    <article class="page">
      <p class="t">CI/CD con GitHub Actions y Docker</p>
      <p class="l">Cada push pasa los tests, construye una imagen y la sube a un registry, de donde la baja el servidor.</p>
      <p class="f">De 12 notas · anoche</p>
    </article>
  </div>
</template>

<style scoped>
.strip {
  position: relative;
  height: 24rem;
  overflow: hidden;
  border-radius: 1.6rem;
  background: #fbe9c6;
  transition: background-color 1200ms ease;
}
.strip.night {
  background: #1c2240;
}
.strip.morning {
  background: #fdf6ea;
}
.label {
  position: absolute;
  left: 2rem;
  top: 1.6rem;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #3a2c12;
  transition: color 800ms;
}
.night .label {
  color: #e7e9ff;
}
.dots {
  position: absolute;
  left: 2rem;
  right: 2rem;
  bottom: 2rem;
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 0.6rem;
}
.dot {
  height: 4.5rem;
  border-radius: 0.8rem;
  background: #fff;
  opacity: 0;
  transform: translateY(-30px);
  transition: opacity 300ms, transform 400ms cubic-bezier(0.34, 1.4, 0.64, 1);
}
.dot.on {
  opacity: 1;
  transform: none;
}
.dot.gone {
  opacity: 0;
  transform: translateY(20px) scale(0.8);
  transition-duration: 900ms;
}
.moon {
  position: absolute;
  right: 3rem;
  top: 2.5rem;
  width: 3.2rem;
  height: 3.2rem;
  border-radius: 50%;
  box-shadow: inset -0.9rem -0.3rem 0 0 #f4e7b5;
  opacity: 0;
  transition: opacity 900ms;
}
.night .moon {
  opacity: 1;
}
.page {
  position: absolute;
  left: 50%;
  top: 55%;
  width: min(30rem, 80%);
  padding: 1.4rem 1.5rem;
  border-radius: 1.2rem;
  background: #fff;
  opacity: 0;
  transform: translate(-50%, -40%);
  transition: opacity 700ms, transform 700ms cubic-bezier(0.22, 1, 0.36, 1);
}
.morning .page {
  opacity: 1;
  transform: translate(-50%, -50%);
}
.t {
  margin: 0 0 0.5rem;
  font-size: 1.2rem;
  font-weight: 650;
}
.l {
  margin: 0;
  color: var(--color-fg-secondary);
  line-height: 1.5;
}
.f {
  margin: 0.8rem 0 0;
  font-size: 0.75rem;
  color: var(--color-fg-muted);
}
</style>
