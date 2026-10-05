<script setup>
import LandingSection from '../components/LandingSection.vue'
import BeforeAfter from './BeforeAfter.vue'
import { copy } from '../i18n.js'

// "What is Kolmi?": the before and after first, as the README opens with it, then the idea in
// words and the hive's line set apart.
</script>

<template>
  <LandingSection id="what" :title="copy.what.title">
    <BeforeAfter />
    <div class="flex flex-col gap-4 text-lg leading-relaxed text-fg-secondary">
      <p v-for="(paragraph, i) in copy.what.body" :key="i">{{ paragraph }}</p>
    </div>
    <blockquote class="py-4 text-center text-2xl font-semibold tracking-tight text-balance text-fg sm:text-3xl">
      {{ copy.what.quote }}
    </blockquote>
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.what.scope }}</p>
  </LandingSection>
</template>
