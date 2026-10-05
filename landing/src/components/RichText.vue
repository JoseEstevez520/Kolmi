<script setup>
import { computed } from 'vue'

// A line of the landing's texts with its `**bold**` and `code` drawn, and nothing else: the
// texts are ours, but they still go in as text, never as HTML. The code looks as Prose draws it.
const props = defineProps({
  text: { type: String, required: true },
})

const parts = computed(() =>
  props.text
    .split(/(\*\*[^*]+\*\*|`[^`]+`)/)
    .filter(Boolean)
    .map((part) => {
      if (part.startsWith('**')) return { tag: 'strong', text: part.slice(2, -2) }
      if (part.startsWith('`')) return { tag: 'code', text: part.slice(1, -1) }
      return { tag: null, text: part }
    }),
)
</script>

<template>
  <template v-for="(part, i) in parts" :key="i">
    <code
      v-if="part.tag === 'code'"
      class="rounded-sm bg-bg-muted px-[0.35em] py-[0.15em] font-mono text-[0.875em] text-fg"
    >{{ part.text }}</code>
    <strong v-else-if="part.tag" class="font-semibold text-fg">{{ part.text }}</strong>
    <template v-else>{{ part.text }}</template>
  </template>
</template>
