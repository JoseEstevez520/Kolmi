<script setup>
import LandingSection from '../components/LandingSection.vue'
import NoteAiDemo from '../components/NoteAiDemo.vue'
import RichParas from '../components/RichParas.vue'
import { copy } from '../i18n.js'

// The AI in a note, after the chat it differs from: a sentence on what it is, the scene that
// shows it (made up, and it says so), then its conclusion again in bold and the rest in words.
</script>

<template>
  <LandingSection id="note-ai" :title="copy.noteAi.title">
    <!-- The text on the left, the note writing itself on the right (Jose, 2026-11-21). -->
    <div class="grid items-center gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12">
      <RichParas :text="copy.noteAi.body" />
      <figure class="m-0" :aria-label="copy.noteAi.label">
        <NoteAiDemo :demo="copy.noteAi.demo" />
      </figure>
    </div>
  </LandingSection>
</template>
