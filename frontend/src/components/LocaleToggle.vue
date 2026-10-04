<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button } from 'elastic-ui'
import { LOCALES, setLocale } from '../lib/i18n.js'
import FlagIcon from './FlagIcon.vue'

// Switches between English and Spanish on the sign-in screens. It shows the other
// language by its own name, so whoever needs it can read it in either.
const { t, locale } = useI18n()
const next = computed(() => (locale.value === 'es' ? 'en' : 'es'))
</script>

<template>
  <Button variant="ghost" size="sm" :aria-label="t('locale.switch')" @click="setLocale(next)">
    <FlagIcon :code="next" />
    <span :lang="next">{{ LOCALES[next] }}</span>
  </Button>
</template>
