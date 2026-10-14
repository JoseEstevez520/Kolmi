<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Button, Callout, Input, StatusText } from 'elastic-ui'
import { Check, Pencil, X } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { formatAgo } from '../lib/format.js'
import { setLiveCount } from '../lib/liveCount.js'
import { usePolling } from '../lib/polling.js'

// The live notes: what is being written right now on top, the earlier sessions below, and a way
// into writing one. The list refreshes while the tab is visible.
const { t } = useI18n()
const router = useRouter()

const notes = ref([])
const currentClass = ref(null)
const loading = ref(true)
const error = ref('')

const now = computed(() => notes.value.filter((n) => n.live))
const earlier = computed(() => notes.value.filter((n) => !n.live))

async function load() {
  try {
    const answer = await api.liveNotes()
    notes.value = answer.notes
    setLiveCount(answer.notes)
    currentClass.value = answer.current_class
    error.value = ''
  } catch (e) {
    error.value = e.message || t('live.error')
  } finally {
    loading.value = false
  }
}
usePolling(load, 6000)

// A note's state as the library's Status: a ring that turns while it is written.
function stateOf(note) {
  if (note.live) return ['working', t('live.state.live')]
  if (note.ended) return ['done', t('live.state.ended')]
  if (!note.shared) return ['idle', t('live.state.private')]
  return ['idle', t('live.state.stopped')]
}

const byline = (note) => t('live.byAgo', { name: note.author ?? '?', ago: formatAgo(note.updated_at) })

// Starting asks only for the title, offered from the class the timetable says is on.
const starting = ref(false)
const title = ref('')
const startError = ref('')
const busy = ref(false)

function openStart() {
  title.value = currentClass.value?.title ?? ''
  startError.value = ''
  starting.value = true
}

async function start() {
  busy.value = true
  startError.value = ''
  try {
    const note = await api.startLiveNote({ title: title.value.trim() || null })
    router.push({ name: 'live-note', params: { id: note.id } })
  } catch (e) {
    startError.value = e.message || t('live.startError')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="py-16">
    <PageLayout :title="t('live.title')">
      <div class="not-prose">
        <form v-if="starting" class="flex flex-wrap items-center gap-2" @submit.prevent="start">
          <Input
            v-model="title"
            class="min-w-0 flex-1"
            :placeholder="currentClass?.title || t('live.startTitlePlaceholder')"
            :aria-label="t('live.startTitleLabel')"
            autofocus
          />
          <Button type="submit" variant="ghost" size="icon" :icon="Check" :disabled="busy" :aria-label="t('live.startGo')" />
          <Button variant="ghost" size="icon" :icon="X" :disabled="busy" :aria-label="t('common.cancel')" @click="starting = false" />
        </form>
        <Button v-else variant="ghost" size="icon" :icon="Pencil" :aria-label="t('live.start')" @click="openStart" />
        <Callout v-if="startError" type="caution" class="mt-4">{{ startError }}</Callout>
      </div>

      <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />
      <Callout v-else-if="error" type="caution" :title="t('live.error')">{{ error }}</Callout>
      <!-- What is being written now comes first; the state on each card says the rest. -->
      <CardGrid v-else-if="notes.length" class="mt-10">
        <PageCard
          v-for="note in [...now, ...earlier]"
          :key="note.id"
          :to="`/live/${note.id}`"
          :title="note.title"
          :description="note.preview"
          :meta="byline(note)"
          :state="stateOf(note)[0]"
          :status="stateOf(note)[1]"
          :clamp="!note.live"
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
