<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, Callout, Empty, StatusText } from 'elastic-ui'
import { NotebookPen, Plus } from '@lucide/vue'
import CardGrid from '../components/CardGrid.vue'
import PageCard from '../components/PageCard.vue'
import PageLayout from '../components/PageLayout.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { formatDate, noteStatusLabel } from '../lib/format.js'
import { plainText, splitNote } from '../lib/notes.js'

// Your notes: a way into writing a new one, and the ones you left. Each opens on its own
// screen (NoteWriteView), still editable while it waits for the daily pass.
const { t } = useI18n()

const notes = ref([])
const loading = ref(true)
const error = ref('')

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

async function load() {
  loading.value = true
  error.value = ''
  try {
    notes.value = await api.myNotes()
  } catch (e) {
    error.value = e.message || t('notes.errorLong')
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="py-16">
    <PageLayout :title="title" :lead="t('notes.lead')">
      <div class="not-prose">
        <Button :icon="Plus" to="/notes/new">{{ t('notes.new') }}</Button>
      </div>

      <h2 id="my-notes" class="mt-10">{{ t('notes.mine') }}</h2>

      <StatusText v-if="loading" :delay="300" :text="t('notes.loading')" working />
      <Callout v-else-if="error" type="caution" :title="t('notes.error')">
        {{ error }}
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
          :meta="formatDate(note.created_at)"
          :status="noteStatusLabel(note.status)"
          :state="STATUS_STATES[note.status]"
          clamp
        />
      </CardGrid>
    </PageLayout>
  </main>
</template>
