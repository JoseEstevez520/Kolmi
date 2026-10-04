<script setup>
import { computed } from 'vue'
import { ES, GB } from 'country-flag-icons/string/3x2'

// A language's flag, small and rounded, with a hairline so a pale flag does not melt into the
// page. It is only drawn: the language's own name is always next to it.
const props = defineProps({
  code: { type: String, required: true },
})

// The flag each language is shown with; an unknown one shows none.
const FLAGS = { es: ES, en: GB }
const src = computed(() => (FLAGS[props.code] ? `data:image/svg+xml;utf8,${encodeURIComponent(FLAGS[props.code])}` : ''))
</script>

<template>
  <img
    v-if="src"
    :src="src"
    alt=""
    aria-hidden="true"
    class="h-4 w-6 shrink-0 rounded-[3px] object-cover ring-1 ring-inset ring-border"
  />
</template>
