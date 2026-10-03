<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Field, Select, SelectContent, SelectItem, SelectTrigger, SelectValue, StatusText } from 'elastic-ui'
import AdminSetting from './AdminSetting.vue'
import { api } from '../lib/api.js'

// The class language: the one the daily pass writes the shared notes and pages in, whatever
// language each note comes in. One value for the whole class, set here by an admin and kept in
// the backend; each person's own UI language lives in Settings and is not this. A pick is saved
// at once, as in Settings, and goes back to what was saved if the backend refuses it.
const { t, te } = useI18n()

const language = ref('')
const languages = ref([])
const loading = ref(true)
const loadError = ref('')
const saveError = ref('')
const status = ref('')
const saving = ref(false)

function languageName({ code, name }) {
  const key = `admin.classLanguage.names.${code}`
  return te(key) ? t(key) : name
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const settings = await api.settings()
    language.value = settings.class_language
    languages.value = settings.languages
  } catch (e) {
    loadError.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

async function save(code) {
  if (saving.value || !code || code === language.value) return
  const previous = language.value
  language.value = code
  saveError.value = ''
  saving.value = true
  status.value = t('admin.classLanguage.saving')
  try {
    const settings = await api.updateSettings({ classLanguage: code })
    language.value = settings.class_language
    status.value = t('admin.classLanguage.saved')
  } catch (e) {
    language.value = previous
    status.value = ''
    saveError.value = e.message || t('common.somethingWrongLong')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <AdminSetting :title="t('admin.classLanguage.label')" :description="t('admin.classLanguage.hint')">
    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />

    <template v-else>
      <Field :error="saveError" class="w-full">
        <Select :model-value="language" @update:model-value="save">
          <SelectTrigger :aria-label="t('admin.classLanguage.label')">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="option in languages" :key="option.code" :value="option.code">
              {{ languageName(option) }}
            </SelectItem>
          </SelectContent>
        </Select>
      </Field>
      <StatusText v-if="status" :text="status" :working="saving" />
    </template>
  </AdminSetting>
</template>
