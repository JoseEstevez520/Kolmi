<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  Button,
  Callout,
  Empty,
  Status,
  StatusText,
  TruncatedText,
} from 'elastic-ui'
import { CircleMinus, FilePen, FilePlus, Flag, History, NotebookPen } from '@lucide/vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { flatten, loadNodes } from '../lib/content.js'
import { formatDuration, formatShortDate } from '../lib/format.js'

// The AI log, for admins: the recent passes one under another, each opening in its place to show
// what it did. Read-only: it only shows what the backend already keeps. What needs a look (a pass that
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

// The pass that is open (one at a time): the newest that has finished until another is opened.
// A pass still running has nothing to show yet.
const openId = ref('')
const firstOf = (list) => String((list.find((pass) => pass.status !== 'running') ?? list[0])?.id ?? '')
watch(shown, (list) => {
  if (openId.value && !list.some((pass) => String(pass.id) === openId.value)) openId.value = firstOf(list)
})

// What each pass did, asked for when it is opened and kept.
const entries = ref({})
const loadingId = ref('')
const failedId = ref('')
const errorText = ref('')
watch(
  openId,
  async (id) => {
    if (!id || entries.value[id]) return
    loadingId.value = id
    failedId.value = ''
    try {
      const log = await api.adminAiLog({ passId: id })
      entries.value = { ...entries.value, [id]: Array.isArray(log) ? log : [] }
    } catch (e) {
      failedId.value = id
      errorText.value = e.message || t('aiLog.errorLong')
    } finally {
      loadingId.value = ''
    }
  },
  { immediate: true },
)
const entriesOf = (pass) => {
  const list = entries.value[String(pass.id)] ?? []
  return focus.value === 'flagged' ? list.filter((entry) => entry.action === 'flagged') : list
}

// A pass's counts, each with its icon: what it read, and what it did. Only what is above zero.
const COUNTS = [
  { key: 'notes', icon: NotebookPen },
  { key: 'created', icon: FilePlus },
  { key: 'updated', icon: FilePen },
  { key: 'discarded', icon: CircleMinus },
  { key: 'flagged', icon: Flag },
]
function countsOf(pass) {
  return COUNTS.map(({ key, icon }) => {
    const n = count(pass.stats?.[key])
    return { key, icon, n, text: t(`aiLog.stats.${key}`, { n }, n) }
  }).filter((item) => item.n > 0)
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
    openId.value = firstOf(passes.value)
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

        <Accordion v-model="openId" type="single" collapsible>
          <AccordionItem v-for="pass in shown" :key="pass.id" :value="String(pass.id)">
            <AccordionTrigger>
              <span class="flex min-w-0 flex-1 flex-wrap items-center gap-x-4 gap-y-1.5 pr-2">
                <span class="text-label tabular-nums text-fg">#{{ pass.id }}</span>
                <Status :state="PASS_STATES[pass.status] ?? 'idle'" :label="label('passStatus', pass.status)" />
                <span class="text-meta font-normal text-fg-muted">
                  {{ passWhen(pass) }}<template v-if="pass.model"> · {{ pass.model }}</template>
                </span>
                <span v-if="countsOf(pass).length" class="ml-auto flex items-center gap-4">
                  <span
                    v-for="item in countsOf(pass)"
                    :key="item.key"
                    :title="item.text"
                    :class="['inline-flex items-center gap-1.5 text-label font-normal tabular-nums', item.key === 'flagged' ? 'text-warning' : 'text-fg-secondary']"
                  >
                    <component :is="item.icon" class="size-4" :stroke-width="1.5" aria-hidden="true" />
                    <span aria-hidden="true">{{ item.n }}</span>
                    <span class="sr-only">{{ item.text }}</span>
                  </span>
                </span>
              </span>
            </AccordionTrigger>
            <AccordionContent>
              <div class="flex flex-col gap-3 pb-2">
                <Callout v-if="pass.error" type="caution" :title="label('passStatus', 'failed')">
                  {{ pass.error }}
                </Callout>

                <StatusText v-if="loadingId === String(pass.id)" :delay="300" :text="t('aiLog.loading')" working />
                <StatusText v-else-if="failedId === String(pass.id)" :text="errorText" error />
                <StatusText v-else-if="pass.status === 'running'" :text="label('passStatus', 'running')" working />
                <p v-else-if="entriesOf(pass).length === 0 && !pass.error" class="m-0 text-label text-fg-muted">{{ t('aiLog.quiet') }}</p>

                <ul v-else class="m-0 flex list-none flex-col divide-y divide-border p-0">
                  <li v-for="entry in entriesOf(pass)" :key="entry.id" class="flex items-start gap-4 py-3">
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
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </PageLayout>
  </main>
</template>
