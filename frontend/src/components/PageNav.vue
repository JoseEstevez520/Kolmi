<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Card, CardDescription, CardHeader, CardTitle } from 'elastic-ui'
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { nodes, prefetchNode, trailTo } from '../lib/content.js'

// At the end of a page: the one before and the one after it in its section, in the order the
// admin gave them, to read on without going back to the section. Each is a Card that is its link.
const props = defineProps({
  id: { type: Number, required: true },
})

const { t } = useI18n()

const level = computed(() => trailTo(props.id, nodes.value).at(-1)?.level ?? [])
const at = computed(() => level.value.findIndex((node) => node.id === props.id))
const previous = computed(() => level.value[at.value - 1])
const next = computed(() => level.value[at.value + 1])
</script>

<template>
  <nav
    v-if="at >= 0 && level.length > 1"
    :aria-label="t('node.previousNext')"
    class="not-prose mt-16 flex flex-col gap-3"
  >
    <span class="text-meta text-fg-muted">{{ t('node.position', { n: at + 1, total: level.length }) }}</span>
    <div class="grid gap-4 sm:grid-cols-2">
      <Card v-if="previous" :to="`/node/${previous.id}`" size="sm" @pointerenter="prefetchNode(previous.id)">
        <CardHeader class="gap-1">
          <CardDescription class="flex items-center gap-1.5">
            <ArrowLeft class="size-3.5" aria-hidden="true" />
            {{ t('node.previous') }}
          </CardDescription>
          <CardTitle>{{ previous.title }}</CardTitle>
        </CardHeader>
      </Card>
      <span v-else aria-hidden="true" class="max-sm:hidden" />

      <Card v-if="next" :to="`/node/${next.id}`" size="sm" @pointerenter="prefetchNode(next.id)">
        <CardHeader class="items-end gap-1 text-right">
          <CardDescription class="flex items-center gap-1.5">
            {{ t('node.next') }}
            <ArrowRight class="size-3.5" aria-hidden="true" />
          </CardDescription>
          <CardTitle>{{ next.title }}</CardTitle>
          <CardDescription v-if="next.description">{{ next.description }}</CardDescription>
        </CardHeader>
      </Card>
    </div>
  </nav>
</template>
