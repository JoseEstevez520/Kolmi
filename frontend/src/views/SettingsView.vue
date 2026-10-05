<script setup>
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  ActionButton,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Separator,
  Switch,
} from 'elastic-ui'
import FlagIcon from '../components/FlagIcon.vue'
import PageLayout from '../components/PageLayout.vue'
import { downloadExport } from '../lib/export.js'
import { LOCALES, setLocale } from '../lib/i18n.js'
import { motionOn, setMotionOn } from '../lib/motion.js'
import { replayTour } from '../lib/tour.js'

// How the app behaves in this browser: its language and its animations. Both depend on the
// device, so they are kept in the browser rather than in the account. One row per setting: what
// it is on the left, its control on the right.
const { t, locale } = useI18n()
const router = useRouter()

// The tour's first step points at Home, so it only makes sense from there.
function showTourAgain() {
  router.push('/').then(replayTour)
}
</script>

<template>
  <main class="py-16">
    <PageLayout data-tour="settings" :title="t('settings.title')" :lead="t('settings.lead')">
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
                <span :lang="code" class="flex items-center gap-2.5">
                  <FlagIcon :code="code" />
                  {{ name }}
                </span>
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

        <section class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5">
          <h2 id="tour" class="text-label font-medium text-fg">{{ t('settings.tour') }}</h2>
          <Button variant="ghost" @click="showTourAgain">{{ t('settings.replayTour') }}</Button>
        </section>

        <Separator />

        <p class="mt-5 text-label text-fg-muted">{{ t('settings.savedHere') }}</p>

        <Separator class="mt-5" />

        <section class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5">
          <div class="flex min-w-0 max-w-sm flex-col gap-1">
            <h2 id="notebook" class="text-label font-medium text-fg">{{ t('settings.notebook') }}</h2>
            <p class="text-label text-fg-secondary">{{ t('settings.notebookHint') }}</p>
          </div>
          <ActionButton
            icon="arrowDown"
            :label="t('export.all')"
            :done-label="t('export.done')"
            :error-label="t('export.error')"
            :action="() => downloadExport()"
          />
        </section>
      </div>
    </PageLayout>
  </main>
</template>
