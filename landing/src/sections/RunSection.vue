<script setup>
import { ArrowUpRight } from '@lucide/vue'
import { Button, Callout, CodeBlock } from 'elastic-ui'
import LandingSection from '../components/LandingSection.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// "Run it locally", as the README has it, and where the project stands.
</script>

<template>
  <LandingSection id="run" :title="copy.run.title">
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.run.lead }}</p>
    <CodeBlock :code="copy.run.commands" language="bash" />
    <p class="leading-relaxed text-fg-secondary"><RichText :text="copy.run.after" /></p>
    <Button variant="outline" :href="copy.links.backendReadme" class="self-start">
      {{ copy.run.backendReadme }}
      <ArrowUpRight aria-hidden="true" />
    </Button>
    <Callout type="note" :title="copy.run.status.title">
      {{ copy.run.status.body }}
      <a :href="copy.links.roadmap" class="underline underline-offset-2">{{ copy.run.status.roadmap }}</a>
    </Callout>
  </LandingSection>
</template>
