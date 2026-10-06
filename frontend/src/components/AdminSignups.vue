<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { StatusText, Switch } from 'elastic-ui'
import AdminSetting from './AdminSetting.vue'
import { api } from '../lib/api.js'

// Whether someone who joins with the class code still has to be approved: off until an admin
// turns it on, for when the code leaks. Saved at once and without a word, as the chat is. Those
// waiting are approved in the Users block.
const { t } = useI18n()

const enabled = ref(false)
const loading = ref(true)
const loadError = ref('')
const saveError = ref('')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    enabled.value = Boolean((await api.settings()).signups_need_approval)
  } catch (e) {
    loadError.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

async function save(on) {
  const before = enabled.value
  saveError.value = ''
  try {
    const settings = await api.updateSettings({ signupsNeedApproval: on })
    enabled.value = Boolean(settings.signups_need_approval)
  } catch (e) {
    enabled.value = before
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

onMounted(load)
</script>

<template>
  <AdminSetting :title="t('admin.signups.title')" :description="t('admin.signups.hint')">
    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />

    <template v-else>
      <Switch :model-value="enabled" @update:model-value="save">
        {{ t('admin.signups.enabled') }}
      </Switch>
      <StatusText v-if="saveError" :text="saveError" error />
    </template>
  </AdminSetting>
</template>
