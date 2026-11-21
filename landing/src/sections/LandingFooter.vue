<script setup>
import { computed } from 'vue'
import { Aurora, Button, Logo } from 'elastic-ui'
import { siGithub, siX } from 'simple-icons'
import LocaleToggle from '../components/LocaleToggle.vue'
import { copy } from '../i18n.js'
import { linkedin } from '../linkedin.js'

// Read when drawn, as the texts follow the chosen language.
const socials = computed(() => [
  { icon: siGithub, label: 'JoseEstevez520', href: copy.value.links.github },
  { icon: siX, label: '@JoseEstevez520', href: copy.value.links.x },
  { icon: linkedin, label: 'Jose Estévez', href: copy.value.links.linkedin },
])

// The page ends where it began, in honey: the call again, the slogan, how to reach me (GitHub, X and
// LinkedIn, as the contact links of my portfolio) and the licence.
</script>

<template>
  <footer>
    <Aurora class="relative flex flex-col items-center gap-8 px-4 pt-48 pb-20 text-center">
      <!-- The page melts into the honey here, as the hero melts out of it at the top. -->
      <div class="fade-in pointer-events-none absolute inset-x-0 top-0 h-64" aria-hidden="true" />
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
        <!-- My links, as the portfolio's contact (icon and name), with no background (Jose, 2026-11-21). -->
        <nav :aria-label="copy.footer.contact" class="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <a
            v-for="link in socials"
            :key="link.href"
            :href="link.href"
            class="inline-flex items-center gap-2 text-fg-secondary transition-colors hover:text-fg"
          >
            <Logo :icon="link.icon" mono alt="" class="size-4" />
            <span>{{ link.label }}</span>
          </a>
        </nav>
      </div>
      <div class="flex flex-col items-center gap-1 text-sm text-fg-secondary">
        <a :href="copy.links.license" class="underline-offset-2 hover:underline">{{ copy.footer.license }}</a>
      </div>
      <LocaleToggle />
    </Aurora>
  </footer>
</template>

<style scoped>
.fade-in {
  background: linear-gradient(to top, transparent, var(--color-bg) 85%);
}
</style>
