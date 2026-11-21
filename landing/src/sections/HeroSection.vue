<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import { copy } from '../i18n.js'

// The first screen, simple (Jose, 2026-11-21: "lo prefiero simple"): the honey aurora, the logo,
// the slogan large, one line and one button. Its bottom melts into the page's colour, so going
// down to the first section is not a hard edge from honey to white. Few words
// (Jose, 2026-11-21). The bar sits on it, in line.
</script>

<template>
  <Aurora class="relative flex min-h-svh flex-col items-center justify-center px-4 pt-32 pb-56 text-center">
    <div class="flex max-w-3xl flex-col items-center gap-7">
      <img src="/logo.svg" alt="" width="64" height="64" class="size-16" />
      <h1 class="text-6xl leading-[0.95] font-semibold tracking-tight text-balance text-fg sm:text-8xl">{{ copy.hero.slogan }}</h1>
      <p class="max-w-xl text-lg leading-relaxed text-pretty text-fg-secondary sm:text-xl">{{ copy.short.lead }}</p>
      <Button size="lg" :href="copy.links.repo">
        <Logo :icon="siGithub" mono alt="" />
        {{ copy.hero.primary }}
      </Button>
    </div>
    <!-- The honey fades into the page instead of stopping at a line. -->
    <div class="fade pointer-events-none absolute inset-x-0 bottom-0 h-40" aria-hidden="true" />
  </Aurora>
</template>

<style scoped>
.fade {
  background: linear-gradient(to bottom, transparent, var(--color-bg) 85%);
}
</style>
