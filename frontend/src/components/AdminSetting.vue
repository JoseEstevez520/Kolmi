<script setup>
// One setting of the class, as a row: what it is and what it does on the left, the control on
// the right (stacked on a phone). Rows sit one under another, split by a line; `aside` takes
// what belongs with the text, such as the next time the pass runs.
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
})
</script>

<template>
  <div class="grid gap-4 py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,28rem)] md:gap-12">
    <div class="min-w-0">
      <h3 class="m-0 text-label text-fg">{{ title }}</h3>
      <p v-if="description" class="m-0 mt-1 text-meta text-fg-muted">{{ description }}</p>
      <slot name="aside" />
    </div>
    <div class="flex min-w-0 flex-col items-start gap-3">
      <slot />
    </div>
  </div>
</template>
