<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Badge,
  Callout,
  Empty,
  StatusText,
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TruncatedText,
} from 'elastic-ui'
import { Bot, History, NotebookPen } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'
import { formatDuration, formatShortDate, noteStatusLabel } from '../lib/format.js'

// The AI log, for admins: the recent passes, what the pass did with each note
// or page, and the notes it worked from. Read like a record: quiet tables, and
// colour only where it says an outcome (elastic-ui USAGE 8).
const { t, te } = useI18n()

const passes = ref([])
const entries = ref([])
const notes = ref([])
const tree = ref([])
const loading = ref(true)
const error = ref('')

const PASS_TONES = {
  running: 'var(--color-warning)',
  done: 'var(--color-success)',
  failed: 'var(--color-danger)',
}

// Updated is the quiet one: it carries no outcome, so it keeps the grey badge.
const ACTION_TONES = {
  created: 'var(--color-success)',
  updated: '',
  discarded: 'var(--color-danger)',
  flagged: 'var(--color-warning)',
}

const NOTE_TONES = {
  pending: 'var(--color-warning)',
  processed: 'var(--color-success)',
  discarded: 'var(--color-danger)',
}

// A label looked up by a value from the backend; an unknown value shows as it came.
function label(group, value) {
  const key = `aiLog.${group}.${value}`
  return value && te(key) ? t(key) : value
}

const nodeTitles = computed(() => {
  const titles = new Map()
  for (const node of flatten(tree.value)) titles.set(node.id, node.title)
  return titles
})

function nodeTitle(id) {
  if (id == null) return ''
  return nodeTitles.value.get(id) || t('aiLog.node', { id })
}

function entryTarget(entry) {
  if (entry.node_id != null) return nodeTitle(entry.node_id)
  if (entry.note_id != null) return t('aiLog.note', { id: entry.note_id })
  return '—'
}

function authorOf(note) {
  const profile = Array.isArray(note.profiles) ? note.profiles[0] : note.profiles
  return profile?.name || '—'
}

// A pass's stats as one short line: the counts that say what it did.
function passResult(pass) {
  if (pass.error) return pass.error
  const stats = pass.stats ?? {}
  const parts = []
  for (const key of ['notes', 'created', 'updated', 'discarded', 'flagged']) {
    const n = stats[key]
    if (n != null) parts.push(t(`aiLog.stats.${key}`, { n }, n))
  }
  return parts.join(' · ')
}

// When a pass ran, in one cell: its start and how long it took, or that it is still going.
function passWhen(pass) {
  const start = formatShortDate(pass.started_at)
  if (!start) return '—'
  const length = pass.finished_at ? formatDuration(pass.started_at, pass.finished_at) : t('aiLog.running')
  return length ? `${start} · ${length}` : start
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [passList, log, noteList, content] = await Promise.all([
      api.adminPasses(),
      api.adminAiLog(),
      api.adminNotes(),
      loadNodes(),
    ])
    passes.value = Array.isArray(passList) ? passList : []
    entries.value = Array.isArray(log) ? log : []
    notes.value = Array.isArray(noteList) ? noteList : []
    tree.value = Array.isArray(content) ? content : []
  } catch (e) {
    error.value = e.message || t('aiLog.errorLong')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('aiLog.title')" :lead="t('aiLog.lead')">
      <StatusText v-if="loading" :delay="300" :text="t('aiLog.loading')" working />

      <Callout v-else-if="error" type="caution" :title="t('aiLog.error')">
        {{ error }}
      </Callout>

      <template v-else>
        <h2 id="passes">{{ t('aiLog.passes') }}</h2>
        <Empty
          v-if="passes.length === 0"
          :title="t('aiLog.passesEmptyTitle')"
          :description="t('aiLog.passesEmpty')"
          :icon="History"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>{{ t('aiLog.passesCaption') }}</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('aiLog.pass') }}</TableHead>
                <TableHead>{{ t('aiLog.status') }}</TableHead>
                <TableHead>{{ t('aiLog.when') }}</TableHead>
                <TableHead class="w-1/3">{{ t('aiLog.result') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="pass in passes" :key="pass.id">
                <TableCell>
                  <span class="block tabular-nums text-fg">#{{ pass.id }}</span>
                  <span v-if="pass.model" class="block text-xs text-fg-muted">{{ pass.model }}</span>
                </TableCell>
                <TableCell>
                  <Badge :color="PASS_TONES[pass.status]">{{ label('passStatus', pass.status) }}</Badge>
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">{{ passWhen(pass) }}</TableCell>
                <TableCell :class="pass.error ? 'text-danger' : 'text-fg-secondary'">
                  <TruncatedText as="div" class="max-w-xs">{{ passResult(pass) || '—' }}</TruncatedText>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <h2 id="activity" class="mt-10">{{ t('aiLog.activity') }}</h2>
        <Empty
          v-if="entries.length === 0"
          :title="t('aiLog.activityEmptyTitle')"
          :description="t('aiLog.activityEmpty')"
          :icon="Bot"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>{{ t('aiLog.activityCaption') }}</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('aiLog.action') }}</TableHead>
                <TableHead>{{ t('aiLog.target') }}</TableHead>
                <TableHead>{{ t('aiLog.when') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="entry in entries" :key="entry.id">
                <TableCell>
                  <Badge :color="ACTION_TONES[entry.action]">{{ label('actions', entry.action) }}</Badge>
                </TableCell>
                <TableCell>
                  <span class="block text-fg">{{ entryTarget(entry) }}</span>
                  <TruncatedText v-if="entry.reason" class="max-w-md text-xs text-fg-muted">{{ entry.reason }}</TruncatedText>
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ formatShortDate(entry.created_at) || '—' }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <h2 id="notes" class="mt-10">{{ t('aiLog.notes') }}</h2>
        <Empty
          v-if="notes.length === 0"
          :title="t('aiLog.notesEmptyTitle')"
          :description="t('aiLog.notesEmpty')"
          :icon="NotebookPen"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>{{ t('aiLog.notesCaption') }}</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>{{ t('aiLog.noteColumn') }}</TableHead>
                <TableHead>{{ t('aiLog.status') }}</TableHead>
                <TableHead>{{ t('aiLog.when') }}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="note in notes" :key="note.id">
                <TableCell>
                  <TruncatedText class="max-w-md text-fg-secondary">{{ note.content || '—' }}</TruncatedText>
                  <span class="block text-xs text-fg-muted">
                    {{ authorOf(note) }}<template v-if="note.node_id != null"> · {{ nodeTitle(note.node_id) }}</template>
                  </span>
                </TableCell>
                <TableCell>
                  <Badge :color="NOTE_TONES[note.status]">{{ noteStatusLabel(note.status) }}</Badge>
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ formatShortDate(note.created_at) || '—' }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </template>
    </PageLayout>
  </main>
</template>
