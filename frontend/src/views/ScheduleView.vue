<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Field, Input, Sheet, SheetTitle, StatusText, Switch, Timetable, Toggle, WeekPillbox } from 'elastic-ui'
import { CalendarDays, Pencil, Plus, SlidersHorizontal, X } from '@lucide/vue'
import NodePicker from '../components/NodePicker.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { invalidate, useCached } from '../lib/cached.js'

// The class's own weekly timetable (not the daily pass's, in Admin): everyone sees the week and
// nothing else. An admin has two icons up in the page's actions: the settings (a Sheet) and the
// edit mode, which makes the grid (elastic-ui's Timetable) editable: drag an empty cell to lay a
// class down, drag a block to move it, drag its edge to lengthen or shorten it (snapped to a
// whole session), click to select it and fill its title, detail or page in the panel below. A gesture only tells what it would change; this is what calls the backend.
const { t, locale } = useI18n()
const isAdmin = computed(() => profile.value?.role === 'admin')

const enabled = ref(false)
// ISO weekdays (1 Monday to 7 Sunday), the same shape as the pass's own days, picked the same
// way with WeekPillbox. Their display names (for Timetable's `days`) come from the locale.
const days = ref([])
const start = ref('08:10')
const end = ref('15:20')
const sessionMinutes = ref(50)
const breaks = ref([])
const events = ref([])
const saveError = ref('')
// Edit mode: the grid is read-only until an admin turns it on.
const editing = ref(false)

// The last answer draws at once and a quiet refetch follows (lib/cached.js). Once the person
// edits something, the screen's own state is the truth: a late answer no longer replaces it.
const { data, loading, error, refresh } = useCached('schedule')
let touched = false
watch(
  data,
  (answer) => {
    if (!answer || touched) return
    apply(answer.settings)
    events.value = answer.events
  },
  { immediate: true },
)

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
    touched = true
    const answer = await api.updateSettings(patch)
    invalidate('schedule')
    // A change made while this one was saving comes next: its answer is the one to show, so this
    // one's, older, would put back for a moment what was just changed.
    if (!queued) apply(answer)
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

function setDays(list) {
  days.value = list
  save({ scheduleDays: list })
}

// The week's line, in the class's words (reused from the pass's own, the same four phrases).
const dayWords = computed(() => ({
  everyDay: t('admin.pass.words.everyDay'),
  weekdays: t('admin.pass.words.weekdays'),
  weekends: t('admin.pass.words.weekends'),
  none: t('admin.pass.words.none'),
}))

