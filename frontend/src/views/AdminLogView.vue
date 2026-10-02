<script setup>
import { computed, onMounted, ref } from 'vue'
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
} from 'elastic-ui'
import { Bot, History, NotebookPen } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'
import { formatDate, noteStatusLabel } from '../lib/format.js'

// The AI log, for admins: the recent passes, what the pass did with each note
// or page, and the notes it worked from. Read like a record: quiet tables, and
// colour only where it says an outcome (elastic-ui USAGE 8).
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

const PASS_LABELS = { running: 'Running', done: 'Done', failed: 'Failed' }
const ACTION_LABELS = { created: 'Created', updated: 'Updated', discarded: 'Discarded', flagged: 'Flagged' }

const nodeTitles = computed(() => {
  const titles = new Map()
  for (const node of flatten(tree.value)) titles.set(node.id, node.title)
  return titles
})

function nodeTitle(id) {
  if (id == null) return ''
  return nodeTitles.value.get(id) || `Node #${id}`
}

function entryTarget(entry) {
  if (entry.node_id != null) return nodeTitle(entry.node_id)
  if (entry.note_id != null) return `Note #${entry.note_id}`
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
  if (stats.notes != null) parts.push(`${stats.notes} notes`)
  for (const key of ['created', 'updated', 'discarded', 'flagged']) {
    if (stats[key] != null) parts.push(`${stats[key]} ${key}`)
  }
  return parts.join(' · ')
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
    error.value = e.message || 'Could not load the AI log.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout title="AI log" lead="What the pass read, what it changed, and the notes it worked from.">
      <StatusText v-if="loading" text="Loading the AI log…" working />

      <Callout v-else-if="error" type="caution" title="Could not load the AI log">
        {{ error }}
      </Callout>

      <template v-else>
        <h2 id="passes">Recent passes</h2>
        <Empty
          v-if="passes.length === 0"
          title="No passes yet"
          description="The first nightly pass will show up here."
          :icon="History"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>Recent AI passes, newest first.</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>Pass</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Finished</TableHead>
                <TableHead class="w-1/3">Result</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="pass in passes" :key="pass.id">
                <TableCell class="tabular-nums text-fg">#{{ pass.id }}</TableCell>
                <TableCell>
                  <Badge :color="PASS_TONES[pass.status]">{{ PASS_LABELS[pass.status] ?? pass.status }}</Badge>
                </TableCell>
                <TableCell class="text-fg-secondary">{{ pass.model || '—' }}</TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ formatDate(pass.started_at) || '—' }}
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ pass.finished_at ? formatDate(pass.finished_at) : '—' }}
                </TableCell>
                <TableCell :class="pass.error ? 'text-danger' : 'text-fg-secondary'">
                  <div class="max-w-xs overflow-hidden whitespace-nowrap mask-fade-r">
                    {{ passResult(pass) || '—' }}
                  </div>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <h2 id="activity" class="mt-10">AI activity</h2>
        <Empty
          v-if="entries.length === 0"
          title="Nothing logged yet"
          description="Every note and page the pass touches will be listed here."
          :icon="Bot"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>Every note and page the pass touched, newest first.</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Reason</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="entry in entries" :key="entry.id">
                <TableCell>
                  <Badge :color="ACTION_TONES[entry.action]">
                    {{ ACTION_LABELS[entry.action] ?? entry.action }}
                  </Badge>
                </TableCell>
                <TableCell class="text-fg">{{ entryTarget(entry) }}</TableCell>
                <TableCell class="text-fg-secondary">
                  <span class="block max-w-md overflow-hidden whitespace-nowrap mask-fade-r">
                    {{ entry.reason || '—' }}
                  </span>
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ formatDate(entry.created_at) || '—' }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>

        <h2 id="notes" class="mt-10">Received notes</h2>
        <Empty
          v-if="notes.length === 0"
          title="No notes yet"
          description="Notes students leave will appear here with their status."
          :icon="NotebookPen"
        />
        <div v-else class="not-prose">
          <Table>
            <TableCaption>The notes students left, newest first.</TableCaption>
            <TableHeader>
              <TableRow>
                <TableHead>Note</TableHead>
                <TableHead>From</TableHead>
                <TableHead>Node</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow v-for="note in notes" :key="note.id">
                <TableCell class="text-fg-secondary">
                  <span class="block max-w-md overflow-hidden whitespace-nowrap mask-fade-r">
                    {{ note.content || '—' }}
                  </span>
                </TableCell>
                <TableCell class="text-fg">{{ authorOf(note) }}</TableCell>
                <TableCell class="text-fg-secondary">
                  {{ note.node_id != null ? nodeTitle(note.node_id) : '—' }}
                </TableCell>
                <TableCell>
                  <Badge :color="NOTE_TONES[note.status]">{{ noteStatusLabel(note.status) }}</Badge>
                </TableCell>
                <TableCell class="whitespace-nowrap text-fg-muted">
                  {{ formatDate(note.created_at) || '—' }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </template>
    </PageLayout>
  </main>
</template>
