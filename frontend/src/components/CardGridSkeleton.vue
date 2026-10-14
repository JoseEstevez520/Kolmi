<script setup>
import { Card, CardHeader, Skeleton, SkeletonText } from 'elastic-ui'
import CardGrid from './CardGrid.vue'
import { useAfter } from '../lib/delayed.js'

// What a card grid looks like before its first answer: the shape of the cards, no words. Only
// for a first load with nothing cached (lib/cached.js); anything already seen draws at once. The
// cards appear after `delay` ms, so a quick answer shows nothing at all.
const props = defineProps({
  count: { type: Number, default: 4 },
  delay: { type: Number, default: 300 },
})
const shown = useAfter(props.delay)
</script>

<template>
  <CardGrid aria-busy="true" class="[--skeleton-bg:var(--color-border)]">
    <Card v-for="n in shown ? count : 0" :key="n" size="sm">
      <CardHeader class="gap-3">
        <Skeleton class="h-4 w-2/5" />
        <SkeletonText :lines="3" />
        <Skeleton class="mt-2 h-3 w-1/4" />
      </CardHeader>
    </Card>
  </CardGrid>
</template>
