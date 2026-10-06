<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ActionButton, DayStrip, StatusText, Switch, WeekPillbox } from 'elastic-ui'
import { api } from '../lib/api.js'

// When the daily pass runs: on or off, the times and the weekdays, all in Madrid time. Every
// change is saved at once and without a word: the next-pass line is the answer, and it follows the
// change. It goes back to what was saved if the backend refuses it. "Run now" starts the pass in the background; the AI log shows it.
const { t, locale } = useI18n()

const ZONE = 'Europe/Madrid'

const enabled = ref(true)
const times = ref([])
const days = ref([])
const loading = ref(true)
const loadError = ref('')
const saveError = ref('')
const saving = ref(false)

async function load() {
  try {
    apply(await api.settings())
  } catch (e) {
    loadError.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

function apply(settings) {
  enabled.value = settings.pass_enabled
  times.value = settings.pass_times
  days.value = settings.pass_days
}

// One save at a time; a change made while one is in flight is saved right after it.
let queued = null
async function save(patch) {
  if (saving.value) {
    queued = { ...queued, ...patch }
    return
  }
  const before = { enabled: enabled.value, times: times.value, days: days.value }
  saveError.value = ''
  saving.value = true
  try {
    apply(await api.updateSettings(patch))
  } catch (e) {
    ;({ enabled: enabled.value, times: times.value, days: days.value } = before)
    saveError.value = e.message || t('common.somethingWrongLong')
  } finally {
    saving.value = false
  }
  if (queued) {
    const next = queued
    queued = null
    await save(next)
  }
}

// The strip hands over sorted "HH:MM" times, only once a knob is let go.
function setTimes(list) {
  times.value = list
  save({ passTimes: list })
}

function setDays(list) {
  days.value = list
  save({ passDays: list })
}

// The pillbox's line, in the class's words.
const dayWords = computed(() => ({
  everyDay: t('admin.pass.words.everyDay'),
  weekdays: t('admin.pass.words.weekdays'),
  weekends: t('admin.pass.words.weekends'),
  none: t('admin.pass.words.none'),
}))

// The next slot, from the settings alone: today's later times, or the next chosen day.
const next = computed(() => {
  if (!enabled.value || !times.value.length || !days.value.length) return null
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat('en-GB', {
      timeZone: ZONE,
      weekday: 'short',
      hour: '2-digit',
      minute: '2-digit',
      hourCycle: 'h23',
    })
      .formatToParts(new Date())
      .map((p) => [p.type, p.value]),
  )
  const today = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].indexOf(parts.weekday) + 1
  const now = `${parts.hour}:${parts.minute}`
  for (let ahead = 0; ahead <= 7; ahead++) {
    const day = ((today - 1 + ahead) % 7) + 1
    if (!days.value.includes(day)) continue
    const time = times.value.find((x) => ahead > 0 || x > now)
    if (time) return { ahead, day, time }
  }
  return null
})

const nextText = computed(() => {
  if (!enabled.value) return t('admin.pass.off')
  if (!next.value) return t('admin.pass.none')
  const { ahead, day, time } = next.value
  const label = ahead === 0 ? t('admin.pass.today') : ahead === 1 ? t('admin.pass.tomorrow') : t(`admin.pass.dayLong.${day}`)
  return t('admin.pass.next', { day: label, time })
})

// The button's failed state says why: another pass is running, or something else went wrong.
const runFailed = ref('')

async function runNow() {
  runFailed.value = t('common.somethingWrong')
  const result = await api.runPass()
  if (result.status === 'already_running') {
    runFailed.value = t('admin.pass.alreadyRunning')
    throw new Error(runFailed.value)
  }
}

onMounted(load)
</script>

<template>
  <section class="flex flex-col gap-8 py-6">
    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />

    <template v-else>
      <div class="flex items-center justify-between gap-4">
        <h3 class="m-0 text-label text-fg">{{ t('admin.pass.title') }}</h3>
        <Switch :model-value="enabled" :aria-label="t('admin.pass.enabled')" @update:model-value="(on) => save({ passEnabled: on })" />
      </div>

      <div v-if="enabled" class="grid gap-8 md:grid-cols-2 md:gap-12">
        <div class="flex min-w-0 flex-col gap-3">
          <h4 class="m-0 text-label text-fg">{{ t('admin.pass.days') }}</h4>
          <WeekPillbox
            :model-value="days"
            :locale="locale"
            :label="t('admin.pass.daysLabel')"
            :words="dayWords"
            @update:model-value="setDays"
          />
        </div>
        <div class="flex min-w-0 flex-col gap-3">
          <h4 class="m-0 text-label text-fg">{{ t('admin.pass.times') }}</h4>
          <DayStrip
            v-model="times"
            :step="60"
            :label="t('admin.pass.times')"
            :add-label="t('admin.pass.addTime')"
            @changed="setTimes"
          />
        </div>
      </div>

      <StatusText v-if="saveError" :text="saveError" error />

      <div class="flex items-center justify-between gap-4">
        <StatusText class="text-label text-fg-secondary" :text="nextText" />
        <ActionButton
          icon="play"
          :label="t('admin.pass.runNow')"
          :done-label="t('admin.pass.started')"
          :error-label="runFailed || t('common.somethingWrong')"
          :action="runNow"
        />
      </div>
    </template>
  </section>
</template>
