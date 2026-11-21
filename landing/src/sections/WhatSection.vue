<script setup>
import LandingSection from '../components/LandingSection.vue'
import HiveScene from '../components/HiveScene.vue'
import RichParas from '../components/RichParas.vue'
import { copy } from '../i18n.js'

// "What is Kolmi?": the before and after first, as the README opens with it, then the problem
// and the idea in words.
</script>

<template>
  <LandingSection id="what" :title="copy.what.title">
    <HiveScene />
    <RichParas :text="copy.what.body[0]" />
  </LandingSection>
</template>
