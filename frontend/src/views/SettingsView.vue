<script setup>
import { useI18n } from 'vue-i18n'
import { RadioGroup, RadioGroupItem, Switch } from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'
import { LOCALES, setLocale } from '../lib/i18n.js'
import { forceMotion, setForceMotion } from '../lib/motion.js'

// How the app behaves in this browser: its language and its animations. Both depend on the
// device, so they are kept in the browser rather than in the account.
const { t, locale } = useI18n()
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('settings.title')" :lead="t('settings.lead')">
      <h2 id="language">{{ t('settings.language') }}</h2>
      <div class="not-prose my-6">
        <RadioGroup :model-value="locale" :label="t('settings.language')" @update:model-value="setLocale">
          <RadioGroupItem v-for="(name, code) in LOCALES" :key="code" :value="code">
            <span :lang="code">{{ name }}</span>
          </RadioGroupItem>
        </RadioGroup>
      </div>

      <h2 id="motion">{{ t('settings.motion') }}</h2>
      <p>{{ t('settings.motionHint') }}</p>
      <div class="not-prose my-6">
        <Switch :model-value="forceMotion" @update:model-value="setForceMotion">
          {{ t('settings.forceMotion') }}
        </Switch>
      </div>
      <p class="text-fg-muted">{{ t('settings.savedHere') }}</p>
    </PageLayout>
  </main>
</template>