// Timetable wants the days as names, Monday first; a weekday's own name comes from the
// locale, read off a known Monday-starting week (2026-01-05), never typed by hand.
const dayNames = computed(() =>
  [...days.value]
    .sort((a, b) => a - b)
    .map((iso) => new Intl.DateTimeFormat(locale.value, { weekday: 'long' }).format(new Date(2026, 0, 4 + iso))),
)

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
    touched = true
    const created = await api.createScheduleEvent({ day, startTime, endTime })
    invalidate('schedule')
    events.value = [...events.value, created]
    selectedId.value = created.id
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onMove(id, day, startTime, endTime) {
  try {
    touched = true
    const updated = await api.updateScheduleEvent({ eventId: id, day, startTime, endTime })
    invalidate('schedule')
    events.value = events.value.map((e) => (e.id === id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onResize(id, startTime, endTime) {
  try {
    touched = true
    const updated = await api.updateScheduleEvent({ eventId: id, startTime, endTime })
    invalidate('schedule')
    events.value = events.value.map((e) => (e.id === id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

async function onRemove(id) {
  events.value = events.value.filter((e) => e.id !== id)
  if (selectedId.value === id) selectedId.value = null
  touched = true
  try {
    await api.deleteScheduleEvent({ eventId: id })
    invalidate('schedule')
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

// No optimistic local update here: the fields it touches (nodeId, title, detail) are
// camelCase on the wire but snake_case in `events`, so it waits for the real row back.
async function patchSelected(patch) {
  if (!selected.value) return
  try {
    touched = true
    const updated = await api.updateScheduleEvent({ eventId: selected.value.id, ...patch })
    invalidate('schedule')
    events.value = events.value.map((e) => (e.id === updated.id ? updated : e))
  } catch (e) {
    saveError.value = e.message || t('common.somethingWrongLong')
  }
}

onMounted(refresh)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('schedule.title')">
      <template v-if="isAdmin && !loading && !error" #actions>
        <div class="flex items-center gap-1">
          <Toggle v-model="editing" class="size-10" :aria-label="t('admin.schedule.edit')" :title="t('admin.schedule.edit')">
            <Pencil aria-hidden="true" class="size-4" />
          </Toggle>
          <Sheet variant="ghost" size="icon" :trigger-label="t('admin.schedule.settings')">
            <template #trigger><SlidersHorizontal aria-hidden="true" class="size-4" /></template>
            <SheetTitle class="sr-only">{{ t('admin.schedule.settings') }}</SheetTitle>
            <div class="flex flex-col gap-6">
              <div class="flex items-center gap-3">
                <CalendarDays aria-hidden="true" class="size-4 text-fg-muted" />
                <Switch :model-value="enabled" :aria-label="t('admin.schedule.enabled')" :title="t('admin.schedule.enabled')" @update:model-value="(on) => save({ scheduleEnabled: on })" />
              </div>

              <div class="grid grid-cols-2 gap-4">
                <Field :label="t('admin.schedule.start')">
                  <Input type="time" :model-value="start" @change="(e) => save({ scheduleStart: e.target.value })" />
                </Field>
                <Field :label="t('admin.schedule.end')">
                  <Input type="time" :model-value="end" @change="(e) => save({ scheduleEnd: e.target.value })" />
                </Field>
                <Field class="col-span-2" :label="t('admin.schedule.sessionMinutes')">
                  <Input type="number" min="5" step="5" :model-value="sessionMinutes" @change="(e) => save({ scheduleSessionMinutes: Number(e.target.value) })" />
                </Field>
              </div>

              <WeekPillbox
                :model-value="days"
                :locale="locale"
                :label="t('admin.schedule.days')"
                :words="dayWords"
                @update:model-value="setDays"
              />

              <div class="flex flex-col gap-3">
                <div v-for="(b, i) in breaks" :key="i" class="flex flex-wrap items-center gap-2">
                  <Input type="time" class="min-w-0 flex-1" :model-value="b.start" @change="(e) => setBreak(i, { start: e.target.value })" />
                  <Input type="time" class="min-w-0 flex-1" :model-value="b.end" @change="(e) => setBreak(i, { end: e.target.value })" />
                  <Input class="order-last w-full" :placeholder="t('admin.schedule.breakLabel')" :model-value="b.label" @change="(e) => setBreak(i, { label: e.target.value })" />
                  <Button variant="ghost" size="icon" :icon="X" :aria-label="t('admin.schedule.removeBreak')" @click="removeBreak(i)" />
                </div>
                <Button class="self-start" variant="ghost" size="icon" :icon="Plus" :aria-label="t('admin.schedule.addBreak')" :title="t('admin.schedule.addBreak')" @click="addBreak" />
              </div>

              <StatusText v-if="saveError" :text="saveError" error />
            </div>
          </Sheet>
        </div>
      </template>

      <StatusText v-if="loading" :delay="300" :text="t('common.loadingContent')" working />
      <Callout v-else-if="error" type="caution" :title="t('common.contentError')">{{ error }}</Callout>

      <template v-else-if="enabled || isAdmin">
        <Timetable
          :days="dayNames"
          :start="start"
          :end="end"
          :events="timetableEvents"
          :breaks="breaks"
          :session-minutes="sessionMinutes"
          :editable="isAdmin && editing"
          @create="onCreate"
          @move="onMove"
          @resize="onResize"
          @remove="onRemove"
          @select="(id) => (selectedId = id)"
        />

        <div v-if="isAdmin && editing && selected" class="flex flex-wrap items-end gap-3 rounded-[var(--radius-md)] bg-surface-sunk p-3">
          <NodePicker
            class="max-w-56"
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

        <StatusText v-if="saveError && !isAdmin" :text="saveError" error />
      </template>
    </PageLayout>
  </main>
</template>
