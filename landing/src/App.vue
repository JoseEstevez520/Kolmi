<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { ScrollIndicator } from 'elastic-ui'
import AskDemo from './components/AskDemo.vue'
import MomentSection from './components/MomentSection.vue'
import BeforeAfter from './sections/BeforeAfter.vue'
import HeroSection from './sections/HeroSection.vue'
import NoteAiDemo from './components/NoteAiDemo.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'
import { copy } from './i18n.js'

// The landing with few words (Jose, 2026-11-21: the old one "tiene demasiado texto"): a simple
// hero, then three moments, each one sentence and its picture (the night pass, the AI in a note,
// the chat); the footer closes with the code. The long explanations live in the README and the docs.
//
// Between sections the page changes colour (Jose, 2026-11-21: "más en scroll, cambios entre
// secciones"): each moment has a tone, and when it reaches the middle of the screen the page's
// background fades to it. The tones are soft and from Kolmi's honey, so each part reads as its own.
const TONES = { what: '#fbf0dc', note: '#ffffff', chat: '#f1eee8' }
let observer = null
onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) if (e.isIntersecting) document.body.style.setProperty('--page-bg', e.target.dataset.tone)
    },
    { rootMargin: '-45% 0px -45% 0px' },
  )
  document.querySelectorAll('[data-tone]').forEach((el) => observer.observe(el))
})
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div id="top">
    <LandingHeader />
    <main>
      <HeroSection />
      <MomentSection id="what" :tone="TONES.what" :title="copy.short.pages"><BeforeAfter /></MomentSection>
      <MomentSection id="note" :tone="TONES.note" :title="copy.short.note"><div class="mx-auto max-w-[46rem]"><NoteAiDemo :demo="copy.noteAi.demo" /></div></MomentSection>
      <MomentSection id="chat" :tone="TONES.chat" :title="copy.short.ask"><AskDemo /></MomentSection>
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
