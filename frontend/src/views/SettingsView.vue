<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import {
  Button,
  ConfirmButton,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Separator,
  StatusText,
  Switch,
} from 'elastic-ui'
import ConnectAI from '../components/ConnectAI.vue'
import FlagIcon from '../components/FlagIcon.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile, signOut } from '../lib/auth.js'
import { LOCALES, setLocale } from '../lib/i18n.js'
import { motionOn, setMotionOn } from '../lib/motion.js'
import { replayTour } from '../lib/tour.js'

// How the app behaves in this browser: its language and its animations. Both depend on the
// device, so they are kept in the browser rather than in the account. One row per setting: what
// it is on the left, its control on the right.
const { t, locale } = useI18n()
const router = useRouter()

// Your account, kept on the server: the name the class sees, and leaving for good. Deleting
// takes your notes and chat with it, not what the hive already wrote into the pages. The last
// admin of a class can't leave: the server says so and it is shown here.
const name = ref(profile.value?.name ?? '')
const saving = ref(false)
const saved = ref(false)
const nameError = ref('')
const deleteError = ref('')

async function saveName() {
  const next = name.value.trim()
  if (!next || next === profile.value?.name) return
  saving.value = true
  saved.value = false
  nameError.value = ''
  try {
    profile.value = await api.updateMyName({ name: next })
    name.value = profile.value.name
    saved.value = true
  } catch (e) {
    nameError.value = e.message || t('common.somethingWrongLong')
  } finally {
    saving.value = false
  }
}

// The square shows a failure itself; the reason is also written under the row.
async function deleteAccount() {
  deleteError.value = ''
  try {
    await api.deleteMyAccount()
  } catch (e) {
    deleteError.value = e.message || t('common.somethingWrongLong')
    throw e
  }
  await signOut()
  router.push('/login')
}

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

        <h2 id="profile" class="mt-12 text-label font-medium text-fg">{{ t('settings.account') }}</h2>

        <form class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5" @submit.prevent="saveName">
          <div class="flex min-w-0 max-w-sm flex-col gap-1">
            <h3 class="text-label font-medium text-fg">{{ t('settings.name') }}</h3>
            <p class="text-label text-fg-secondary">{{ t('settings.nameHint') }}</p>
          </div>
          <div class="flex w-full items-center gap-2 sm:w-80">
            <Input
              v-model="name"
              class="min-w-0 flex-1"
              :aria-label="t('settings.name')"
              autocomplete="name"
              maxlength="80"
              required
              @input="saved = false"
            />
            <Button
              type="submit"
              :loading="saving"
              :disabled="!name.trim() || name.trim() === profile?.name"
            >
              {{ t('common.save') }}
            </Button>
          </div>
          <StatusText v-if="saved" class="w-full" :text="t('settings.nameSaved')" />
          <StatusText v-if="nameError" class="w-full" :text="nameError" error />
        </form>

        <Separator />

        <section class="flex flex-wrap items-center justify-between gap-x-8 gap-y-3 py-5">
          <div class="flex min-w-0 max-w-sm flex-col gap-1">
            <h3 class="text-label font-medium text-fg">{{ t('settings.deleteAccount') }}</h3>
            <p class="text-label text-fg-secondary">{{ t('settings.deleteHint') }}</p>
          </div>
          <ConfirmButton
            variant="ghost"
            tone="danger"
            :label="t('settings.deleteAccount')"
            :confirm-label="t('settings.deleteConfirm')"
            :cancel-label="t('common.cancel')"
            :action="deleteAccount"
          />
          <StatusText v-if="deleteError" class="w-full" :text="deleteError" error />
        </section>

        <ConnectAI />
      </div>
    </PageLayout>
  </main>
</template>
