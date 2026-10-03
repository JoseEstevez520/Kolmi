<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ActionButton, Field, StatusText, Switch, TagsInput, ToggleGroup, ToggleGroupItem } from 'elastic-ui'
import { api } from '../lib/api.js'

// When the daily pass runs: on or off, the times and the weekdays, all in Madrid time. Every
// change is saved at once, as in the class language block, and goes back to what was saved if
// the backend refuses it. "Run now" starts the pass in the background; the AI log shows it.
const { t } = useI18n()

const ZONE = 'Europe/Madrid'
const ALL_DAYS = [1, 2, 3, 4, 5, 6, 7]

const enabled = ref(true)
const times = ref([])
const days = ref([])
const loading = ref(true)
const loadError = ref('')
const saveError = ref('')
const status = ref('')
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

async function save(patch) {
  if (saving.value) return
  const before = { enabled: enabled.value, times: times.value, days: days.value }
  saveError.value = ''
  saving.value = true
  status.value = t('admin.pass.saving')
  try {
    apply(await api.updateSettings(patch))
    status.value = t('admin.pass.saved')
  } catch (e) {
    ;({ enabled: enabled.value, times: times.value, days: days.value } = before)
    status.value = ''
    saveError.value = e.message || t('common.somethingWrongLong')
  } finally {
    saving.value = false
  }
}

// "3:00" becomes "03:00"; what is not a time is left out.
function normalise(text) {
  const match = /^(\d{1,2}):(\d{2})$/.exec(String(text).trim())
  if (!match || +match[1] > 23 || +match[2] > 59) return null
  return `${match[1].padStart(2, '0')}:${match[2]}`
}

function setTimes(list) {
  const clean = [...new Set(list.map(normalise).filter(Boolean))].sort()
  saveError.value = clean.length < list.length ? t('admin.pass.timesInvalid') : ''
  times.value = clean
  save({ passTimes: clean })
}

function setDays(list) {
  const clean = (list || []).map(Number).sort()
  days.value = clean
  save({ passDays: clean })
}

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
  <section class="flex flex-col gap-4">
    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
    <StatusText v-else-if="loadError" :text="loadError" error />

    <template v-else>
      <Field :description="t('admin.pass.hint')" :error="saveError">
        <Switch :model-value="enabled" @update:model-value="(on) => save({ passEnabled: on })">
          {{ t('admin.pass.enabled') }}
        </Switch>
      </Field>

      <template v-if="enabled">
        <Field :label="t('admin.pass.times')" :description="t('admin.pass.timesHint')">
          <TagsInput
            :model-value="times"
            :placeholder="t('admin.pass.timesPlaceholder')"
            :max="6"
            @update:model-value="setTimes"
          />
        </Field>

        <Field :label="t('admin.pass.days')">
          <ToggleGroup
            type="multiple"
            :model-value="days.map(String)"
            :aria-label="t('admin.pass.daysLabel')"
            @update:model-value="setDays"
          >
            <ToggleGroupItem v-for="day in ALL_DAYS" :key="day" :value="String(day)">
              {{ t(`admin.pass.dayShort.${day}`) }}
            </ToggleGroupItem>
          </ToggleGroup>
        </Field>
      </template>

      <StatusText :text="status || nextText" :working="saving" />

      <div class="flex flex-col items-start gap-2">
        <ActionButton
          icon="play"
          :label="t('admin.pass.runNow')"
          :done-label="t('admin.pass.started')"
          :error-label="runFailed || t('common.somethingWrong')"
          :action="runNow"
        />
        <p class="text-meta text-fg-muted">{{ t('admin.pass.runHint') }}</p>
      </div>
    </template>
  </section>
</template>
