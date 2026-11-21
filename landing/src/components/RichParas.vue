<script setup>
import { computed } from 'vue'
import RichText from './RichText.vue'

// A description as short paragraphs, not one block (Jose, 2026-11-21: "usa más enters"): the text
// breaks at each blank line, and each paragraph is drawn by RichText.
const props = defineProps({
  text: { type: String, required: true },
})
const paras = computed(() => props.text.split(/\n\s*\n/))
</script>

<template>
  <div class="flex flex-col gap-4 text-lg leading-relaxed text-fg-secondary">
    <p v-for="(p, i) in paras" :key="i" class="m-0"><RichText :text="p" /></p>
  </div>
</template>
