<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { StatusText, Switch } from 'elastic-ui'
import AdminSetting from './AdminSetting.vue'
import { api } from '../lib/api.js'

const { t } = useI18n()
const enabled = ref(true)
const ready = ref(false)
const error = ref('')
onMounted(async () => {
  try {
    enabled.value = (await api.settings()).export_enabled
    ready.value = true
  } catch (e) { error.value = e.message }
})
async function save(value) {
  error.value = ''
  try { enabled.value = (await api.updateSettings({ exportEnabled: value })).export_enabled }
  catch (e) { error.value = e.message }
}
</script>
<template>
  <AdminSetting :title="t('export.title')">
    <Switch v-if="ready" :model-value="enabled" @update:model-value="save">{{ t('export.enabled') }}</Switch>
    <StatusText v-if="error" :text="error" error />
  </AdminSetting>
</template>
