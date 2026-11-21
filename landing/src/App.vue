<script setup>
import { ScrollIndicator } from 'elastic-ui'
import AskDemo from './components/AskDemo.vue'
import MomentSection from './components/MomentSection.vue'
import BeforeAfter from './sections/BeforeAfter.vue'
import HeroSection from './sections/HeroSection.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'
import { copy } from './i18n.js'

// The landing with few words (Jose, 2026-11-21: the old one "tiene demasiado texto"): the hero with
// the note writing itself, then two moments, each one sentence and its picture; the footer closes with the code. The long
// explanations live in the README and the docs.
</script>

<template>
  <div id="top">
    <LandingHeader />
    <main>
      <HeroSection />
      <MomentSection id="what" :title="copy.short.pages"><BeforeAfter /></MomentSection>
      <MomentSection id="chat" :title="copy.short.ask"><AskDemo /></MomentSection>
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
