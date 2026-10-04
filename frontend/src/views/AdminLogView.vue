<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Empty, Status, StatusText, TruncatedText } from 'elastic-ui'
import { History } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'
import { formatDuration, formatShortDate } from '../lib/format.js'

// The AI log, for admins: the recent passes down the left, and what the chosen one did down the
// right. Read-only: it only shows what the backend already keeps. What needs a look (a pass that
// failed, a note the pass flagged) sits on top and narrows the list when pressed.
const { t, te } = useI18n()

const passes = ref([])
const notes = ref([])
const tree = ref([])
const loading = ref(true)
const error = ref('')

// Each value the backend sends, as the library's Status state. Discarded is a normal
// decision, so it is grey and not the danger colour; only a failure is red.
const PASS_STATES = { running: 'working', done: 'done', failed: 'error' }
const ACTION_STATES = { created: 'done', updated: 'done', discarded: 'discarded', flagged: 'flagged' }

// A label looked up by a value from the backend; an unknown value shows as it came.
function label(group, value) {
  const key = `aiLog.${group}.${value}`
  return value && te(key) ? t(key) : value
}

const nodeTitles = computed(() => new Map(flatten(tree.value).map((node) => [node.id, node.title])))
const noteById = computed(() => new Map(notes.value.map((note) => [note.id, note])))

// A stat is a count, or a list of what was counted (flagged notes, say).
const count = (value) => (Array.isArray(value) ? value.length : (value ?? 0))
const flaggedIn = (pass) => count(pass.stats?.flagged)

const failedCount = computed(() => passes.value.filter((pass) => pass.status === 'failed').length)
const flaggedCount = computed(() => passes.value.reduce((sum, pass) => sum + flaggedIn(pass), 0))

// What the list is narrowed to: nothing, the passes that failed, or those that flagged a note.
const focus = ref(null)
const toggle = (what) => (focus.value = focus.value === what ? null : what)
const shown = computed(() => {
  if (focus.value === 'failed') return passes.value.filter((pass) => pass.status === 'failed')
  if (focus.value === 'flagged') return passes.value.filter((pass) => flaggedIn(pass) > 0)
  return passes.value
})

const selectedId = ref(null)
const selected = computed(() => passes.value.find((pass) => pass.id === selectedId.value) ?? null)
// The chosen pass is the newest in view until one is picked, and follows the list as it narrows.
watch(shown, (list) => {
  if (!list.some((pass) => pass.id === selectedId.value)) selectedId.value = list[0]?.id ?? null
})

// What each pass did, asked for when it is chosen and kept.
const entries = ref({})
const entriesLoading = ref(false)
const entriesError = ref('')
watch(selectedId, async (id) => {
  entriesError.value = ''
  if (id == null || entries.value[id]) return
  entriesLoading.value = true
  try {
    const log = await api.adminAiLog({ passId: id })
    entries.value = { ...entries.value, [id]: Array.isArray(log) ? log : [] }
  } catch (e) {
    entriesError.value = e.message || t('aiLog.errorLong')
  } finally {
    entriesLoading.value = false
  }
})
const chosenEntries = computed(() => entries.value[selectedId.value] ?? [])
const visibleEntries = computed(() =>
  focus.value === 'flagged' ? chosenEntries.value.filter((entry) => entry.action === 'flagged') : chosenEntries.value,
)

// A pass's counts as one short line: "4 notes · 2 created · 1 updated".
function passResult(pass) {
  const stats = pass.stats ?? {}
  const parts = []
  for (const key of ['notes', 'created', 'updated', 'discarded', 'flagged']) {
    const n = count(stats[key])
    if (stats[key] != null) parts.push(t(`aiLog.stats.${key}`, { n }, n))
  }
  return parts.join(' · ')
}

// When a pass ran, in one line: its start and how long it took, or that it is still going.
function passWhen(pass) {
  const start = formatShortDate(pass.started_at)
  if (!start) return '—'
  const length = pass.finished_at ? formatDuration(pass.started_at, pass.finished_at) : t('aiLog.running')
  return length ? `${start} · ${length}` : start
}

function targetOf(entry) {
  if (entry.node_id != null) return { title: nodeTitles.value.get(entry.node_id) || t('aiLog.node', { id: entry.node_id }), to: nodeTitles.value.has(entry.node_id) ? `/node/${entry.node_id}` : '' }
  if (entry.note_id != null) return { title: t('aiLog.note', { id: entry.note_id }), to: '' }
  return { title: '—', to: '' }
}

