<script setup>
// Every screen: one article at a single width (elastic-ui USAGE 11), with its
// title and an optional lead line just under it.
defineProps({
  title: { type: String, required: true },
  lead: { type: String, default: '' },
})
</script>

<template>
  <article class="prose article">
    <h1>{{ title }}</h1>
    <p v-if="lead" class="text-lg">{{ lead }}</p>
    <slot />
  </article>
</template>
