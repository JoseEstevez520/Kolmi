<script setup>
import LandingSection from '../components/LandingSection.vue'
import BeforeAfter from './BeforeAfter.vue'
import { copy } from '../i18n.js'

// "What is Kolmi?": the before and after first, as the README opens with it, then the idea in
// words, the hive's line in bold as the section's conclusion.
</script>

<template>
  <LandingSection id="what" :title="copy.what.title">
    <BeforeAfter />
    <div class="flex flex-col gap-4 text-lg leading-relaxed text-fg-secondary">
      <p v-for="(paragraph, i) in copy.what.body" :key="i">{{ paragraph }}</p>
    </div>
    <p class="text-lg font-semibold text-fg">{{ copy.what.quote }}</p>
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.what.scope }}</p>
  </LandingSection>
</template>
