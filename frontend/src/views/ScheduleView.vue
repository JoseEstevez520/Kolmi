<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Empty, Field, Input, StatusText, Switch, Timetable } from 'elastic-ui'
import { CalendarDays, Plus, X } from '@lucide/vue'
import NodePicker from '../components/NodePicker.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'

// The class's own weekly timetable (not the daily pass's, in Admin): everyone sees it here; an
// admin edits it right on the same page, the grid itself (elastic-ui's Timetable, editable): drag
// an empty cell to lay a class down, drag a block to move it, drag its edge to lengthen or
// shorten it (snapped to a whole session), click to select it and fill its title, detail or page
// in the panel below. A gesture only tells what it would change; this is what calls the backend.
const { t } = useI18n()
const isAdmin = computed(() => profile.value?.role === 'admin')

const enabled = ref(false)
const days = ref([])
const start = ref('08:10')
const end = ref('15:20')
const sessionMinutes = ref(50)
const breaks = ref([])
const events = ref([])
const loading = ref(true)
const error = ref('')
const saveError = ref('')

async function load() {
  try {
    const [settings, loadedEvents] = await Promise.all([api.settings(), api.scheduleEvents()])
    apply(settings)
    events.value = loadedEvents
  } catch (e) {
    error.value = e.message || t('common.somethingWrongLong')
  } finally {
    loading.value = false
  }
}

function apply(settings) {
  enabled.value = settings.schedule_enabled
  days.value = settings.schedule_days
  start.value = settings.schedule_start
  end.value = settings.schedule_end
  sessionMinutes.value = settings.schedule_session_minutes
  breaks.value = settings.schedule_breaks
}

// One save at a time; a change made while one is in flight is saved right after it.
let saving = false
let queued = null
async function save(patch) {
  if (saving) {
    queued = { ...queued, ...patch }
    return
  }
  const before = { enabled: enabled.value, days: days.value, start: start.value, end: end.value, sessionMinutes: sessionMinutes.value, breaks: breaks.value }
  saveError.value = ''
  saving = true
  try {
    apply(await api.updateSettings(patch))
  } catch (e) {
    ;({ enabled: enabled.value, days: days.value, start: start.value, end: end.value, sessionMinutes: sessionMinutes.value, breaks: breaks.value } = before)
    saveError.value = e.message || t('common.somethingWrongLong')
  } finally {
    saving = false
  }
  if (queued) {
    const next = queued
    queued = null
    await save(next)
  }
}

function addDay() {
  days.value = [...days.value, '']
  save({ scheduleDays: days.value })
}
function setDay(i, value) {
  days.value = days.value.map((d, idx) => (idx === i ? value : d))
  save({ scheduleDays: days.value })
}
function removeDay(i) {
  days.value = days.value.filter((_, idx) => idx !== i)
  save({ scheduleDays: days.value })
}

function addBreak() {
  breaks.value = [...breaks.value, { start: '11:30', end: '12:00', label: '' }]
  save({ scheduleBreaks: breaks.value })
}
function setBreak(i, patch) {
  breaks.value = breaks.value.map((b, idx) => (idx === i ? { ...b, ...patch } : b))
  save({ scheduleBreaks: breaks.value })
}
function removeBreak(i) {
  breaks.value = breaks.value.filter((_, idx) => idx !== i)
  save({ scheduleBreaks: breaks.value })
}

// The slots: the grid is the editor, for an admin. A gesture only tells what it would change.
const timetableEvents = computed(() =>
  events.value.map((e) => ({
    id: e.id,
    day: e.day,
    start: e.start_time,
    end: e.end_time,
    title: e.title || (isAdmin.value ? t('admin.schedule.untitled') : ''),
    detail: e.detail || undefined,
    color: e.color || undefined,
    to: e.to,
  })),
)

const selectedId = ref(null)
const selected = computed(() => events.value.find((e) => e.id === selectedId.value) ?? null)

