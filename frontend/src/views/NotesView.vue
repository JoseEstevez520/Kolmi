<script setup>
import { computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Empty } from 'elastic-ui'
import { NotebookPen, Plus } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import CardGridSkeleton from '../components/CardGridSkeleton.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { useCached } from '../lib/cached.js'
import { formatDay, noteStatusLabel } from '../lib/format.js'
import { setLiveCount } from '../lib/liveCount.js'
import { plainText, splitNote } from '../lib/notes.js'
import { usePolling } from '../lib/polling.js'

// Your notes: a way into writing a new one, and the ones you left. When classmates are writing
// live, their notes come first, as a row of cards. Writing live is a switch in a note's own
// header (NoteWriteView). Each opens on its own
// screen (NoteWriteView), still editable while it waits for the daily pass.
const { t } = useI18n()

// The last list draws at once and is refreshed quietly; "loading" is only for a first visit.
const { data, loading, error, refresh } = useCached('notes')
const notes = computed(() => data.value ?? [])

// Other people's live notes: from the cache at once, refreshed while this screen is open
// (paused while the tab is hidden). Your own live note is not here: its switch shows it.
const live = useCached('live')
const liveNotes = computed(() => (live.data.value?.notes ?? []).filter((n) => n.live && !n.mine))
watch(live.data, (answer) => answer && setLiveCount(answer.notes), { immediate: true })
usePolling(live.refresh, 6000)

// A note's status as the library's Status state: waiting, taken in, or left out.
const STATUS_STATES = {
  pending: 'idle',
  processed: 'done',
  discarded: 'discarded',
}

const title = computed(() => (profile.value?.name ? t('notes.greeting', { name: profile.value.name }) : t('notes.title')))

// A card shows a note's title and its words; a plain-text note is all words.
// A note of only files shows their names.
function preview(note) {
  const names = (note.files ?? []).map((file) => file.name).join(', ')
  if (note.format !== 'markdown') return { title: '', text: note.content || names }
  const parts = splitNote(note.content)
  return { title: parts.title, text: plainText(parts.body) || names }
}

onMounted(refresh)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="t('notes.lead')">
      <CardGrid v-if="liveNotes.length" class="not-prose mb-10">
        <PageCard
          v-for="note in liveNotes"
          :key="note.id"
          :to="`/live/${note.id}`"
          :title="note.title"
          :description="note.preview"
          :meta="note.author ?? ''"
          state="working"
          :status="t('live.state.live')"
        />
      </CardGrid>

      <div class="not-prose">
        <div class="flex items-center gap-2">
          <Button :icon="Plus" to="/notes/new" data-tour="new-note">{{ t('notes.new') }}</Button>
        </div>
      </div>

      <h2 id="my-notes" class="mt-10">{{ t('notes.mine') }}</h2>

      <CardGridSkeleton v-if="loading" class="mt-4" />
      <Callout v-else-if="error" type="caution" :title="t('notes.error')">
        {{ error.trim() || t('notes.errorLong') }}
      </Callout>
      <Empty
        v-else-if="notes.length === 0"
        :title="t('notes.emptyTitle')"
        :description="t('notes.empty')"
        :icon="NotebookPen"
      />
      <CardGrid v-else>
        <PageCard
          v-for="note in notes"
          :key="note.id"
          :to="`/notes/${note.id}`"
          :title="preview(note).title"
          :description="preview(note).text"
          :meta="formatDay(note.created_at)"
          :status="noteStatusLabel(note.status)"
          :state="STATUS_STATES[note.status]"
          clamp
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
