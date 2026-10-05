<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import { copy } from '../i18n.js'

// The first screen, laid out as the class invitation (docs/brand-visuals.md): the honey aurora
// fills it and one centred column sits on top, with no card and no second surface. It starts
// under the header (h-14), so the bar shows the honey through its blur.
</script>

<template>
  <Aurora class="-mt-14 flex min-h-svh items-center justify-center px-4 pt-34 pb-20 text-center">
    <div class="flex max-w-xl flex-col items-center gap-8">
      <div class="flex flex-col items-center gap-4">
        <img src="/logo.svg" alt="" width="72" height="72" class="size-[72px]" />
        <div class="flex flex-col gap-2">
          <h1 class="text-5xl leading-none font-semibold tracking-tight text-fg sm:text-6xl">Kolmi</h1>
          <p class="text-lg text-fg-secondary">{{ copy.hero.slogan }}</p>
        </div>
      </div>

      <p class="text-lg leading-relaxed text-pretty text-fg sm:text-xl">{{ copy.hero.lead }}</p>

      <div class="flex flex-col items-center gap-4">
        <Button size="lg" :href="copy.links.repo">
          <Logo :icon="siGithub" mono alt="" />
          {{ copy.hero.primary }}
        </Button>
        <p class="text-sm text-fg-secondary">{{ copy.hero.scope }}</p>
      </div>
    </div>
  </Aurora>
</template>
