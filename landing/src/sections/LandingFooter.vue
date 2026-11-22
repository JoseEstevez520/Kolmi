<script setup>
import { computed } from 'vue'
import { Aurora, Button, IconLink, IconLinks, Logo } from 'elastic-ui'
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
    <Aurora class="relative flex flex-col items-center gap-8 px-4 pt-40 pb-20 sm:pt-48 text-center">
      <!-- The page melts into the honey here, as the hero melts out of it at the top. -->
      <div class="fade-in pointer-events-none absolute inset-x-0 top-0 h-40" aria-hidden="true" />
      <div class="flex flex-col items-center gap-4">
        <img src="/logo.svg" alt="" width="48" height="48" class="size-12" />
        <p class="text-3xl font-semibold tracking-tight text-balance text-fg sm:text-4xl">{{ copy.footer.cta }}</p>
        <p class="text-lg text-fg-secondary">{{ copy.hero.slogan }}</p>
      </div>
      <!-- How to run it lives here now, under the call, instead of a section of its own (Jose,
           2026-11-23): the code and the steps side by side, and what it needs in one line. -->
      <div class="flex flex-col items-center gap-3">
        <div class="flex flex-wrap justify-center gap-2">
          <Button size="lg" :href="copy.links.repo">
            <Logo :icon="siGithub" mono alt="" />
            {{ copy.footer.primary }}
          </Button>
          <Button size="lg" variant="secondary" :href="copy.links.run">{{ copy.run.cta }}</Button>
        </div>
        <p class="m-0 max-w-md text-sm text-balance text-fg-secondary">{{ copy.run.short }}</p>
      </div>
      <div class="flex flex-col items-center gap-3">
        <p class="text-fg-secondary">{{ copy.footer.contact }}</p>
        <!-- My links: the icon alone, opening into its name when pointed at, with no tray (as the
             people in my portfolio's posts). -->
        <IconLinks variant="ghost" :label="copy.footer.contact" class="hidden sm:flex">
          <IconLink v-for="link in socials" :key="link.href" :icon="link.icon" :label="link.label" :href="link.href" />
        </IconLinks>
        <!-- On a phone there is no pointer to open them, so the row would show every name and wrap
             (Jose, 2026-11-23): there, just the three marks in a line. -->
        <nav class="flex gap-3 sm:hidden" :aria-label="copy.footer.contact">
          <Button v-for="link in socials" :key="link.href" variant="ghost" size="icon" :href="link.href" :aria-label="link.label">
            <Logo :icon="link.icon" alt="" />
          </Button>
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
