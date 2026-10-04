<script setup>
import { computed } from 'vue'

// A language's flag as an emoji, so it looks as the device draws its own (Apple's on an iPhone or
// a Mac). It is only drawn: the language's own name is always next to it.
const props = defineProps({
  code: { type: String, required: true },
})

// The flag each language is shown with; an unknown one shows none.
const FLAGS = { es: '🇪🇸', en: '🇬🇧' }
const flag = computed(() => FLAGS[props.code] ?? '')
</script>

<template>
  <span
    v-if="flag"
    aria-hidden="true"
    class="shrink-0 text-[1.25rem] leading-none [font-family:'Apple_Color_Emoji','Noto_Color_Emoji','Segoe_UI_Emoji',sans-serif]"
  >{{ flag }}</span>
</template>
