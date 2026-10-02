<script setup>
import { computed, shallowRef } from 'vue'
import { useRoute } from 'vue-router'
import { ThemeToggle } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'
import { loadPageRenderer } from '../lib/openui/load.js'

// Development only (/dev/pages): the sample pages in src/lib/openui/samples, drawn with the real
// renderer, to compare the web agent's pages with hand-made ones. `?s=<name>` picks one.
const SAMPLES = Object.fromEntries(
  Object.entries(import.meta.glob('../lib/openui/samples/*.oui', { query: '?raw', import: 'default', eager: true })).map(
    ([path, source]) => [path.split('/').pop().replace(/\.oui$/, ''), source],
  ),
)

const route = useRoute()
const names = Object.keys(SAMPLES).sort()
const current = computed(() => (names.includes(route.query.s) ? route.query.s : names[0]))
const openui = shallowRef(null)
loadPageRenderer().then((loaded) => (openui.value = loaded))

const onErrors = (errors) => errors.length && console.warn('Sample has errors:', errors)
</script>

<template>
  <main class="py-10">
    <nav class="article mb-10 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
      <RouterLink
        v-for="name in names"
        :key="name"
        :to="{ query: { s: name } }"
        :class="name === current ? 'font-semibold text-fg' : 'text-fg-muted hover:text-fg'"
      >
        {{ name }}
      </RouterLink>
      <ThemeToggle class="ml-auto" />
    </nav>
    <PageLayout v-if="current" :title="current">
      <component
        :is="openui.Renderer"
        v-if="openui"
        :key="current"
        :response="SAMPLES[current]"
        :library="openui.pageLibrary"
        :on-error="onErrors"
      />
    </PageLayout>
  </main>
</template>
