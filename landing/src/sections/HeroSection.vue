<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import NoteAiDemo from '../components/NoteAiDemo.vue'
import { copy } from '../i18n.js'

// The first screen: the honey aurora, the slogan large, one line and one button, and under them
// the note writing itself with Ctrl+Enter, large, as the picture of what Kolmi does. Few words
// (Jose, 2026-11-21). It starts under the header (h-14), so the bar shows the honey through its blur.
</script>

<template>
  <Aurora class="-mt-14 flex flex-col items-center px-4 pt-32 pb-16 text-center">
    <div class="flex max-w-3xl flex-col items-center gap-7">
      <img src="/logo.svg" alt="" width="64" height="64" class="size-16" />
      <h1 class="text-6xl leading-[0.95] font-semibold tracking-tight text-balance text-fg sm:text-8xl">{{ copy.hero.slogan }}</h1>
      <p class="max-w-xl text-lg leading-relaxed text-pretty text-fg-secondary sm:text-xl">{{ copy.short.lead }}</p>
      <Button size="lg" :href="copy.links.repo">
        <Logo :icon="siGithub" mono alt="" />
        {{ copy.hero.primary }}
      </Button>
    </div>
    <div class="mt-16 w-full max-w-[54rem] text-left">
      <NoteAiDemo :demo="copy.noteAi.demo" />
    </div>
  </Aurora>
</template>