// The note an entry came from, in a few words, with who left it.
function noteOf(entry) {
  const note = noteById.value.get(entry.note_id)
  if (!note) return ''
  const profile = Array.isArray(note.profiles) ? note.profiles[0] : note.profiles
  const who = profile?.name ? `${profile.name} · ` : ''
  return `${who}${(note.content || '').replace(/\s+/g, ' ').trim()}`
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [passList, noteList, content] = await Promise.all([api.adminPasses(), api.adminNotes(), loadNodes()])
    passes.value = Array.isArray(passList) ? passList : []
    notes.value = Array.isArray(noteList) ? noteList : []
    tree.value = Array.isArray(content) ? content : []
    selectedId.value = passes.value[0]?.id ?? null
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

      <Empty
        v-else-if="passes.length === 0"
        :title="t('aiLog.passesEmptyTitle')"
        :description="t('aiLog.passesEmpty')"
        :icon="History"
      />

      <div v-else class="not-prose flex flex-col gap-6">
        <!-- What needs a look. Nothing here when nothing does. -->
        <div v-if="failedCount || flaggedCount" class="flex flex-wrap items-center gap-2">
          <Button
            v-if="failedCount"
            variant="ghost"
            size="sm"
            :aria-pressed="focus === 'failed'"
            :class="focus === 'failed' && 'bg-bg-muted text-fg'"
            @click="toggle('failed')"
          >
            <Status state="error" :label="t('aiLog.failedPasses', { n: failedCount }, failedCount)" />
          </Button>
          <Button
            v-if="flaggedCount"
            variant="ghost"
            size="sm"
            :aria-pressed="focus === 'flagged'"
            :class="focus === 'flagged' && 'bg-bg-muted text-fg'"
            @click="toggle('flagged')"
          >
            <Status state="flagged" :label="t('aiLog.stats.flagged', { n: flaggedCount }, flaggedCount)" />
          </Button>
        </div>

        <div class="grid gap-8 md:grid-cols-[16rem_minmax(0,1fr)] md:gap-10">
          <ul class="flex flex-col gap-0.5" :aria-label="t('aiLog.passes')">
            <li v-for="pass in shown" :key="pass.id">
              <Button
                variant="ghost"
                :aria-current="pass.id === selectedId || undefined"
                :class="[
                  'h-auto w-full flex-col items-start gap-1 px-3 py-2 text-left font-normal',
                  pass.id === selectedId && 'bg-bg-muted text-fg',
                ]"
                @click="selectedId = pass.id"
              >
                <span class="flex w-full items-center justify-between gap-2">
                  <span class="text-label tabular-nums text-fg">#{{ pass.id }}</span>
                  <Status :state="PASS_STATES[pass.status] ?? 'idle'" :label="label('passStatus', pass.status)" />
                </span>
                <span class="text-meta text-fg-muted">{{ passWhen(pass) }}</span>
              </Button>
            </li>
          </ul>

          <section v-if="selected" class="flex min-w-0 flex-col gap-5" :aria-label="`#${selected.id}`">
            <header class="flex flex-col gap-1">
              <h2 class="m-0 text-title text-fg">#{{ selected.id }}</h2>
              <p v-if="passResult(selected)" class="m-0 text-label text-fg-secondary">{{ passResult(selected) }}</p>
              <p v-if="selected.model" class="m-0 text-meta text-fg-muted">{{ selected.model }}</p>
            </header>

            <Callout v-if="selected.error" type="caution" :title="label('passStatus', 'failed')">
              {{ selected.error }}
            </Callout>

            <StatusText v-if="entriesLoading" :delay="300" :text="t('aiLog.loading')" working />
            <StatusText v-else-if="entriesError" :text="entriesError" error />
            <p v-else-if="visibleEntries.length === 0 && !selected.error" class="m-0 text-label text-fg-muted">{{ t('aiLog.quiet') }}</p>

            <ul v-else class="flex flex-col divide-y divide-border">
              <li v-for="entry in visibleEntries" :key="entry.id" class="flex items-start gap-4 py-3">
                <Status
                  class="w-32 shrink-0 pt-px"
                  :state="ACTION_STATES[entry.action] ?? 'idle'"
                  :label="label('actions', entry.action)"
                />
                <div class="flex min-w-0 flex-1 flex-col gap-0.5">
                  <RouterLink v-if="targetOf(entry).to" :to="targetOf(entry).to" class="text-label text-fg hover:underline">
                    {{ targetOf(entry).title }}
                  </RouterLink>
                  <span v-else class="text-label text-fg">{{ targetOf(entry).title }}</span>
                  <TruncatedText v-if="entry.reason" class="text-meta text-fg-muted">{{ entry.reason }}</TruncatedText>
                  <TruncatedText v-if="noteOf(entry)" class="text-meta text-fg-faint">{{ noteOf(entry) }}</TruncatedText>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </PageLayout>
  </main>
</template>
