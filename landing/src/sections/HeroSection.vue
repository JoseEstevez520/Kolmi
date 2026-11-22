<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import { copy } from '../i18n.js'

// The first screen, laid out as the class invitation (docs/brand-visuals.md): the honey aurora
// fills it and one centred column sits on top, with no card and no second surface. It starts
// under the header (h-14), so the bar shows the honey through its blur. The column sits in the
// middle of the screen under the bar, and the honey goes on a little past it before it melts
// into the page over a shorter ramp (Jose, 2026-11-23: centred in height, the honey reaching lower).
</script>

<template>
  <Aurora class="relative -mt-14 px-4 pb-40 text-center">
    <div class="mx-auto flex min-h-svh max-w-xl flex-col items-center justify-center gap-8 pt-14">
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
      </div>
    </div>
    <!-- The honey melts into the page instead of stopping at a line. -->
    <div class="fade pointer-events-none absolute inset-x-0 bottom-0 h-64" aria-hidden="true" />
  </Aurora>
</template>

<style scoped>
.fade {
  /* A shorter, eased ramp: the honey holds most of the way and thins out near the end. */
  background: linear-gradient(
    to bottom,
    transparent 0%,
    color-mix(in oklab, var(--color-bg) 10%, transparent) 30%,
    color-mix(in oklab, var(--color-bg) 45%, transparent) 60%,
    color-mix(in oklab, var(--color-bg) 85%, transparent) 85%,
    var(--color-bg) 100%
  );
}
</style>
