<script setup>
import LandingSection from '../components/LandingSection.vue'
import HiveScene from '../components/HiveScene.vue'
import { copy } from '../i18n.js'

// "What is Kolmi?": the before and after first, as the README opens with it, then the problem
// and the idea in words.
</script>

<template>
  <LandingSection id="what" :title="copy.what.title">
    <HiveScene />
    <div class="flex flex-col gap-4 text-lg leading-relaxed text-fg-secondary">
      <p>{{ copy.what.body[0] }}</p>
    </div>
  </LandingSection>
</template>
