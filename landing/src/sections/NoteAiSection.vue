<script setup>
import LandingSection from '../components/LandingSection.vue'
import RichParas from '../components/RichParas.vue'
import { copy } from '../i18n.js'

// The AI in a note: a sentence on what it is, then the real thing on video (Jose, 2026-11-22: the
// git video "mola más" than the drawn scene): "how git works" + Ctrl+Enter becomes a heading, a
// sentence and a diagram. Muted, looping, inline, so it plays like a GIF on phones too.
</script>

<template>
  <LandingSection id="note-ai" :title="copy.noteAi.title">
    <!-- The text on the left, the note writing itself on the right (Jose, 2026-11-21). -->
    <div class="grid items-center gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-12">
      <RichParas :text="copy.noteAi.body" />
      <figure class="m-0">
        <video
          class="block w-full rounded-[1.8rem] bg-white"
          src="/video/note-ai-git.mp4"
          poster="/video/note-ai-git.jpg"
          :aria-label="copy.noteAi.label"
          autoplay
          muted
          loop
          playsinline
          preload="metadata"
          width="1080"
          height="1080"
        />
      </figure>
    </div>
  </LandingSection>
</template>
