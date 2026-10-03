<script setup>
import { useI18n } from 'vue-i18n'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Separator,
  Switch,
} from 'elastic-ui'
import PageLayout from '../components/PageLayout.vue'
import { LOCALES, setLocale } from '../lib/i18n.js'
import { motionOn, setMotionOn } from '../lib/motion.js'

// How the app behaves in this browser: its language and its animations. Both depend on the
// device, so they are kept in the browser rather than in the account. One row per setting: what
// it is on the left, its control on the right.
const { t, locale } = useI18n()
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('settings.title')" :lead="t('settings.lead')">
      <div class="not-prose mt-10 flex flex-col">
        <section class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5">
          <div class="flex min-w-0 max-w-sm flex-col gap-1">
            <h2 id="language" class="text-label font-medium text-fg">{{ t('settings.language') }}</h2>
            <p class="text-label text-fg-secondary">{{ t('settings.languageHint') }}</p>
          </div>
          <!-- A list, so more languages fit as they come. -->
          <Select :model-value="locale" class="w-44" @update:model-value="setLocale">
            <SelectTrigger :aria-label="t('settings.language')">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="(name, code) in LOCALES" :key="code" :value="code">
                <span :lang="code">{{ name }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </section>

        <Separator />

        <section class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5">
          <h2 id="motion" class="text-label font-medium text-fg">{{ t('settings.motion') }}</h2>
          <Switch :model-value="motionOn" @update:model-value="setMotionOn">
            <span class="sr-only">{{ t('settings.motion') }}</span>
          </Switch>
        </section>

        <Separator />

        <p class="mt-5 text-label text-fg-muted">{{ t('settings.savedHere') }}</p>
      </div>
    </PageLayout>
  </main>
</template>
