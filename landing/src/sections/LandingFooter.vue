<script setup>
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import LocaleToggle from '../components/LocaleToggle.vue'
import { copy } from '../i18n.js'

// The page ends where it began, in honey: the call again, the slogan and the licence.
</script>

<template>
  <footer>
    <Aurora class="flex flex-col items-center gap-8 px-4 py-20 text-center">
      <div class="flex flex-col items-center gap-4">
        <img src="/logo.svg" alt="" width="48" height="48" class="size-12" />
        <p class="text-3xl font-semibold tracking-tight text-balance text-fg sm:text-4xl">{{ copy.footer.cta }}</p>
        <p class="text-lg text-fg-secondary">{{ copy.hero.slogan }}</p>
      </div>
      <Button size="lg" :href="copy.links.repo">
        <Logo :icon="siGithub" mono alt="" />
        {{ copy.footer.primary }}
      </Button>
      <div class="flex flex-col items-center gap-1 text-sm text-fg-secondary">
        <a :href="copy.links.license" class="underline-offset-2 hover:underline">{{ copy.footer.license }}</a>
        <a :href="copy.links.security" class="underline-offset-2 hover:underline">{{ copy.footer.security }}</a>
      </div>
      <LocaleToggle />
    </Aurora>
  </footer>
</template>
