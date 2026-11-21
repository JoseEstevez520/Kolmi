<script setup>
import { Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import LocaleToggle from '../components/LocaleToggle.vue'
import { copy } from '../i18n.js'

// The bar, in line with the page instead of following it (Jose, 2026-11-21: the sticky bar got in
// the way): it sits on top of the hero and scrolls away with it. Only the logo, the language and
// the code; the page is short enough to need no menu.
</script>

<template>
  <header class="absolute inset-x-0 top-0 z-10">
    <div class="mx-auto flex h-16 w-[min(100%-2rem,72rem)] items-center justify-between">
      <a href="#top" class="flex items-center gap-2 rounded-md text-fg">
        <img src="/logo.svg" alt="" width="24" height="24" class="size-6" />
        <span class="font-semibold tracking-tight">Kolmi</span>
      </a>
      <div class="flex items-center gap-1">
        <LocaleToggle />
        <Button variant="ghost" size="sm" :href="copy.links.repo" :aria-label="`${copy.nav.code}: GitHub`">
          <Logo :icon="siGithub" mono alt="" />
          GitHub
        </Button>
      </div>
    </div>
  </header>
</template>
