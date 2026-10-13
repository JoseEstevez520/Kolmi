<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Timetable } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// create / update / delete_schedule_event: the week's blocks with the one that changes lit,
// green when it is added or changed and red when it goes.
const props = defineProps({
  tool: { type: String, default: 'create_schedule_event' },
  args: { type: Object, default: () => ({}) },
})
const { locale } = useI18n()
const data = usePreviewData()
data.ensure.nodes()
data.ensure.schedule()

const settings = computed(() => data.schedule.value?.settings)
// Timetable wants the days as names, Monday first, from the locale as the schedule screen does.
const dayNames = computed(() =>
  [...(settings.value?.schedule_days ?? [])]
    .sort((a, b) => a - b)
    .map((iso) => new Intl.DateTimeFormat(locale.value, { weekday: 'long' }).format(new Date(2026, 0, 4 + iso))),
)

const toBlock = (e, color) => ({
  id: e.id,
  day: e.day,
  start: e.start_time,
  end: e.end_time,
  title: e.title || '',
  detail: e.detail || undefined,
  color: color ?? (e.color || undefined),
})

const GREEN = 'var(--color-success)'
const RED = 'var(--color-danger)'

const events = computed(() => {
  const all = data.schedule.value?.events ?? []
  const { event_id: id } = props.args
  if (props.tool === 'delete_schedule_event') return all.map((e) => toBlock(e, e.id === id ? RED : undefined))
  if (props.tool === 'update_schedule_event') {
    const old = all.find((e) => e.id === id)
    if (!old) return null
    const patch = Object.fromEntries(Object.entries(props.args).filter(([, v]) => v !== undefined && v !== null))
    return all.map((e) => (e.id === id ? toBlock({ ...e, ...patch }, GREEN) : toBlock(e)))
  }
  const node = flatten(data.nodes.value).find((n) => n.id === props.args.node_id)
  const added = {
    id: 'new',
    day: props.args.day,
    start_time: props.args.start_time,
    end_time: props.args.end_time,
    title: props.args.title || node?.title,
    detail: props.args.detail,
  }
  return [...all.map((e) => toBlock(e)), toBlock(added, GREEN)]
})
const ready = computed(() => settings.value && events.value && dayNames.value.length)
</script>

<template>
  <Timetable
    v-if="ready"
    :days="dayNames"
    :start="settings.schedule_start"
    :end="settings.schedule_end"
    :events="events"
    :breaks="settings.schedule_breaks"
    :session-minutes="settings.schedule_session_minutes"
    still
  />
</template>
