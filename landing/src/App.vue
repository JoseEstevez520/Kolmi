<script setup>
import { ScrollIndicator } from 'elastic-ui'
import AiSection from './sections/AiSection.vue'
import AskSection from './sections/AskSection.vue'
import HeroSection from './sections/HeroSection.vue'
import HowSection from './sections/HowSection.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'
import LinksSection from './sections/LinksSection.vue'
import RunSection from './sections/RunSection.vue'
import TodaySection from './sections/TodaySection.vue'
import WhatSection from './sections/WhatSection.vue'

// The landing follows the README, section by section, with each of its images made of the app's
// own parts. Grey between the honey: the aurora opens and closes the page, and the replay brings
// its own.
</script>

<template>
  <div id="top">
    <LandingHeader />
    <main>
      <HeroSection />
      <WhatSection />
      <HowSection />
      <AskSection />
      <AiSection />
      <TodaySection />
      <RunSection />
      <LinksSection />
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
