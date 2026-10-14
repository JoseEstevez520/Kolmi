<script setup>
import { Button } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// For whoever would host it: what it needs and where the steps are, with no commands copied here
// to go out of date. They live in the README and the backend's README.
</script>

<template>
  <LandingSection id="run" :title="copy.run.title">
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.run.body" /></p>
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.run.scope" /></p>
    <div>
      <Button variant="secondary" :href="copy.links.run">{{ copy.run.cta }}</Button>
    </div>
  </LandingSection>
</template>
