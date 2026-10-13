<script setup>
import { ref, watchEffect } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'
import { loadNode } from '../lib/content.js'

// The pages an answer comes from, written by id so the model never copies a title. Each node is
// read once per session (loadNode caches by id); one that cannot be read is left out.
const props = defineProps({ ids: { type: Array, default: () => [] } })
const { t } = useI18n()
const found = ref([])

watchEffect(async (onCleanup) => {
  let stale = false
  onCleanup(() => (stale = true))
  const ids = [...new Set(props.ids.map(Number).filter(Number.isFinite))]
  const nodes = await Promise.all(ids.map((id) => loadNode(id).catch(() => null)))
  if (!stale) found.value = nodes.filter((n) => n?.title).map((n) => ({ id: n.id, title: n.title }))
})
</script>

<template>
  <p v-if="found.length" class="not-prose m-0 text-meta text-fg-faint">
    {{ t('chat.sourcesLabel') }}
    <template v-for="(page, i) in found" :key="page.id">
      <RouterLink :to="`/node/${page.id}`" class="underline underline-offset-2 hover:text-fg">{{
        page.title
      }}</RouterLink
      ><template v-if="i < found.length - 1">, </template>
    </template>
  </p>
</template>
