<script setup>
import { computed } from 'vue'
import { Button } from 'elastic-ui'
import { copy, locale, LOCALES, setLocale } from '../i18n.js'

// Switches between English and Spanish, as the app's own toggle does: it shows the other
// language by its own name, so whoever needs it can read it in either.
const next = computed(() => (locale.value === 'es' ? 'en' : 'es'))
</script>

<template>
  <Button variant="ghost" size="sm" :aria-label="copy.nav.switchLocale" @click="setLocale(next)">
    <span :lang="next">{{ LOCALES[next] }}</span>
  </Button>
</template>
