<script setup>
import { ScrollIndicator } from 'elastic-ui'
import HeroSection from './sections/HeroSection.vue'
import HowSection from './sections/HowSection.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'
import LinksSection from './sections/LinksSection.vue'
import PagesSection from './sections/PagesSection.vue'
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
      <TodaySection />
      <PagesSection />
      <RunSection />
      <LinksSection />
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
