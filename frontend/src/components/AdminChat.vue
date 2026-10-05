<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { NumberField, StatusText, Switch } from 'elastic-ui'
import AdminSetting from './AdminSetting.vue'
import { api } from '../lib/api.js'

// The chat: off until an admin turns it on, and a daily message cap per student once it is.
// It runs on the instance's own model (the gatekeeper's), reading only the class's own content.
// A change is saved at once and without a word, as the class language and Automatic are.
const { t } = useI18n()

const enabled = ref(false)
const dailyLimit = ref(20)
const loading = ref(true)
const loadError = ref('')
const saveError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const settings = await api.settings()
    enabled.value = settings.chat_enabled
    dailyLimit.value = settings.chat_daily_limit
  } catch (e) {
    loadError.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

async function save(patch) {
  const before = { enabled: enabled.value, dailyLimit: dailyLimit.value }
  saveError.value = ''
  try {
    const settings = await api.updateSettings(patch)
    enabled.value = settings.chat_enabled
    dailyLimit.value = settings.chat_daily_limit
  } catch (e) {
    ;({ enabled: enabled.value, dailyLimit: dailyLimit.value } = before)
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

onMounted(load)
</script>

<template>
  <AdminSetting :title="t('admin.chat.title')" :description="t('admin.chat.hint')">
    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />

    <template v-else>
      <Switch :model-value="enabled" @update:model-value="(on) => save({ chatEnabled: on })">
        {{ t('admin.chat.enabled') }}
      </Switch>
      <div v-if="enabled" class="flex w-full items-center justify-between gap-4">
        <span class="text-label text-fg-secondary">{{ t('admin.chat.dailyLimit') }}</span>
        <NumberField
          :model-value="dailyLimit"
          :min="1"
          :max="200"
          class="w-28"
          @update:model-value="(n) => n && save({ chatDailyLimit: n })"
        />
      </div>
      <StatusText v-if="saveError" :text="saveError" error />
    </template>
  </AdminSetting>
</template>
