<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, Empty, StatusText, Timetable } from 'elastic-ui'
import { CalendarDays } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'

// The class's own weekly timetable (not the daily pass's schedule, in Settings), set up by
// an admin. An empty state until it is, same as the home with nothing on it yet.
const { t } = useI18n()

const settings = ref(null)
const events = ref([])
const loading = ref(true)
const error = ref('')

async function load() {
  try {
    const [loadedSettings, loadedEvents] = await Promise.all([api.settings(), api.scheduleEvents()])
    settings.value = loadedSettings
    events.value = loadedEvents
  } catch (e) {
    error.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

const timetableEvents = computed(() =>
  events.value.map((event) => ({
    day: event.day,
    start: event.start_time,
    end: event.end_time,
    title: event.title || '',
    detail: event.detail || undefined,
    color: event.color || undefined,
    to: event.to,
  })),
)

const timetableBreaks = computed(() => settings.value?.schedule_breaks ?? [])

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('schedule.title')" :lead="t('schedule.lead')">
      <StatusText v-if="loading" :delay="300" :text="t('common.loadingContent')" working />
      <Callout v-else-if="error" type="caution" :title="t('common.contentError')">{{ error }}</Callout>
      <Empty
        v-else-if="!settings.schedule_enabled"
        :title="t('common.nothingHere')"
        :description="t('schedule.empty')"
        :icon="CalendarDays"
      />
      <Timetable
        v-else
        :days="settings.schedule_days"
        :start="settings.schedule_start"
        :end="settings.schedule_end"
        :events="timetableEvents"
        :breaks="timetableBreaks"
      />
    </PageLayout>
  </main>
</template>