async function onCreate({ day, start: startTime, end: endTime }) {
  try {
    const created = await api.createScheduleEvent({ day, startTime, endTime })
    events.value = [...events.value, created]
    selectedId.value = created.id
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onMove(id, day, startTime, endTime) {
  try {
    const updated = await api.updateScheduleEvent({ eventId: id, day, startTime, endTime })
    events.value = events.value.map((e) => (e.id === id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onResize(id, startTime, endTime) {
  try {
    const updated = await api.updateScheduleEvent({ eventId: id, startTime, endTime })
    events.value = events.value.map((e) => (e.id === id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onRemove(id) {
  events.value = events.value.filter((e) => e.id !== id)
  if (selectedId.value === id) selectedId.value = null
  try {
    await api.deleteScheduleEvent({ eventId: id })
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

// No optimistic local update here: the fields it touches (nodeId, title, detail) are
// camelCase on the wire but snake_case in `events`, so it waits for the real row back.
async function patchSelected(patch) {
  if (!selected.value) return
  try {
    const updated = await api.updateScheduleEvent({ eventId: selected.value.id, ...patch })
    events.value = events.value.map((e) => (e.id === updated.id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('schedule.title')" :lead="t('schedule.lead')">
      <StatusText v-if="loading" :delay="300" :text="t('common.loadingContent')" working />
      <Callout v-else-if="error" type="caution" :title="t('common.contentError')">{{ error }}</Callout>

      <template v-else>
        <template v-if="isAdmin">
          <div class="flex items-center justify-between gap-4">
            <span class="text-label text-fg">{{ t('admin.schedule.enabled') }}</span>
            <Switch :model-value="enabled" :aria-label="t('admin.schedule.enabled')" @update:model-value="(on) => save({ scheduleEnabled: on })" />
          </div>
        </template>

        <Empty
          v-if="!enabled && !isAdmin"
          :title="t('common.nothingHere')"
          :description="t('schedule.empty')"
          :icon="CalendarDays"
        />

        <template v-else-if="enabled || isAdmin">
          <template v-if="isAdmin">
            <div class="flex flex-col gap-3">
              <h3 class="m-0 text-label text-fg">{{ t('admin.schedule.shape') }}</h3>
              <div class="grid gap-4 sm:grid-cols-3">
                <Field :label="t('admin.schedule.start')">
                  <Input type="time" :model-value="start" @change="(e) => save({ scheduleStart: e.target.value })" />
                </Field>
                <Field :label="t('admin.schedule.end')">
                  <Input type="time" :model-value="end" @change="(e) => save({ scheduleEnd: e.target.value })" />
                </Field>
                <Field :label="t('admin.schedule.sessionMinutes')">
                  <Input type="number" min="5" step="5" :model-value="sessionMinutes" @change="(e) => save({ scheduleSessionMinutes: Number(e.target.value) })" />
                </Field>
              </div>

              <Field :label="t('admin.schedule.days')">
                <div class="flex flex-col gap-2">
                  <div v-for="(day, i) in days" :key="i" class="flex items-center gap-2">
                    <Input :model-value="day" class="flex-1" @change="(e) => setDay(i, e.target.value)" />
                    <Button variant="ghost" size="icon" :icon="X" :aria-label="t('admin.schedule.removeDay', { day })" @click="removeDay(i)" />
                  </div>
                  <Button variant="ghost" size="sm" :icon="Plus" @click="addDay">{{ t('admin.schedule.addDay') }}</Button>
                </div>
              </Field>
            </div>

            <div class="flex flex-col gap-3">
              <h3 class="m-0 text-label text-fg">{{ t('admin.schedule.breaks') }}</h3>
              <div v-for="(b, i) in breaks" :key="i" class="flex items-center gap-2">
                <Input type="time" class="w-28" :model-value="b.start" @change="(e) => setBreak(i, { start: e.target.value })" />
                <Input type="time" class="w-28" :model-value="b.end" @change="(e) => setBreak(i, { end: e.target.value })" />
                <Input class="flex-1" :placeholder="t('admin.schedule.breakLabel')" :model-value="b.label" @change="(e) => setBreak(i, { label: e.target.value })" />
                <Button variant="ghost" size="icon" :icon="X" :aria-label="t('admin.schedule.removeBreak')" @click="removeBreak(i)" />
              </div>
              <Button variant="ghost" size="sm" :icon="Plus" @click="addBreak">{{ t('admin.schedule.addBreak') }}</Button>
            </div>

            <p class="m-0 text-ui text-fg-muted">{{ t('admin.schedule.slotsHint') }}</p>
          </template>

          <Timetable
            :days="days"
            :start="start"
            :end="end"
            :events="timetableEvents"
            :breaks="breaks"
            :session-minutes="sessionMinutes"
            :editable="isAdmin"
            @create="onCreate"
            @move="onMove"
            @resize="onResize"
            @remove="onRemove"
            @select="(id) => (selectedId = id)"
          />

          <div v-if="isAdmin && selected" class="flex flex-wrap items-end gap-3 rounded-[var(--radius-md)] bg-surface-sunk p-3">
            <NodePicker
              :model-value="selected.node_id"
              :placeholder="t('admin.schedule.slotPagePlaceholder')"
              :none-label="t('admin.schedule.slotPageNone')"
              :label="t('admin.schedule.slotPage')"
              @update:model-value="(v) => patchSelected({ nodeId: v })"
            />
            <Field :label="t('admin.schedule.slotTitle')">
              <Input :model-value="selected.title" @change="(e) => patchSelected({ title: e.target.value || null })" />
            </Field>
            <Field :label="t('admin.schedule.slotDetail')">
              <Input :model-value="selected.detail" @change="(e) => patchSelected({ detail: e.target.value || null })" />
            </Field>
            <Button variant="ghost" size="icon" :icon="X" :aria-label="t('admin.schedule.removeSlot')" @click="onRemove(selected.id)" />
          </div>
        </template>

        <StatusText v-if="saveError" :text="saveError" error />
      </template>
    </PageLayout>
  </main>
</template>
