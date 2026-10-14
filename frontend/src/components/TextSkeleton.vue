<script setup>
import { Skeleton, SkeletonText } from 'elastic-ui'
import { useAfter } from '../lib/delayed.js'

// What a text page looks like before its content: the lines of a paragraph or two, with a
// heading bar when the heading is not already on screen. After `delay` ms, so a quick answer
// shows nothing at all.
const props = defineProps({
  lines: { type: Number, default: 6 },
  heading: { type: Boolean, default: false },
  delay: { type: Number, default: 300 },
})
const shown = useAfter(props.delay)
</script>

<template>
  <div aria-busy="true" class="flex flex-col gap-4 [--skeleton-bg:var(--color-border)]">
    <template v-if="shown">
      <Skeleton v-if="heading" class="h-8 w-1/2" />
      <SkeletonText :lines="lines" />
      <SkeletonText :lines="Math.max(2, lines - 3)" />
    </template>
  </div>
</template>
