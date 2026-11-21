<script setup>
import { ScrollIndicator } from 'elastic-ui'
import StoryScroll from './components/StoryScroll.vue'
import LandingFooter from './sections/LandingFooter.vue'
import LandingHeader from './sections/LandingHeader.vue'

// The landing as one story told in place (StoryScroll): a stage pinned to the screen that the scroll
// moves through, from the hero to the notes, the page, the AI in a note and the chat. Then the
// footer, scrolled as usual. The older sections stay in the code, out of the page.
</script>

<template>
  <div id="top">
    <LandingHeader />
    <main>
      <StoryScroll />
    </main>
    <LandingFooter />
    <ScrollIndicator />
  </div>
</template>
