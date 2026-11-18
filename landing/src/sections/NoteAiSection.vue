<script setup>
import LandingSection from '../components/LandingSection.vue'
import NoteAiReel from '../components/NoteAiReel.vue'
import RichText from '../components/RichText.vue'
import { copy } from '../i18n.js'

// The AI in a note, after the chat it differs from: a sentence on what it is, the scene that
// shows it (made up, and it says so), then its conclusion again in bold and the rest in words.
</script>

<template>
  <LandingSection id="note-ai" :title="copy.noteAi.title">
    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.noteAi.body" /></p>
    <p class="text-lg leading-relaxed text-fg-secondary">{{ copy.noteAi.lead }}</p>

    <figure class="m-0 flex flex-col gap-4" :aria-label="copy.noteAi.label">
      <NoteAiReel :reel="copy.noteAi.reel" />
      <figcaption class="text-center text-sm text-fg-muted">{{ copy.noteAi.caption }}</figcaption>
    </figure>

    <p class="text-lg leading-relaxed text-fg-secondary"><RichText :text="copy.noteAi.after" /></p>
  </LandingSection>
</template>
