<script setup>
import { Aurora, Button, IconLink, IconLinks, Logo } from 'elastic-ui'
import { siGithub, siX } from 'simple-icons'
import LocaleToggle from '../components/LocaleToggle.vue'
import { copy } from '../i18n.js'
import { linkedin } from '../linkedin.js'

// The page ends where it began, in honey: the call again, the slogan, how to reach me (GitHub, X and
// LinkedIn, as the contact links of my portfolio) and the licence.
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
      <div class="flex flex-col items-center gap-3">
        <p class="text-fg-secondary">{{ copy.footer.contact }}</p>
        <IconLinks :label="copy.footer.contact">
          <IconLink :icon="siGithub" label="JoseEstevez520" :href="copy.links.github" />
          <IconLink :icon="siX" label="@JoseEstevez520" :href="copy.links.x" />
          <IconLink :icon="linkedin" label="Jose Estévez" :href="copy.links.linkedin" />
        </IconLinks>
      </div>
      <div class="flex flex-col items-center gap-1 text-sm text-fg-secondary">
        <a :href="copy.links.license" class="underline-offset-2 hover:underline">{{ copy.footer.license }}</a>
      </div>
      <LocaleToggle />
    </Aurora>
  </footer>
</template>
