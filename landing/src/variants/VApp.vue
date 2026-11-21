<script setup>
import { ref } from 'vue'
import { useLoop } from './useLoop.js'

// C: the app as it is. The class's tree of pages on the left; in the morning a new page shows in
// the tree, marked new, and opens.
const fresh = ref(false)
const open = ref(false)
useLoop(
  [
    [0, () => ((fresh.value = false), (open.value = false))],
    [1400, () => (fresh.value = true)],
    [2600, () => (open.value = true)],
  ],
  9500,
)
const TREE = ['Redes', 'Bases de datos', 'Programación', 'Despliegue']
</script>

<template>
  <div class="app">
    <aside class="side">
      <p class="cls">DAW 2 · Clase</p>
      <ul>
        <li v-for="t in TREE" :key="t">{{ t }}</li>
        <li class="child" :class="{ fresh, open }">CI/CD con GitHub Actions y Docker <span class="badge">Nueva</span></li>
      </ul>
    </aside>
    <main class="main">
      <template v-if="open">
        <p class="t">CI/CD con GitHub Actions y Docker</p>
        <p class="l">Cada push pasa los tests, construye una imagen de Docker y la sube a un registry, de donde la baja el servidor.</p>
        <div class="chips"><span>git push</span>→<span class="v">GitHub Actions</span>→<span class="b">registry</span>→<span class="g">servidor</span></div>
        <p class="f">Escrita anoche a partir de 4 notas de la clase</p>
      </template>
      <p v-else class="empty">Elige una página</p>
    </main>
  </div>
</template>

<style scoped>
.app {
  display: grid;
  grid-template-columns: 15rem 1fr;
  height: 24rem;
  overflow: hidden;
  border-radius: 1.4rem;
  background: var(--color-bg-subtle);
}
.side {
  padding: 1.4rem 1rem;
  background: var(--color-bg-muted);
}
.cls {
  margin: 0 0 1rem 0.5rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--color-fg-muted);
}
ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
li {
  padding: 0.45rem 0.6rem;
  border-radius: 0.6rem;
  font-size: 0.92rem;
  color: var(--color-fg-secondary);
}
.child {
  margin-left: 0.9rem;
  max-height: 0;
  overflow: hidden;
  padding-block: 0;
  opacity: 0;
  transition: all 500ms cubic-bezier(0.22, 1, 0.36, 1);
}
.child.fresh {
  max-height: 3.5rem;
  padding-block: 0.45rem;
  opacity: 1;
}
.child.open {
  background: #fbe7bf;
  color: var(--color-fg);
}
.badge {
  margin-left: 0.3rem;
  padding: 0.05rem 0.4rem;
  border-radius: 0.4rem;
  font-size: 0.7rem;
  background: #f0aa3c;
  color: #fff;
}
.main {
  padding: 2rem 2.2rem;
  text-align: left;
  animation: none;
}
.main > * {
  animation: in 500ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes in {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}
.t {
  margin: 0 0 0.6rem;
  font-size: 1.4rem;
  font-weight: 650;
}
.l {
  margin: 0 0 1rem;
  line-height: 1.55;
  color: var(--color-fg-secondary);
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  color: var(--color-fg-muted);
}
.chips span {
  padding: 0.3rem 0.6rem;
  border-radius: 0.55rem;
  font-size: 0.85rem;
  background: var(--color-bg-muted);
  color: var(--color-fg);
}
.chips .v {
  background: #efe9fe;
  color: #5b3fd6;
}
.chips .b {
  background: #e7f0ff;
  color: #2563eb;
}
.chips .g {
  background: #e6f6ec;
  color: #1c7c45;
}
.f {
  margin: 1rem 0 0;
  font-size: 0.75rem;
  color: var(--color-fg-muted);
}
.empty {
  color: var(--color-fg-muted);
}
</style>
