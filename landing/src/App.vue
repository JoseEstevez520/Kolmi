<script setup>
import { ScrollIndicator } from 'elastic-ui'
import AskDemo from './components/AskDemo.vue'
import PinnedChapters from './components/PinnedChapters.vue'
import BeforeAfter from './sections/BeforeAfter.vue'
import HeroSection from './sections/HeroSection.vue'
import NoteAiDemo from './components/NoteAiDemo.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'
import { copy } from './i18n.js'

// The landing with few words (Jose, 2026-11-21: the old one "tiene demasiado texto"): a simple
// hero scrolled as usual, then a pinned stage (PinnedChapters) that the scroll steps through, three
// chapters, each one sentence and its picture (the night pass, the AI in a note,
// the chat); the footer closes with the code. The long explanations live in the README and the docs.
</script>

<template>
  <div id="top">
    <LandingHeader />
    <main>
      <HeroSection />
      <PinnedChapters
        :chapters="[
          { id: 'what', title: copy.short.pages, layout: 'stack' },
          { id: 'note', title: copy.short.note, layout: 'left' },
          { id: 'chat', title: copy.short.ask, layout: 'right' },
        ]"
      >
        <template #what><BeforeAfter /></template>
        <template #note><NoteAiDemo :demo="copy.noteAi.demo" /></template>
        <template #chat><AskDemo /></template>
      </PinnedChapters>
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
