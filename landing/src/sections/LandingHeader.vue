<script setup>
import { Button, Logo, StickyHeader } from 'elastic-ui'
import { siGithub } from 'simple-icons'
import LocaleToggle from '../components/LocaleToggle.vue'
import { copy } from '../i18n.js'

// The landing's bar: a page without a sidebar that wants a quiet bar (USAGE 15), held at the
// top over a blur. The links fold away on a phone; the language, the code and the theme stay.
// At the top it is clear, the hero's honey right through it, and veiled once the page moves.
</script>

<template>
  <StickyHeader :label="copy.nav.label" clear class="landing-header">
    <template #logo>
      <a href="#top" class="flex items-center gap-2 rounded-md text-fg">
        <img src="/logo.svg" alt="" width="24" height="24" class="size-6" />
        <span class="font-semibold tracking-tight">Kolmi</span>
      </a>
    </template>

    <Button variant="ghost" size="sm" href="#how">{{ copy.nav.how }}</Button>
    <Button variant="ghost" size="sm" href="#chat">{{ copy.nav.chat }}</Button>
    <Button variant="ghost" size="sm" href="#ai">{{ copy.nav.ai }}</Button>

    <template #actions>
      <LocaleToggle />
      <!-- A ghost button as the rest of the bar: the same grey, no tray of the brand's colour. -->
      <Button variant="ghost" size="sm" :href="copy.links.repo" :aria-label="`${copy.nav.code}: GitHub`">
        <Logo :icon="siGithub" mono alt="" />
        GitHub
      </Button>
    </template>
  </StickyHeader>
</template>


<style>
/* The links sit in the middle of the page, not in the middle of what the logo and the actions leave
   (Jose, 2026-11-23: "el nav no está bien centrado"). StickyHeader spaces its three parts with
   justify-between, so the sides take equal shares here and the actions go to the right. */
@media (min-width: 768px) {
  .landing-header > div > :first-child,
  .landing-header > div > :last-child {
    flex: 1 1 0;
  }
  .landing-header > div > :last-child {
    justify-content: flex-end;
  }
}
</style>
