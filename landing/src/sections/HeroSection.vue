<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import { copy } from '../i18n.js'

// The first screen, simple (Jose, 2026-11-21: "lo prefiero simple"): the honey aurora, the logo,
// the slogan large, one line and one button. What Kolmi does comes right after, as you scroll. Few words
// (Jose, 2026-11-21). It starts under the header (h-14), so the bar shows the honey through its blur.
</script>

<template>
  <Aurora class="-mt-14 flex min-h-svh flex-col items-center justify-center px-4 pt-32 pb-20 text-center">
    <div class="flex max-w-3xl flex-col items-center gap-7">
      <img src="/logo.svg" alt="" width="64" height="64" class="size-16" />
      <h1 class="text-6xl leading-[0.95] font-semibold tracking-tight text-balance text-fg sm:text-8xl">{{ copy.hero.slogan }}</h1>
      <p class="max-w-xl text-lg leading-relaxed text-pretty text-fg-secondary sm:text-xl">{{ copy.short.lead }}</p>
      <Button size="lg" :href="copy.links.repo">
        <Logo :icon="siGithub" mono alt="" />
        {{ copy.hero.primary }}
      </Button>
    </div>
  </Aurora>
</template>
