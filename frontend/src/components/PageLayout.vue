<script setup>
import { onBeforeUnmount, onMounted, ref, useTemplateRef, watch } from 'vue'
import { TableOfContents } from 'elastic-ui'
import { showToc } from '../lib/toc.js'

// Every screen: one article at a single width (elastic-ui USAGE 11), with its
// title and an optional lead line just under it. With `toc`, on wide screens,
// the table of contents of its headings (`h2` and `h3` with an `id`) beside it,
// read from what the article shows, so it follows the page as it loads.
const props = defineProps({
  title: { type: String, required: true },
  lead: { type: String, default: '' },
  toc: { type: Boolean, default: false },
})

const article = useTemplateRef('article')
const headings = ref([])

function read() {
  const found = [...(article.value?.querySelectorAll('h2[id], h3[id]') ?? [])]
  const next = found.map((h) => ({
    id: h.id,
    label: h.textContent.trim(),
    level: h.tagName === 'H2' ? 2 : 3,
  }))
  if (JSON.stringify(next) !== JSON.stringify(headings.value)) headings.value = next
}

let observer
onMounted(() => {
  if (!props.toc) return
  read()
  observer = new MutationObserver(read)
  observer.observe(article.value, { childList: true, subtree: true, characterData: true })
})

// With a table of contents the scroll line steps aside: the contents already mark where you are.
let release
watch(
  () => props.toc && headings.value.length > 1,
  (shown) => {
    if (shown && !release) release = showToc()
    else if (!shown && release) {
      release()
      release = undefined
    }
  },
)

onBeforeUnmount(() => {
  observer?.disconnect()
  release?.()
})
</script>

<template>
  <div class="relative">
    <article ref="article" class="prose article">
      <div v-if="$slots.actions" class="flex items-start justify-between gap-4">
        <h1>{{ title }}</h1>
        <div class="shrink-0 pt-1"><slot name="actions" /></div>
      </div>
      <h1 v-else>{{ title }}</h1>
      <p v-if="lead" class="text-lg">{{ lead }}</p>
      <slot />
    </article>

    <aside v-if="toc && headings.length > 1" class="absolute inset-y-0 right-8 hidden w-52 2xl:block">
      <TableOfContents :items="headings" class="sticky top-[calc(var(--page-header-height)+1rem)]" />
    </aside>
  </div>
</template>
