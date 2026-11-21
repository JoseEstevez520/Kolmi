<script setup>
import LandingSection from '../components/LandingSection.vue'
import NoteAiDemo from '../components/NoteAiDemo.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// The AI in a note, after the chat it differs from: a sentence on what it is, the scene that
// shows it (made up, and it says so), then its conclusion again in bold and the rest in words.
</script>

<template>
  <LandingSection id="note-ai" :title="copy.noteAi.title">
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.noteAi.body" /></p>

    <figure class="m-0 flex flex-col gap-4" :aria-label="copy.noteAi.label">
      <div class="mx-auto w-full max-w-[46rem]"><NoteAiDemo :demo="copy.noteAi.demo" /></div>
    </figure>

  </LandingSection>
</template>
