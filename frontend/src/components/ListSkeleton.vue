<script setup>
import { Skeleton } from 'elastic-ui'
import { useAfter } from '../lib/delayed.js'

// What a list looks like before its first answer: rows with the shape of the real ones, no words.
// `list` is a status, two lines and room for actions (reports, a pass's entries); `table` is the
// people and connections tables (name over a detail, a few short cells). Only for a first load
// with nothing to show; it appears after `delay` ms so a quick answer shows nothing at all.
const props = defineProps({
  rows: { type: Number, default: 4 },
  layout: { type: String, default: 'list' },
  // The table layout's Select-sized cell (the people's role); off for a table without one.
  select: { type: Boolean, default: true },
  delay: { type: Number, default: 300 },
})
const shown = useAfter(props.delay)
</script>

<template>
  <div aria-busy="true" class="[--skeleton-bg:var(--color-border)]">
    <ul v-if="shown" class="m-0 flex list-none flex-col divide-y divide-border p-0">
      <li v-for="n in rows" :key="n" :class="['flex items-center gap-4 py-3', layout === 'table' && 'px-3']">
        <template v-if="layout === 'table'">
          <div class="flex w-40 shrink-0 flex-col gap-1.5">
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-3 w-full" />
          </div>
          <Skeleton class="h-4 w-16 shrink-0 max-sm:hidden" />
          <Skeleton v-if="select" class="h-9 w-28 shrink-0 max-sm:hidden" />
          <Skeleton class="ml-auto h-4 w-14" />
        </template>
        <template v-else>
          <Skeleton class="h-4 w-32 shrink-0" />
          <div class="flex min-w-0 flex-1 flex-col gap-1.5">
            <Skeleton class="h-4 w-1/2" />
            <Skeleton class="h-3 w-1/3" />
          </div>
        </template>
      </li>
    </ul>
  </div>
</template>
